import os
from ament_index_python.packages import (get_package_prefix, get_package_share_directory)
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription)
from launch.substitutions import (PathJoinSubstitution, LaunchConfiguration)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import SetParameter, Node

import xacro

# ROS2 Launch System will look for this function definition #
def generate_launch_description():

    # Get Package Directory #
    pkg_box_bot_gazebo = get_package_share_directory('my_box_bot_gazebo')
    pkg_box_bot_description = get_package_share_directory('my_box_bot_description')
    gz_sim_pkg = get_package_share_directory("ros_gz_sim")

    # Set the Path to Robot Mesh Models for Loading in Gazebo Sim #
    # NOTE: Do this BEFORE launching Gazebo Sim #
    install_dir_path_gazebo = (get_package_prefix('my_box_bot_gazebo') + "/share")
    install_dir_path_description = (get_package_prefix('my_box_bot_description') + "/share")
    gazebo_models_path = os.path.join(pkg_box_bot_gazebo, "models")
    description_meshes_path = os.path.join(pkg_box_bot_description, "meshes")
    gazebo_resource_paths = [install_dir_path_gazebo, install_dir_path_description, gazebo_models_path, description_meshes_path]
    if "GZ_SIM_RESOURCE_PATH" in os.environ:
        for resource_path in gazebo_resource_paths:
            if resource_path not in os.environ["GZ_SIM_RESOURCE_PATH"]:
                os.environ["GZ_SIM_RESOURCE_PATH"] += (':' + resource_path)
    else:
        os.environ["GZ_SIM_RESOURCE_PATH"] = (':'.join(gazebo_resource_paths))

    # Setup to launch the simulator and Gazebo world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_pkg, 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': [
            '-r ',  # <-- start unpaused
            PathJoinSubstitution([pkg_box_bot_gazebo, 'worlds', 'box_bot_empty.world'])
        ]}.items(),
    )

    # convert XACRO file into URDF
    xacro_file = os.path.join(pkg_box_bot_description, 'urdf', 'box_bot.xacro')
    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)
    params = {'robot_description': doc.toxml()}

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_node',
        output="screen",
        parameters=[params]
    )

    # Spawn the Robot
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        name="my_robot_spawn",
        arguments=[
            "-name", "my_robot",
            "-allow_renaming", "true",
            "-topic", "robot_description",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.2",
            "-Y", "3.14",
        ],
        output="screen",
    )

    # ROS-Gazebo Bridge
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        arguments=[
            "/clock" + "@rosgraph_msgs/msg/Clock" + "[gz.msgs.Clock",
            "/cmd_vel" + "@geometry_msgs/msg/Twist" + "@gz.msgs.Twist",
            "/tf" + "@tf2_msgs/msg/TFMessage" + "[gz.msgs.Pose_V",
            "/odom" + "@nav_msgs/msg/Odometry" + "[gz.msgs.Odometry",
            "/joint_states" + "@sensor_msgs/msg/JointState" + "[gz.msgs.Model",
        ],
        remappings=[
            # there are no remappings for this robot description
        ],
        output="screen",
    )

    # Create and Return the Launch Description Object #
    return LaunchDescription(
        [
            # Sets use_sim_time for all nodes started below (doesn't work for nodes started from ignition gazebo) #
            SetParameter(name="use_sim_time", value=True),
            gz_sim,
            robot_state_publisher_node,
            gz_spawn_entity,
            gz_bridge
        ]
    )