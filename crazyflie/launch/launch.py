import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.conditions import LaunchConfigurationEquals
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():

    server_yaml_file = LaunchConfiguration('server_yaml_file')

    # load crazyflies
    crazyflies_yaml = os.path.join(
        get_package_share_directory('crazyflie'),
        'config',
        'crazyflies.yaml')

    with open(crazyflies_yaml, 'r') as ymlfile:
        crazyflies = yaml.safe_load(ymlfile)

    # server params
    server_yaml = os.path.join(
        get_package_share_directory('crazyflie'),
        'config',
        'server.yaml')

    with open(server_yaml, 'r') as ymlfile:
        server_yaml_contents = yaml.safe_load(ymlfile)

    server_params = [crazyflies] + [server_yaml_contents["/crazyflie_server"]["ros__parameters"]]



    server_yaml_contents["/crazyflie_server"]["ros__parameters"]['robots'] = crazyflies['robots']
    server_yaml_contents["/crazyflie_server"]["ros__parameters"]['robot_types'] = crazyflies['robot_types']
    server_yaml_contents["/crazyflie_server"]["ros__parameters"]['all'] = crazyflies['all']

    #print(server_params)

    # robot description
    urdf = os.path.join(
        get_package_share_directory('crazyflie'),
        'urdf',
        'crazyflie_description.urdf')
    with open(urdf, 'r') as f:
        robot_desc = f.read()
    server_params[1]["robot_description"] = robot_desc
    server_yaml_contents["/crazyflie_server"]["ros__parameters"]["robot_description"] = robot_desc


    # construct motion_capture_configuration
    motion_capture_yaml = os.path.join(
        get_package_share_directory('crazyflie'),
        'config',
        'motion_capture.yaml')

    with open(motion_capture_yaml, 'r') as ymlfile:
        motion_capture = yaml.safe_load(ymlfile)

    motion_capture_params = motion_capture["/motion_capture_tracking"]["ros__parameters"]
    motion_capture_params["rigid_bodies"] = dict()
    for key, value in crazyflies["robots"].items():
        type = crazyflies["robot_types"][value["type"]]
        if value["enabled"] and type["motion_capture"]["enabled"]:
            motion_capture_params["rigid_bodies"][key] =  {
                    "initial_position": value["initial_position"],
                    "marker": type["motion_capture"]["marker"],
                    "dynamics": type["motion_capture"]["dynamics"],
                }

    # copy relevent settings to server params
    server_params[1]["poses_qos_deadline"] = motion_capture_params["topics"]["poses"]["qos"]["deadline"]

    server_yaml_contents["/crazyflie_server"]["ros__parameters"]["poses_qos_deadline"] = motion_capture_params["topics"]["poses"]["qos"]["deadline"]

    #print(server_yaml_contents) 
    #print as yaml
    print('hello')
    print(yaml.dump(server_yaml_contents, default_flow_style=False, sort_keys=False))
    print('hello2')

    yaml_file = yaml.dump(server_params, default_flow_style=False, sort_keys=False)
    with open('temp.yml', 'w') as outfile:
        yaml.dump(server_yaml_contents, outfile, default_flow_style=False, sort_keys=False)

    # teleop params
    teleop_params = os.path.join(
        get_package_share_directory('crazyflie'),
        'config',
        'teleop.yaml')

    return LaunchDescription([
        DeclareLaunchArgument('backend', default_value='cpp'),
        DeclareLaunchArgument('debug', default_value='False'),
        DeclareLaunchArgument('rviz', default_value='False'),
        DeclareLaunchArgument('gui', default_value='True'),
        DeclareLaunchArgument('server_yaml_file', default_value=''),
        Node(
            package='motion_capture_tracking',
            executable='motion_capture_tracking_node',
            condition=LaunchConfigurationNotEquals('backend','sim'),
            name='motion_capture_tracking',
            output='screen',
            parameters=[motion_capture_params]
        ),
        Node(
            package='crazyflie',
            executable='teleop',
            name='teleop',
            remappings=[
                ('emergency', 'all/emergency'),
                ('takeoff', 'all/takeoff'),
                ('land', 'all/land'),
                # uncomment to manually control (and update teleop.yaml)
                # ('cmd_vel_legacy', 'cf6/cmd_vel_legacy'),
                # ('cmd_full_state', 'cf6/cmd_full_state'),
                # ('notify_setpoints_stop', 'cf6/notify_setpoints_stop'),
            ],
            parameters=[teleop_params]
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node' # by default id=0
        ),
        Node(
            package='crazyflie',
            executable='crazyflie_server.py',
            condition=LaunchConfigurationEquals('backend','cflib'),
            name='crazyflie_server',
            output='screen',
            parameters=[server_yaml_file]
        ),
        Node(
            package='crazyflie',
            executable='crazyflie_server',
            condition=LaunchConfigurationEquals('backend','cpp'),
            name='crazyflie_server',
            output='screen',
            parameters=[server_yaml_file],
            prefix=PythonExpression(['"xterm -e gdb -ex run --args" if ', LaunchConfiguration('debug'), ' else ""']),
        ),
        Node(
            package='crazyflie_sim',
            executable='crazyflie_server',
            condition=LaunchConfigurationEquals('backend','sim'),
            name='crazyflie_server',
            output='screen',
            emulate_tty=True,
            parameters= [PythonExpression(["'temp.yml' if '", LaunchConfiguration('server_yaml_file'), "' == '' else '", LaunchConfiguration('server_yaml_file'), "'"])],
        ),
        Node(
            condition=LaunchConfigurationEquals('rviz', 'True'),
            package='rviz2',
            namespace='',
            executable='rviz2',
            name='rviz2',
            arguments=['-d' + os.path.join(get_package_share_directory('crazyflie'), 'config', 'config.rviz')],
            parameters=[{
                "use_sim_time": PythonExpression(["'", LaunchConfiguration('backend'), "' == 'sim'"]),
            }]
        ),
        Node(
            condition=LaunchConfigurationEquals('gui', 'True'),
            package='crazyflie',
            namespace='',
            executable='gui.py',
            name='gui',
            parameters=[{
                "use_sim_time": PythonExpression(["'", LaunchConfiguration('backend'), "' == 'sim'"]),
            }]
        ),
    ])
