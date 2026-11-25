"""
Start a PX4 SITL drone in Gazebo with the umwelt belief node.

Starts, in order:
  1. Gazebo with the umwelt_field world
  2. the Micro XRCE-DDS Agent
  3. PX4 SITL in standalone mode, which spawns an x500 with a depth camera
     into the running world
  4. a ros_gz bridge for the depth point cloud
  5. the umwelt belief node
  6. the viewer bridge, serving the viewer at http://127.0.0.1:8765/

PX4's startup script copies ROS_DOMAIN_ID into its UXRCE_DDS_DOM_ID parameter,
so PX4 topics show up on the same domain as the rest of the project.

Usage:
  ros2 launch umwelt_sim sim.launch.py
  ros2 launch umwelt_sim sim.launch.py headless:=true
  ros2 launch umwelt_sim sim.launch.py px4_dir:=/path/to/PX4-Autopilot
  ros2 launch umwelt_sim sim.launch.py viewer:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, LogInfo,
                            OpaqueFunction, TimerAction)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WORLD = 'umwelt_field'
PX4_AIRFRAME = '4002'          # gz_x500_depth
PX4_MODEL = 'gz_x500_depth'
ROBOT_ID = 'x500_depth_0'      # Gazebo names the spawned model <model>_<instance>


def _path_list(*paths):
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    return os.pathsep.join([p for p in paths if p] + ([existing] if existing else []))


def _setup(context):
    px4_dir = os.path.expanduser(LaunchConfiguration('px4_dir').perform(context))
    headless = LaunchConfiguration('headless').perform(context).lower() in ('1', 'true')
    points_topic = LaunchConfiguration('points_topic').perform(context)
    spawn_pose = LaunchConfiguration('spawn_pose').perform(context)
    viewer = LaunchConfiguration('viewer').perform(context).lower() in ('1', 'true')
    domain = os.environ.get('ROS_DOMAIN_ID', '0')

    build_dir = os.path.join(px4_dir, 'build', 'px4_sitl_default')
    px4_bin = os.path.join(build_dir, 'bin', 'px4')
    if not os.path.isfile(px4_bin):
        return [LogInfo(msg=f'PX4 SITL binary not found at {px4_bin}. '
                            'Run scripts/setup_px4.sh, or pass px4_dir:=<path>.')]

    share = get_package_share_directory('umwelt_sim')
    world_file = os.path.join(share, 'worlds', f'{WORLD}.sdf')
    gz_models = os.path.join(px4_dir, 'Tools', 'simulation', 'gz', 'models')
    gz_plugins = os.path.join(px4_dir, 'build', 'px4_sitl_default', 'src', 'modules',
                              'simulation', 'gz_plugins')

    gz_env = {
        'GZ_SIM_RESOURCE_PATH': _path_list(gz_models, os.path.join(share, 'worlds')),
        'GZ_SIM_SYSTEM_PLUGIN_PATH': os.pathsep.join(
            p for p in [gz_plugins, os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')] if p),
    }

    gz_cmd = ['gz', 'sim', '-r', world_file]
    if headless:
        gz_cmd.insert(2, '-s')
    gazebo = ExecuteProcess(cmd=gz_cmd, additional_env=gz_env, output='screen')

    agent = ExecuteProcess(cmd=['MicroXRCEAgent', 'udp4', '-p', '8888'], output='screen')

    # PX4 runs from a per-instance working directory and is pointed at the
    # build's etc folder, the same way PX4's own multi-vehicle script does it.
    rootfs = os.path.join(build_dir, 'rootfs', '0')
    os.makedirs(rootfs, exist_ok=True)
    px4 = ExecuteProcess(
        cmd=[px4_bin, '-i', '0', '-d', os.path.join(build_dir, 'etc')],
        cwd=rootfs,
        additional_env={
            **gz_env,
            'PX4_GZ_STANDALONE': '1',
            'PX4_GZ_WORLD': WORLD,
            'PX4_SYS_AUTOSTART': PX4_AIRFRAME,
            'PX4_SIM_MODEL': PX4_MODEL,
            'PX4_GZ_MODEL_POSE': spawn_pose,
        },
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='depth_bridge',
        arguments=[f'{points_topic}@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked'],
        output='screen',
    )

    belief = Node(
        package='umwelt_robot',
        executable='belief_node',
        name='belief_node',
        parameters=[{'robot_id': ROBOT_ID, 'points_topic': points_topic}],
        output='screen',
    )

    actions = [
        LogInfo(msg=f'umwelt sim: world {WORLD}, PX4 at {px4_dir}, ROS_DOMAIN_ID {domain}'),
        gazebo,
        agent,
        # Give Gazebo time to load the world before PX4 tries to spawn into it.
        TimerAction(period=5.0, actions=[px4]),
        TimerAction(period=8.0, actions=[bridge, belief]),
    ]
    if viewer:
        actions.append(Node(
            package='umwelt_viewer',
            executable='viewer_bridge',
            name='viewer_bridge',
            parameters=[{'robot_ids': [ROBOT_ID]}],
            output='screen',
        ))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'px4_dir',
            default_value=os.environ.get(
                'PX4_DIR', os.path.join(os.environ.get('UMWELT_WS', '~/umwelt_ws'),
                                        'deps', 'PX4-Autopilot')),
            description='PX4-Autopilot checkout with px4_sitl_default built'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run Gazebo without the GUI'),
        DeclareLaunchArgument(
            'points_topic', default_value='/depth_camera/points',
            description='Gazebo topic of the depth point cloud'),
        DeclareLaunchArgument(
            'viewer', default_value='true',
            description='Serve the browser viewer at http://127.0.0.1:8765/'),
        DeclareLaunchArgument(
            'spawn_pose', default_value='0,0,0.2,0,0,0',
            description='Vehicle spawn pose in the world: x,y,z,roll,pitch,yaw'),
        OpaqueFunction(function=_setup),
    ])
