from launch import LaunchDescription
from launch.actions import ExecuteProcess
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory('my_box_bot_gazebo')
    world = os.path.join(pkg_path, 'worlds', 'box_bot_empty.world')

    return LaunchDescription([
        ExecuteProcess(
            cmd=['gz', 'sim', world],
            output='screen'
        )
    ])