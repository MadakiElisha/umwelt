"""
A 2D occupancy belief built from 3D range measurements.

Each cell stores the log-odds of being occupied. A cell that has never been
observed sits at log-odds 0, which is probability 0.5, the prior. Every scan
moves cells along each ray toward free and cells at an obstacle hit toward
occupied, using a simple inverse sensor model.

Points are sorted by height:
  below obstacle_z_min   ground. The ray is free all the way to the point.
  inside the band        obstacle. Free up to the point, occupied at it.
  above obstacle_z_max   ignored. Says nothing about the ground plane.
Points beyond max_range are clipped to max_range and only clear free space.
"""

import numpy as np


class OccupancyBelief:
    """Log-odds occupancy grid on the world XY plane."""

    def __init__(self, size_m=100.0, resolution=0.5, origin_xy=None,
                 l_occ=0.85, l_free=-0.4, l_min=-4.0, l_max=4.0):
        self.resolution = float(resolution)
        self.width = int(round(size_m / resolution))
        self.height = self.width
        if origin_xy is None:
            origin_xy = (-size_m / 2.0, -size_m / 2.0)
        self.origin = np.asarray(origin_xy, dtype=float)
        self.l_occ = l_occ
        self.l_free = l_free
        self.l_min = l_min
        self.l_max = l_max
        self.logodds = np.zeros((self.height, self.width), dtype=np.float32)

    def world_to_cell(self, xy):
        """Return (ix, iy, inside) for an (N, 2) array of world points."""
        idx = np.floor((np.asarray(xy) - self.origin) / self.resolution).astype(np.int64)
        ix, iy = idx[:, 0], idx[:, 1]
        inside = (ix >= 0) & (ix < self.width) & (iy >= 0) & (iy < self.height)
        return ix, iy, inside

    def probabilities(self):
        """Return P(occupied) per cell, row-major with y as the row index."""
        return (1.0 / (1.0 + np.exp(-self.logodds))).astype(np.float32)

    def integrate(self, origin, points, max_range=10.0,
                  obstacle_z_min=0.3, obstacle_z_max=6.0):
        """Fold one scan into the belief. origin is (3,), points is (N, 3), both world."""
        origin = np.asarray(origin, dtype=float)
        points = np.asarray(points, dtype=float).reshape(-1, 3)
        points = points[np.all(np.isfinite(points), axis=1)]
        points = points[points[:, 2] <= obstacle_z_max]
        if points.size == 0:
            return

        delta = points - origin
        rng = np.linalg.norm(delta, axis=1)
        keep = rng > 1e-6
        points, delta, rng = points[keep], delta[keep], rng[keep]
        if points.size == 0:
            return

        in_range = rng <= max_range
        scale = np.minimum(1.0, max_range / rng)
        ends = origin + delta * scale[:, None]
        is_obstacle = in_range & (points[:, 2] >= obstacle_z_min)

        # Free space: sample each ray on the XY plane at half-cell spacing.
        seg = ends[:, :2] - origin[:2]
        length = np.linalg.norm(seg, axis=1)
        direction = np.divide(seg, length[:, None], out=np.zeros_like(seg),
                              where=length[:, None] > 0)
        step = self.resolution * 0.5
        n_steps = int(np.ceil(max_range / step)) + 1
        t = np.arange(n_steps) * step
        # Stop one cell short of an obstacle so the hit cell is not also cleared.
        limit = length - np.where(is_obstacle, self.resolution, 0.0)
        valid = t[None, :] <= limit[:, None]
        samples = origin[:2] + direction[:, None, :] * t[None, :, None]
        free_xy = samples[valid]

        free = self._unique_cells(free_xy)
        occupied = self._unique_cells(ends[is_obstacle, :2])
        if free.size and occupied.size:
            free = free[~np.isin(free, occupied)]

        flat = self.logodds.reshape(-1)
        flat[free] += self.l_free
        flat[occupied] += self.l_occ
        np.clip(flat, self.l_min, self.l_max, out=flat)

    def _unique_cells(self, xy):
        if len(xy) == 0:
            return np.empty(0, dtype=np.int64)
        ix, iy, inside = self.world_to_cell(xy)
        return np.unique(iy[inside] * self.width + ix[inside])
