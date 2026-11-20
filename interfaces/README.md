# interfaces

ROS 2 message definitions shared by every layer, in the `umwelt_interfaces` package.

## Messages

| Message | Direction | Purpose |
| --- | --- | --- |
| `Belief` | robot to brain | Pose, occupancy grid, objects and candidate plans, all with uncertainty |
| `GridBelief` | part of `Belief` | Occupancy as float probabilities, so uncertainty survives |
| `ObjectBelief` | part of `Belief` | A detected object with a class distribution and existence probability |
| `CandidatePlan` | part of `Belief` | A plan under consideration, scored by expected free energy |
| `OperatorQuery` | robot to brain | A question for the operator, with its expected information gain |
| `Intent` | glasses to brain | Gaze, head pose and speech, plus the brain's resolution of them |
| `Task` | brain to robot | A vehicle-independent goal: go to, inspect, survey, hold, return |
| `TaskStatus` | robot to brain | Progress of a task |

## Topics

Per robot, under `/umwelt/<robot_id>/`:

- `belief` (`Belief`)
- `query` (`OperatorQuery`)
- `task` (`Task`)
- `task_status` (`TaskStatus`)

Operator side:

- `/umwelt/intent` (`Intent`)

## Conventions

- All poses and points are in the shared world frame, ENU, metres (REP 103). PX4 works in NED. Conversion happens in the robot layer and never leaks into these messages.
- Probabilities are `float32` in `[0, 1]`.
- IDs are strings so they can be UUIDs or readable names during development.
- Nothing here is specific to a vehicle type. If a field only makes sense for a drone, it belongs in `robot/`.

See `docs/decisions/0002-interface-design.md` for the reasoning.
