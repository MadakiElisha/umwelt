"""
Frame conversions between PX4 and the umwelt world frame.

PX4 reports position in a local NED frame (x north, y east, z down) and
attitude as the rotation from the FRD body frame (x forward, y right,
z down) into NED. umwelt uses ENU for the world (x east, y north, z up)
and FLU for bodies (x forward, y left, z up), following ROS REP 103.

Quaternions are (w, x, y, z) throughout, matching PX4.
"""

import numpy as np

# Maps a NED vector to ENU: swap x and y, negate z. It is its own inverse.
NED_TO_ENU = np.array([[0.0, 1.0, 0.0],
                       [1.0, 0.0, 0.0],
                       [0.0, 0.0, -1.0]])

# Maps an FLU body vector to FRD (and back): negate y and z.
FLU_TO_FRD = np.diag([1.0, -1.0, -1.0])


def ned_to_enu(v):
    """Convert a vector or an (N, 3) array of vectors from NED to ENU."""
    return np.asarray(v, dtype=float) @ NED_TO_ENU.T


def frd_to_flu(v):
    """Convert a body vector or an (N, 3) array from FRD to FLU."""
    return np.asarray(v, dtype=float) @ FLU_TO_FRD.T


def quat_to_matrix(q):
    """Return the rotation matrix for a unit quaternion (w, x, y, z)."""
    w, x, y, z = np.asarray(q, dtype=float) / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def matrix_to_quat(r):
    """Return the unit quaternion (w, x, y, z) for a rotation matrix, with w >= 0."""
    r = np.asarray(r, dtype=float)
    trace = np.trace(r)
    if trace > 0:
        s = 2.0 * np.sqrt(trace + 1.0)
        q = [0.25 * s,
             (r[2, 1] - r[1, 2]) / s,
             (r[0, 2] - r[2, 0]) / s,
             (r[1, 0] - r[0, 1]) / s]
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = 2.0 * np.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2])
        q = [(r[2, 1] - r[1, 2]) / s,
             0.25 * s,
             (r[0, 1] + r[1, 0]) / s,
             (r[0, 2] + r[2, 0]) / s]
    elif r[1, 1] > r[2, 2]:
        s = 2.0 * np.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2])
        q = [(r[0, 2] - r[2, 0]) / s,
             (r[0, 1] + r[1, 0]) / s,
             0.25 * s,
             (r[1, 2] + r[2, 1]) / s]
    else:
        s = 2.0 * np.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1])
        q = [(r[1, 0] - r[0, 1]) / s,
             (r[0, 2] + r[2, 0]) / s,
             (r[1, 2] + r[2, 1]) / s,
             0.25 * s]
    q = np.array(q)
    q /= np.linalg.norm(q)
    return q if q[0] >= 0 else -q


def attitude_ned_frd_to_enu_flu(q_ned_frd):
    """
    Convert a PX4 attitude to the umwelt convention.

    Takes the quaternion rotating FRD body vectors into NED and returns the
    rotation matrix and quaternion that rotate FLU body vectors into ENU.
    """
    r_ned_frd = quat_to_matrix(q_ned_frd)
    r_enu_flu = NED_TO_ENU @ r_ned_frd @ FLU_TO_FRD
    return r_enu_flu, matrix_to_quat(r_enu_flu)


def rpy_to_matrix(roll, pitch, yaw):
    """Return the rotation matrix for roll, pitch, yaw in radians (Rz Ry Rx)."""
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return rz @ ry @ rx


# Maps a ROS optical frame vector (x right, y down, z forward) to a body-style
# camera frame (x forward, y left, z up).
OPTICAL_TO_CAMERA = np.array([[0.0, 0.0, 1.0],
                              [-1.0, 0.0, 0.0],
                              [0.0, -1.0, 0.0]])
