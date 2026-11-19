# umwelt

See what your robots believe. Task them by looking and speaking.

In biology, an *umwelt* is the world as a particular organism perceives it. A tick, a bat and a person standing in the same field each live in a different umwelt. Robots are no different. A drone running autonomy has its own picture of the world: a map, a pose estimate, a set of uncertainties and a plan it is weighing up.

This project puts that picture in front of the operator, drawn in place on the real world through XR glasses, and lets the operator answer back by looking at things and speaking. The goal is a human and a robot working from one shared model of the world instead of two separate ones joined by a joystick.

## Why

Once a robot can fly or drive itself, the operator stops being a pilot and becomes a supervisor. The hard part is no longer control. It is knowing what the robot thinks is out there, how sure it is, what it is about to do, and when it is worth stepping in.

Screens and controllers make this expensive. The operator has to look away from the world, read a 2D display and map it back onto the scene in their head. Giving a high-level instruction means translating it into waypoints. Glasses remove both costs: information is drawn where it belongs, and "survey that ridge" plus a glance is enough to say what you mean.

## How it fits together

```
 Robot           PX4 autopilot, ROS 2 autonomy, belief publisher
   |  pose, beliefs            ^  tasks
   v                           |
 Brain           shared world frame, belief server, intent to task
   |  what to draw             ^  intent (gaze, voice)
   v                           |
 Glasses         world-anchored overlay, gaze and voice input
```

- **Robot.** Flies or drives itself. Publishes its pose, its belief about the world (occupancy, detections, uncertainty) and the plans it is considering.
- **Brain.** Runs on a laptop or phone. Keeps the robot and the operator in one coordinate frame, decides what is worth showing, and turns operator intent into tasks the robot can execute.
- **Glasses.** A thin client. Draws what the brain sends and reports where the operator is looking and what they said. Until real hardware is needed, a desktop 3D viewer stands in for the glasses.

The interfaces between these layers are defined once in `interfaces/` and are meant to be the same for UAVs, UGVs and USVs.

Longer term, the brain is framed in terms of active inference: the robot holds beliefs and preferences, the operator's gaze and speech are observations about what the operator wants, and the robot asks for input only when the answer is expected to reduce its uncertainty enough to be worth the interruption. See `docs/architecture.md`.

## Repository layout

| Path | Contents |
| --- | --- |
| `interfaces/` | ROS 2 message and service definitions shared by every layer |
| `robot/` | ROS 2 nodes that run on or next to the vehicle |
| `brain/` | World frame alignment, belief server, intent handling |
| `viewer/` | Desktop viewer that stands in for the glasses |
| `glasses/` | Android XR client (later) |
| `sim/` | Gazebo worlds, PX4 configuration, launch files |
| `docker/` | Reproducible development image (later) |
| `docs/` | Architecture notes and design decisions |
| `scripts/` | Environment checks and setup |

## Getting started

Tested target: Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, PX4 v1.15 or newer.

The repo lives inside its own colcon workspace so it never shares a build with other projects:

```bash
mkdir -p ~/umwelt_ws/src
cd ~/umwelt_ws/src
git clone git@github.com:MadakiElisha/umwelt.git
cd umwelt

./scripts/check_env.sh      # reports what is installed and what is missing
./scripts/setup_env.sh      # creates ~/umwelt_ws/.venv for extra Python packages
```

Then, in each new shell:

```bash
source ~/umwelt_ws/src/umwelt/scripts/activate.sh
```

This sources ROS 2 Jazzy, activates the project virtual environment and, once something has been built, sources the workspace overlay.

## Roadmap

1. **Scaffold.** Layout, environment setup, docs. *(this PR)*
2. **Interfaces.** `Belief`, `Task` and `Intent` messages.
3. **Belief in sim.** PX4 SITL drone in Gazebo publishing pose and an occupancy belief.
4. **Viewer.** Desktop 3D view from an operator position, showing the belief in place.
5. **Intent.** Click or speak to select a point, turn it into a task, watch the drone act on it.
6. **Asking well.** The robot decides when to ask the operator, based on expected information gain.
7. **Glasses.** Move the viewer to Android XR, solve co-localization outdoors.
8. **More vehicles.** A UGV and a USV on the same interfaces.

## Status

Early. Everything runs in simulation for now.

## License

Apache 2.0. See `LICENSE`.
