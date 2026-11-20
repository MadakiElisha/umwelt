# sim

Gazebo worlds, PX4 configuration and launch files.

Target versions: PX4 v1.15 or newer, Gazebo Harmonic, ROS 2 Jazzy, with the Micro XRCE-DDS Agent bridging PX4 and ROS 2.

PX4 is not vendored here. Point `PX4_DIR` at your checkout if it is not in `~/PX4-Autopilot`.

## Middleware and domain

The Micro XRCE-DDS Agent bridges PX4 into DDS, so every node in this project runs on `rmw_fastrtps_cpp`. `scripts/activate.sh` sets this for the current shell only, which leaves other workspaces (for example ones on `rmw_zenoh_cpp`) untouched.

PX4's `UXRCE_DDS_DOM_ID` parameter must match `ROS_DOMAIN_ID` (42 by default here), otherwise ROS 2 nodes will not see PX4 topics. The launch files take care of this.

Tested against PX4 v1.15.0, Gazebo Harmonic (gz-sim 8.15), ROS 2 Jazzy.
