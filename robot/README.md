# robot

ROS 2 nodes that run on or next to the vehicle.

- Belief publisher: pose, map with uncertainty, candidate plans.
- Task executor: turns a `Task` into a PX4 mission or offboard setpoints.

Low-level control always stays with the autopilot.
