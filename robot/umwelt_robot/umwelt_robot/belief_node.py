"""
Publish a robot's belief from PX4 odometry and a depth point cloud.

Subscribes:
  <px4_namespace>/fmu/out/vehicle_odometry   px4_msgs/VehicleOdometry
  <points_topic>                             sensor_msgs/PointCloud2

Publishes:
  /umwelt/<robot_id>/belief                  umwelt_interfaces/Belief
  /umwelt/<robot_id>/debug/occupancy         nav_msgs/OccupancyGrid (for RViz)
  /umwelt/<robot_id>/debug/pose              geometry_msgs/PoseStamped (for RViz)

All outputs are in the world frame: ENU, origin at the PX4 local origin.
Belief.velocity.linear is in the world frame, Belief.velocity.angular is in
the body FLU frame.
"""

import math

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
import numpy as np
from px4_msgs.msg import VehicleOdometry
import rclpy
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, qos_profile_sensor_data,
                       QoSProfile, ReliabilityPolicy)
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from umwelt_interfaces.msg import Belief

from umwelt_robot import frames
from umwelt_robot.occupancy import OccupancyBelief

# Used when PX4 reports a variance as NaN, meaning it has no estimate.
UNKNOWN_VARIANCE = 1e3


def _variance(v):
    return UNKNOWN_VARIANCE if not math.isfinite(v) else float(v)


class BeliefNode(Node):
    """Turns PX4 state and depth data into an umwelt Belief."""

    def __init__(self):
        super().__init__('belief_node')

        self.robot_id = self.declare_parameter('robot_id', 'x500_depth_0').value
        self.world_frame = self.declare_parameter('world_frame', 'world').value
        px4_ns = self.declare_parameter('px4_namespace', '').value
        points_topic = self.declare_parameter('points_topic', '/depth_camera/points').value
        cam_xyz = self.declare_parameter('camera_xyz', [0.132, 0.0, 0.261]).value
        cam_rpy = self.declare_parameter('camera_rpy', [0.0, 0.0, 0.0]).value
        cloud_is_optical = self.declare_parameter('cloud_is_optical', False).value
        grid_size = self.declare_parameter('grid_size_m', 100.0).value
        grid_res = self.declare_parameter('grid_resolution', 0.5).value
        self.max_range = self.declare_parameter('max_range', 10.0).value
        self.z_min = self.declare_parameter('obstacle_z_min', 0.3).value
        self.z_max = self.declare_parameter('obstacle_z_max', 6.0).value
        self.stride = max(1, int(self.declare_parameter('point_stride', 4).value))
        rate = self.declare_parameter('publish_rate', 5.0).value

        # Camera to body (FLU) extrinsics.
        self.cam_t = np.asarray(cam_xyz, dtype=float)
        self.cam_r = frames.rpy_to_matrix(*cam_rpy)
        if cloud_is_optical:
            self.cam_r = self.cam_r @ frames.OPTICAL_TO_CAMERA

        self.grid = OccupancyBelief(size_m=grid_size, resolution=grid_res)
        self.position = None        # ENU, (3,)
        self.r_world_body = None    # FLU body to ENU, (3, 3)
        self.belief = Belief()
        self.scans = 0
        self.cloud_logged = False

        px4_qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             history=HistoryPolicy.KEEP_LAST, depth=1)
        self.create_subscription(VehicleOdometry, f'{px4_ns}/fmu/out/vehicle_odometry',
                                 self.on_odometry, px4_qos)
        self.create_subscription(PointCloud2, points_topic, self.on_points,
                                 qos_profile_sensor_data)

        base = f'/umwelt/{self.robot_id}'
        self.belief_pub = self.create_publisher(Belief, f'{base}/belief', 10)
        self.grid_pub = self.create_publisher(OccupancyGrid, f'{base}/debug/occupancy', 1)
        self.pose_pub = self.create_publisher(PoseStamped, f'{base}/debug/pose', 10)
        self.create_timer(1.0 / rate, self.publish)

        self.get_logger().info(
            f'robot {self.robot_id}: odometry from {px4_ns}/fmu/out/vehicle_odometry, '
            f'points from {points_topic}')

    def on_odometry(self, msg):
        if msg.pose_frame != VehicleOdometry.POSE_FRAME_NED:
            self.get_logger().warn('odometry pose frame is not NED, skipping',
                                   throttle_duration_sec=5.0)
            return

        position = frames.ned_to_enu(msg.position)
        r_ned_frd = frames.quat_to_matrix(msg.q)
        r_enu_flu, q_enu_flu = frames.attitude_ned_frd_to_enu_flu(msg.q)

        if msg.velocity_frame == VehicleOdometry.VELOCITY_FRAME_BODY_FRD:
            v_ned = r_ned_frd @ np.asarray(msg.velocity, dtype=float)
        else:
            v_ned = np.asarray(msg.velocity, dtype=float)
        velocity = frames.ned_to_enu(v_ned)
        angular = frames.frd_to_flu(msg.angular_velocity)

        self.position = position
        self.r_world_body = r_enu_flu

        pose = self.belief.pose
        pose.pose.position.x, pose.pose.position.y, pose.pose.position.z = map(float, position)
        o = pose.pose.orientation
        o.w, o.x, o.y, o.z = map(float, q_enu_flu)

        # NED variances become ENU by swapping x and y. Orientation variances
        # are per axis (roll, pitch, yaw) and do not change under FRD to FLU.
        pv, ov = msg.position_variance, msg.orientation_variance
        cov = [0.0] * 36
        for i, v in enumerate([pv[1], pv[0], pv[2], ov[0], ov[1], ov[2]]):
            cov[i * 7] = _variance(v)
        pose.covariance = cov

        lin, ang = self.belief.velocity.linear, self.belief.velocity.angular
        lin.x, lin.y, lin.z = map(float, velocity)
        ang.x, ang.y, ang.z = map(float, angular)

    def on_points(self, msg):
        if self.position is None:
            return
        pts = point_cloud2.read_points_numpy(msg, field_names=('x', 'y', 'z'),
                                             skip_nans=True)
        # Depth cameras report +inf where nothing is in range (sky, far away).
        # skip_nans only removes NaN, so drop non-finite points here.
        pts = pts[::self.stride].astype(float)
        pts = pts[np.isfinite(pts).all(axis=1)]
        if pts.size == 0:
            return
        if not self.cloud_logged:
            # One-off check of the cloud convention. With the camera looking
            # forward, x should carry the depth for a body-style cloud and z
            # for an optical one.
            med = np.median(np.abs(pts), axis=0)
            self.get_logger().info(
                f'first cloud: frame_id={msg.header.frame_id!r}, {len(pts)} points, '
                f'median |x| |y| |z| = {med[0]:.2f} {med[1]:.2f} {med[2]:.2f}')
            self.cloud_logged = True

        # Camera frame to body, then body to world. Uses the latest odometry,
        # which is close enough at sim rates. Interpolation can come later.
        body = pts @ self.cam_r.T + self.cam_t
        world = body @ self.r_world_body.T + self.position
        sensor_origin = self.r_world_body @ self.cam_t + self.position

        self.grid.integrate(sensor_origin, world, max_range=self.max_range,
                            obstacle_z_min=self.z_min, obstacle_z_max=self.z_max)
        self.scans += 1

    def publish(self):
        if self.position is None:
            return
        now = self.get_clock().now().to_msg()

        b = self.belief
        b.header.stamp = now
        b.header.frame_id = self.world_frame
        b.robot_id = self.robot_id

        g = b.grid
        g.header = b.header
        g.resolution = float(self.grid.resolution)
        g.width = self.grid.width
        g.height = self.grid.height
        g.origin.position.x = float(self.grid.origin[0])
        g.origin.position.y = float(self.grid.origin[1])
        g.origin.orientation.w = 1.0
        g.prior = 0.5
        probs = self.grid.probabilities()
        g.p_occupied = probs.ravel().tolist()

        self.belief_pub.publish(b)

        pose = PoseStamped()
        pose.header = b.header
        pose.pose = b.pose.pose
        self.pose_pub.publish(pose)

        if self.grid_pub.get_subscription_count() > 0:
            self.grid_pub.publish(self._debug_grid(b.header, probs))

    def _debug_grid(self, header, probs):
        msg = OccupancyGrid()
        msg.header = header
        msg.info.resolution = float(self.grid.resolution)
        msg.info.width = self.grid.width
        msg.info.height = self.grid.height
        msg.info.origin.position.x = float(self.grid.origin[0])
        msg.info.origin.position.y = float(self.grid.origin[1])
        msg.info.origin.orientation.w = 1.0
        data = np.rint(probs * 100).astype(np.int8)
        # Show untouched cells as unknown so RViz draws them grey.
        data[np.abs(self.grid.logodds) < 1e-3] = -1
        msg.data = data.ravel().tolist()
        return msg


def main():
    rclpy.init()
    node = BeliefNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
