# Architecture

This document explains what umwelt is trying to do and how the parts are split. It will change as the design firms up. Decisions that are settled get their own record in `docs/decisions/`.

## The problem

As autonomy improves, the operator's job moves away from direct control and toward supervision. A supervisor needs three things:

1. **Situational awareness of the robot's mind.** What does it think is out there, how confident is it, and what is it about to do?
2. **A cheap way to state intent.** "Check that roof" should not require placing six waypoints on a map.
3. **Good timing for interventions.** The robot should interrupt when the operator's input matters, and stay quiet otherwise.

Conventional ground control stations handle these poorly because they live on a screen that is separate from the world. Every reading has to be mapped from the screen back to the scene, and every instruction has to be translated from a thought into map clicks.

## Layers

### Robot

Runs on or next to the vehicle. In simulation this is PX4 SITL in Gazebo plus ROS 2 nodes.

- Flight or drive control stays with the autopilot (PX4 or ArduPilot). umwelt never sends low-level control.
- Autonomy nodes accept `Task` messages and turn them into missions or setpoints.
- A belief publisher reports pose, an occupancy or semantic map with uncertainty, and the candidate plans the robot is considering.

### Brain

Runs on a laptop or phone near the operator. It does the work the glasses are too small to do.

- **World frame.** Keeps the robot and the operator's head in one coordinate frame. In simulation this is free. Outdoors it means combining GNSS, heading and visual alignment, and it is the hardest problem in the project.
- **Belief server.** Subscribes to robot beliefs and decides what is worth drawing, given a very small display and a limited attention budget.
- **Intent to task.** Resolves references ("that", "there") using the operator's gaze ray against the shared map, parses the spoken request, and produces a `Task` for a specific robot.

### Glasses

A thin client. It draws primitives the brain sends in world coordinates and reports head pose, gaze and speech. Keeping it thin means the core does not depend on any one headset vendor.

Until real glasses are needed, the desktop viewer in `viewer/` plays this role from a fixed operator position on the ground.

## Interfaces

All layers talk through messages defined in `interfaces/`. Three are central:

- `Belief`: what a robot currently thinks, with uncertainty.
- `Task`: a high-level goal for a robot, independent of vehicle type.
- `Intent`: what the operator indicated, before it has been turned into a task.

The same three messages must work for a quadcopter, a ground rover and a surface vessel. Vehicle-specific detail belongs in the robot layer, not in the interfaces.

## Active inference framing

The longer-term model treats the human-robot pair as two agents sharing a generative model of the world.

- The robot maintains beliefs (a posterior over world states) and preferences (a prior over outcomes it wants to see).
- The operator mostly contributes preferences and occasional corrections to beliefs.
- Operator gaze and speech are observations. They update the robot's model of what the operator wants.
- When choosing between plans, the robot scores them by expected free energy. A query to the operator is one of the available actions, and it is chosen when its epistemic value (expected reduction in uncertainty) outweighs the cost of interrupting a person.

The display follows from this. Showing the robot's posterior and its top candidate policies is what lets the operator correct it at the right moment.

## Constraints worth remembering

- Display field of view on current glasses is narrow. Draw less.
- Power and thermal limits on glasses are tight. Compute stays off the head.
- Links drop. Every layer has to degrade safely, and the autopilot's own failsafes always win.
