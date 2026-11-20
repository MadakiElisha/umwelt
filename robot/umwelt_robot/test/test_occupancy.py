import numpy as np
import pytest

from umwelt_robot.occupancy import OccupancyBelief


def _cell_prob(grid, x, y):
    ix, iy, inside = grid.world_to_cell(np.array([[x, y]]))
    assert inside[0]
    return grid.probabilities()[iy[0], ix[0]]


def test_starts_at_prior():
    grid = OccupancyBelief(size_m=20.0, resolution=0.5)
    assert grid.probabilities() == pytest.approx(0.5)


def test_obstacle_hit_marks_free_then_occupied():
    grid = OccupancyBelief(size_m=20.0, resolution=0.5)
    origin = [0.0, 0.0, 2.0]
    wall = np.array([[5.0, 0.0, 2.0]])
    for _ in range(5):
        grid.integrate(origin, wall)
    assert _cell_prob(grid, 2.5, 0.0) < 0.2
    assert _cell_prob(grid, 5.0, 0.0) > 0.8
    # Behind the wall was never seen.
    assert _cell_prob(grid, 7.0, 0.0) == pytest.approx(0.5)


def test_ground_hit_is_free_not_occupied():
    grid = OccupancyBelief(size_m=20.0, resolution=0.5)
    grid.integrate([0.0, 0.0, 3.0], np.array([[4.0, 0.0, 0.0]]))
    assert _cell_prob(grid, 4.0, 0.0) < 0.5


def test_points_above_band_are_ignored():
    grid = OccupancyBelief(size_m=20.0, resolution=0.5)
    grid.integrate([0.0, 0.0, 2.0], np.array([[4.0, 0.0, 20.0]]))
    assert grid.probabilities() == pytest.approx(0.5)


def test_beyond_max_range_only_clears():
    grid = OccupancyBelief(size_m=40.0, resolution=0.5)
    grid.integrate([0.0, 0.0, 2.0], np.array([[15.0, 0.0, 2.0]]), max_range=10.0)
    assert _cell_prob(grid, 5.0, 0.0) < 0.5
    assert _cell_prob(grid, 15.0, 0.0) == pytest.approx(0.5)
    assert (grid.probabilities() <= 0.5 + 1e-6).all()


def test_log_odds_are_clamped():
    grid = OccupancyBelief(size_m=20.0, resolution=0.5, l_max=2.0)
    for _ in range(50):
        grid.integrate([0.0, 0.0, 2.0], np.array([[5.0, 0.0, 2.0]]))
    assert grid.logodds.max() == pytest.approx(2.0)


def test_nan_and_out_of_grid_points_are_safe():
    grid = OccupancyBelief(size_m=10.0, resolution=0.5)
    pts = np.array([[np.nan, 0.0, 1.0], [100.0, 100.0, 1.0], [2.0, 0.0, 1.0]])
    grid.integrate([0.0, 0.0, 1.0], pts, max_range=200.0)
    assert _cell_prob(grid, 2.0, 0.0) > 0.5
