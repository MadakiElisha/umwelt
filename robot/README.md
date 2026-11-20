# robot

ROS 2 nodes that run on or next to the vehicle, in the `umwelt_robot` package.

Low-level control always stays with the autopilot. These nodes only read state and, later, hand the autopilot high-level goals.

## belief_node

Builds and publishes the robot's `Belief`.

- Reads `/fmu/out/vehicle_odometry` from PX4 and converts it from NED and FRD to ENU and FLU.
- Reads a depth point cloud and folds each scan into a 2D log-odds occupancy grid. Unobserved cells stay at 0.5.
- Publishes `/umwelt/<robot_id>/belief` at 5 Hz, plus debug topics for RViz: `debug/occupancy` and `debug/pose`.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `robot_id` | `x500_depth_0` | Used in topic names |
| `points_topic` | `/depth_camera/points` | Depth point cloud |
| `camera_xyz` | `[0.12, 0.03, 0.242]` | Camera position in the body frame (FLU), metres |
| `camera_rpy` | `[0, 0, 0]` | Camera orientation in the body frame, radians |
| `cloud_is_optical` | `false` | Set true if the cloud uses the ROS optical convention (z forward) |
| `grid_size_m` | `100.0` | Grid side length, centred on the world origin |
| `grid_resolution` | `0.5` | Cell size in metres |
| `max_range` | `10.0` | Points beyond this only clear free space |
| `obstacle_z_min` / `obstacle_z_max` | `0.3` / `6.0` | Height band that counts as an obstacle |
| `point_stride` | `4` | Use every Nth point to save CPU |

The frame and grid logic live in `frames.py` and `occupancy.py`, with no ROS dependency, and are unit tested in `test/`.
