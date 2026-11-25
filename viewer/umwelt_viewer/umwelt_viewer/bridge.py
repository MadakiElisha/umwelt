"""
Serve the umwelt viewer and stream robot beliefs to it.

Subscribes to /umwelt/<robot_id>/belief for each configured robot and serves:

  http://<host>:<port>/         the viewer page
  http://<host>:<port>/config   viewer settings as JSON
  ws://<host>:<port>/ws         live state and grid messages (see protocol.py)

ROS spins in a background thread. The web server runs on asyncio in the main
thread and pushes the latest state at state_rate and the latest grid at
grid_rate, skipping anything that has not changed. Slow clients never hold
up ROS callbacks.
"""

import asyncio
import os
import threading

from aiohttp import web, WSMsgType
from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from umwelt_interfaces.msg import Belief

from umwelt_viewer import protocol


class ViewerBridge(Node):
    """Keeps the latest Belief per robot for the web server to read."""

    def __init__(self):
        super().__init__('viewer_bridge')
        self.robot_ids = list(self.declare_parameter('robot_ids', ['x500_depth_0']).value)
        self.host = self.declare_parameter('host', '127.0.0.1').value
        self.port = int(self.declare_parameter('port', 8765).value)
        self.state_rate = float(self.declare_parameter('state_rate', 10.0).value)
        self.grid_rate = float(self.declare_parameter('grid_rate', 2.0).value)
        self.operator_position = list(
            self.declare_parameter('operator_position', [-6.0, -10.0, 1.7]).value)

        self.lock = threading.Lock()
        self.latest = {}
        self.state_seq = {}
        self.grid_seq = {}

        for robot_id in self.robot_ids:
            self.create_subscription(
                Belief, f'/umwelt/{robot_id}/belief',
                lambda msg, rid=robot_id: self.on_belief(rid, msg), 10)

    def on_belief(self, robot_id, msg):
        with self.lock:
            self.latest[robot_id] = msg
            self.state_seq[robot_id] = self.state_seq.get(robot_id, 0) + 1
            if msg.grid.width and msg.grid.height:
                self.grid_seq[robot_id] = self.grid_seq.get(robot_id, 0) + 1

    def snapshot(self):
        with self.lock:
            return dict(self.latest), dict(self.state_seq), dict(self.grid_seq)

    def config(self):
        return {
            'robots': self.robot_ids,
            'operator_position': self.operator_position,
            'state_rate': self.state_rate,
            'grid_rate': self.grid_rate,
        }


def _stamp(header):
    return header.stamp.sec + header.stamp.nanosec * 1e-9


def _state(robot_id, msg):
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    v = msg.velocity.linear
    known = protocol.known_fraction(msg.grid.p_occupied) if msg.grid.p_occupied else 0.0
    return protocol.state_message(
        robot_id, _stamp(msg.header), (p.x, p.y, p.z), (q.x, q.y, q.z, q.w),
        (v.x, v.y, v.z), msg.pose.covariance, msg.active_task_id, known)


def _grid(robot_id, msg):
    g = msg.grid
    return protocol.encode_grid(
        robot_id, _stamp(g.header), g.resolution, g.width, g.height,
        (g.origin.position.x, g.origin.position.y), g.p_occupied)


class Server:
    """aiohttp app plus the broadcast loops."""

    def __init__(self, bridge, web_dir):
        self.bridge = bridge
        self.web_dir = web_dir
        self.clients = set()
        self.sent_state = {}
        self.sent_grid = {}

    def app(self):
        app = web.Application()
        app.router.add_get('/', self.index)
        app.router.add_get('/config', self.config)
        app.router.add_get('/ws', self.websocket)
        app.router.add_static('/static/', self.web_dir)
        return app

    async def index(self, _request):
        return web.FileResponse(os.path.join(self.web_dir, 'index.html'))

    async def config(self, _request):
        return web.json_response(self.bridge.config())

    async def websocket(self, request):
        ws = web.WebSocketResponse(heartbeat=10.0)
        await ws.prepare(request)
        self.clients.add(ws)
        # A new client gets the current grid straight away.
        latest, _, _ = self.bridge.snapshot()
        for robot_id, msg in latest.items():
            await self._send(ws, _state(robot_id, msg))
            if msg.grid.width:
                await self._send(ws, _grid(robot_id, msg))
        try:
            async for m in ws:
                if m.type == WSMsgType.ERROR:
                    break
        finally:
            self.clients.discard(ws)
        return ws

    async def _send(self, ws, payload):
        try:
            if isinstance(payload, bytes):
                await ws.send_bytes(payload)
            else:
                await ws.send_str(payload)
        except (ConnectionResetError, RuntimeError):
            self.clients.discard(ws)

    async def _broadcast(self, payload):
        await asyncio.gather(*(self._send(ws, payload) for ws in list(self.clients)))

    async def state_loop(self):
        period = 1.0 / self.bridge.state_rate
        while True:
            await asyncio.sleep(period)
            if not self.clients:
                continue
            latest, state_seq, _ = self.bridge.snapshot()
            for robot_id, seq in state_seq.items():
                if self.sent_state.get(robot_id) != seq:
                    self.sent_state[robot_id] = seq
                    await self._broadcast(_state(robot_id, latest[robot_id]))

    async def grid_loop(self):
        period = 1.0 / self.bridge.grid_rate
        while True:
            await asyncio.sleep(period)
            if not self.clients:
                continue
            latest, _, grid_seq = self.bridge.snapshot()
            for robot_id, seq in grid_seq.items():
                if self.sent_grid.get(robot_id) != seq:
                    self.sent_grid[robot_id] = seq
                    await self._broadcast(_grid(robot_id, latest[robot_id]))


async def _serve(bridge):
    web_dir = os.path.join(get_package_share_directory('umwelt_viewer'), 'web')
    server = Server(bridge, web_dir)
    runner = web.AppRunner(server.app())
    await runner.setup()
    site = web.TCPSite(runner, bridge.host, bridge.port)
    await site.start()
    bridge.get_logger().info(
        f'viewer at http://{bridge.host}:{bridge.port}/ for robots {bridge.robot_ids}')
    try:
        await asyncio.gather(server.state_loop(), server.grid_loop())
    finally:
        await runner.cleanup()


def main():
    rclpy.init()
    bridge = ViewerBridge()
    spinner = threading.Thread(target=rclpy.spin, args=(bridge,), daemon=True)
    spinner.start()
    try:
        asyncio.run(_serve(bridge))
    except KeyboardInterrupt:
        pass
    finally:
        bridge.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
