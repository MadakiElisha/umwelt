import json

import numpy as np
import pytest

from umwelt_viewer import protocol


def test_quantise_maps_prior_to_middle():
    q = protocol.quantise([0.0, 0.5, 1.0, np.nan])
    assert list(q) == [0, 128, 255, 128]


def test_grid_roundtrip():
    p = np.linspace(0.0, 1.0, 12, dtype=np.float32)
    frame = protocol.encode_grid('x500_depth_0', 12.5, 0.5, 4, 3, (-1.0, -0.75), p)
    header, data = protocol.decode_grid(frame)
    assert header['type'] == 'grid'
    assert header['robot_id'] == 'x500_depth_0'
    assert (header['width'], header['height']) == (4, 3)
    assert header['origin'] == [-1.0, -0.75]
    assert data.dtype == np.uint8
    assert data / 255.0 == pytest.approx(p, abs=1 / 255)


def test_grid_size_mismatch_raises():
    with pytest.raises(ValueError):
        protocol.encode_grid('r', 0.0, 0.5, 4, 4, (0.0, 0.0), np.zeros(10))


def test_grid_frame_is_compact():
    frame = protocol.encode_grid('r', 0.0, 0.5, 200, 200, (0.0, 0.0), np.full(40000, 0.5))
    assert len(frame) < 40000 + 200


def test_known_fraction():
    assert protocol.known_fraction([0.5, 0.55, 0.9, 0.1]) == pytest.approx(0.5)
    assert protocol.known_fraction([]) == 0.0


def test_state_message_with_and_without_covariance():
    cov = [0.0] * 36
    cov[0], cov[7] = 0.04, 0.09
    msg = json.loads(protocol.state_message(
        'r', 1.0, (1, 2, 3), (0, 0, 0, 1), (3, 4, 0), cov, 'task-1', 0.25))
    assert msg['speed'] == pytest.approx(5.0)
    assert msg['cov_xy'] == [[0.04, 0.0], [0.0, 0.09]]
    assert msg['active_task_id'] == 'task-1'

    cov[0] = cov[7] = protocol.UNKNOWN_VARIANCE
    msg = json.loads(protocol.state_message('r', 1.0, (0, 0, 0), (0, 0, 0, 1), (0, 0, 0), cov))
    assert msg['cov_xy'] is None
