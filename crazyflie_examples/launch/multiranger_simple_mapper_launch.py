import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    crazyflie = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('crazyflie'), 'launch'),
            '/launch.py']),
        launch_arguments={
            'backend': 'cflib',
            'gui': 'false',
            'teleop': 'false',
            'mocap': 'false',
            }.items())

    crazyflie_name = '/cf231'

    return LaunchDescription([
        crazyflie,
        Node(
            package='crazyflie',
            executable='crazyflie_server.py',
            name='crazyflie_server',
            output='screen',
            parameters=[server_params]
        ),
        Node(
            package='crazyflie',
            executable='vel_mux.py',
            name='vel_mux',
            output='screen',
            parameters=[{'hover_height': 0.3},
                        {'incoming_twist_topic': '/cmd_vel'},
                        {'robot_prefix': crazyflie_name}]
        ),
        Node(
            package='crazyflie',
            executable='simple_mapper_multiranger.py',
            name='simple_mapper_multiranger',
            output='screen',
            parameters=[
                {'robot_prefix': crazyflie_name}]
        ),
    ])
