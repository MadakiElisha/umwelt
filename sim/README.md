# sim

Gazebo worlds and launch files, in the `umwelt_sim` package.

## Running

```bash
source ~/umwelt_ws/src/umwelt/scripts/activate.sh
ros2 launch umwelt_sim sim.launch.py              # add headless:=true to skip the Gazebo GUI
```

This starts Gazebo with the `umwelt_field` world, the Micro XRCE-DDS Agent, PX4 SITL in standalone mode (spawning an x500 with a depth camera), a bridge for the depth cloud, and the belief node.

Fly the drone with QGroundControl: take off, then send it toward the wall to the east, the shed to the north east or the poles to the south east.

## Watching the belief

In another shell:

```bash
source ~/umwelt_ws/src/umwelt/scripts/activate.sh
ros2 topic hz /umwelt/x500_depth_0/belief      # about 5 Hz once PX4 is up
rviz2
```

In RViz set the fixed frame to `world`, then add:

- **Map** on `/umwelt/x500_depth_0/debug/occupancy`
- **Pose** on `/umwelt/x500_depth_0/debug/pose`

Grey is unknown (the 0.5 prior). As the drone flies, cells along each camera ray turn free and cells at obstacles turn occupied.

## Troubleshooting

- **No PX4 topics** (`ros2 topic list | grep fmu` is empty): check that `RMW_IMPLEMENTATION` is `rmw_fastrtps_cpp` and `ROS_DOMAIN_ID` is set before launching. PX4 copies it into `UXRCE_DDS_DOM_ID` at startup.
- **No point cloud**: list Gazebo topics with `gz topic -l | grep -i depth` and pass the right one as `points_topic:=...`.
- **Map looks rotated or mirrored**: the cloud may use the optical convention. Relaunch the belief node with `cloud_is_optical:=true`.

Target versions: PX4 v1.15 or newer, Gazebo Harmonic, ROS 2 Jazzy, with the Micro XRCE-DDS Agent bridging PX4 and ROS 2.

PX4 is not vendored here. Point `PX4_DIR` at your checkout if it is not in `~/PX4-Autopilot`.

## Middleware and domain

The Micro XRCE-DDS Agent bridges PX4 into DDS, so every node in this project runs on `rmw_fastrtps_cpp`. `scripts/activate.sh` sets this for the current shell only, which leaves other workspaces (for example ones on `rmw_zenoh_cpp`) untouched.

PX4's `UXRCE_DDS_DOM_ID` parameter must match `ROS_DOMAIN_ID` (42 by default here), otherwise ROS 2 nodes will not see PX4 topics. PX4 does this itself at startup when `ROS_DOMAIN_ID` is set in its environment.

Tested against PX4 v1.15.0, Gazebo Harmonic (gz-sim 8.15), ROS 2 Jazzy.
