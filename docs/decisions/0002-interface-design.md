# 0002. Interface design

Status: accepted

## Context

The robot, brain and glasses layers need a shared vocabulary that works for aerial, ground and surface vehicles, and that carries uncertainty all the way to the display. The existing ROS 2 messages get part of the way. `nav_msgs/OccupancyGrid` is close but stores occupancy as int8 percentages with a single "unknown" value, which loses exactly the information we want to show.

## Decision

1. **A small custom package, `umwelt_interfaces`,** built on standard types (`geometry_msgs`, `nav_msgs/Path`) wherever they fit.
2. **Uncertainty is first class.** Grid cells are float probabilities, objects carry class distributions and existence probabilities, poses carry covariance. An unobserved cell keeps the prior, so unknown and uncertain are the same thing.
3. **Plans are part of the belief.** The robot publishes the plans it is weighing, not only the one it chose, scored by expected free energy and its pragmatic and epistemic parts. This is what lets the operator correct the robot before it commits.
4. **Questions are explicit.** `OperatorQuery` carries its expected information gain so the brain can decide which robot gets the operator's attention.
5. **Tasks are messages, not ROS 2 actions,** for now. Topics are simpler to bridge to the glasses, to record and to replay, and cancellation is a task type. `TaskStatus` covers feedback. This can be revisited if action semantics become necessary.
6. **One world frame, ENU.** Vehicle-specific frames such as PX4's NED never appear in these messages.

## Consequences

- Off-the-shelf visualisers cannot draw `GridBelief` or `CandidatePlan` directly. The viewer will need a small conversion layer.
- Messages are larger than an int8 grid. At 0.5 m resolution a 200 m square is 160,000 cells, about 640 kB as float32. Fine on a laptop, worth downsampling before it goes to the glasses.
- Planners that do not use active inference can still fill `CandidatePlan` with an ordinary cost.
