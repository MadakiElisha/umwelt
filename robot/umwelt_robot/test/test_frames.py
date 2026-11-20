import numpy as np
import pytest

from umwelt_robot import frames


def test_ned_to_enu_position():
    # 10 m north, 5 m east, 2 m up.
    enu = frames.ned_to_enu([10.0, 5.0, -2.0])
    assert enu == pytest.approx([5.0, 10.0, 2.0])


def test_ned_to_enu_batch():
    out = frames.ned_to_enu(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 1.0]]))
    assert out == pytest.approx(np.array([[0.0, 1.0, 0.0], [1.0, 0.0, -1.0]]))


def test_quaternion_roundtrip():
    rng = np.random.default_rng(0)
    for _ in range(100):
        q = rng.normal(size=4)
        q /= np.linalg.norm(q)
        q = q if q[0] >= 0 else -q
        assert frames.matrix_to_quat(frames.quat_to_matrix(q)) == pytest.approx(q, abs=1e-9)


def _yaw_ned(yaw):
    return [np.cos(yaw / 2), 0.0, 0.0, np.sin(yaw / 2)]


@pytest.mark.parametrize('yaw_ned, forward_enu', [
    (0.0, [0.0, 1.0, 0.0]),            # facing north
    (np.pi / 2, [1.0, 0.0, 0.0]),      # facing east
    (np.pi, [0.0, -1.0, 0.0]),         # facing south
])
def test_attitude_heading(yaw_ned, forward_enu):
    r, _ = frames.attitude_ned_frd_to_enu_flu(_yaw_ned(yaw_ned))
    assert r @ [1.0, 0.0, 0.0] == pytest.approx(forward_enu, abs=1e-9)
    # Body up stays world up for a level vehicle.
    assert r @ [0.0, 0.0, 1.0] == pytest.approx([0.0, 0.0, 1.0], abs=1e-9)


def test_attitude_level_north_is_ninety_degree_enu_yaw():
    _, q = frames.attitude_ned_frd_to_enu_flu([1.0, 0.0, 0.0, 0.0])
    expected = [np.cos(np.pi / 4), 0.0, 0.0, np.sin(np.pi / 4)]
    assert q == pytest.approx(expected, abs=1e-9)


def test_nose_up_pitch_survives_conversion():
    # PX4 pitch is positive nose up about the FRD y axis.
    pitch = 0.3
    q_ned = [np.cos(pitch / 2), 0.0, np.sin(pitch / 2), 0.0]
    r, _ = frames.attitude_ned_frd_to_enu_flu(q_ned)
    forward = r @ [1.0, 0.0, 0.0]
    assert forward[2] == pytest.approx(np.sin(pitch))


def test_optical_axis_is_forward():
    assert frames.OPTICAL_TO_CAMERA @ [0.0, 0.0, 1.0] == pytest.approx([1.0, 0.0, 0.0])
