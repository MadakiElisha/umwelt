"""
Wire format between the viewer bridge and the browser.

Two kinds of message go over the websocket:

  state  JSON text. Pose, velocity, position uncertainty and a few counters
         for one robot. Small, sent often.

  grid   Binary. A 4-byte little-endian header length, a UTF-8 JSON header,
         then width * height bytes of P(occupied) quantised to 0..255,
         row-major with y as the row. Sent less often.

Keeping the grid binary and quantised makes a 200 x 200 grid 40 kB instead
of roughly 640 kB of float JSON, which matters once this runs over Wi-Fi to
a headset.

All positions are in the shared world frame (ENU, metres).
"""

import json
import math
import struct

import numpy as np

# PoseWithCovariance uses 1e3 here to mean "no estimate". See belief_node.
UNKNOWN_VARIANCE = 1e3


def quantise(p):
    """Map probabilities in [0, 1] to uint8, 0.5 to 128."""
    p = np.nan_to_num(np.asarray(p, dtype=np.float32), nan=0.5)
    return np.clip(np.rint(p * 255.0), 0, 255).astype(np.uint8)


def encode_grid(robot_id, stamp, resolution, width, height, origin_xy, p_occupied):
    """Pack one occupancy grid as a binary websocket frame."""
    data = quantise(p_occupied)
    if data.size != width * height:
        raise ValueError(f'grid has {data.size} cells, expected {width} x {height}')
    header = json.dumps({
        'type': 'grid',
        'robot_id': robot_id,
        'stamp': stamp,
        'resolution': resolution,
        'width': width,
        'height': height,
        'origin': [origin_xy[0], origin_xy[1]],
    }, separators=(',', ':')).encode('utf-8')
    return struct.pack('<I', len(header)) + header + data.tobytes()


def decode_grid(frame):
    """Unpack a frame made by encode_grid. Used by tests and tools."""
    (n,) = struct.unpack_from('<I', frame, 0)
    header = json.loads(frame[4:4 + n].decode('utf-8'))
    data = np.frombuffer(frame, dtype=np.uint8, offset=4 + n)
    return header, data


def known_fraction(p_occupied, threshold=0.1):
    """Share of cells whose probability has moved at least threshold away from 0.5."""
    p = np.asarray(p_occupied, dtype=np.float32)
    if p.size == 0:
        return 0.0
    return float(np.mean(np.abs(p - 0.5) >= threshold))


def state_message(robot_id, stamp, position, orientation_xyzw, velocity,
                  covariance, active_task_id='', known=0.0):
    """Build the JSON state message for one robot."""
    cov = list(covariance)
    sx2, sy2 = cov[0], cov[7]
    sxy = cov[1]
    has_cov = sx2 < UNKNOWN_VARIANCE and sy2 < UNKNOWN_VARIANCE
    return json.dumps({
        'type': 'state',
        'robot_id': robot_id,
        'stamp': stamp,
        'position': [float(v) for v in position],
        'orientation': [float(v) for v in orientation_xyzw],
        'velocity': [float(v) for v in velocity],
        'speed': math.sqrt(sum(float(v) ** 2 for v in velocity)),
        # 2x2 horizontal position covariance, or null when PX4 has no estimate.
        'cov_xy': [[sx2, sxy], [sxy, sy2]] if has_cov else None,
        'active_task_id': active_task_id,
        'known_fraction': known,
    }, separators=(',', ':'))
