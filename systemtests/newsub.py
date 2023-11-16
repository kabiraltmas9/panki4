#!/usr/bin/env python3   
from subprocess import Popen
import time
import os
import signal
from mcap_handler import McapHandler
from datetime import datetime
from plotter_class import Plotter


if __name__ == "__main__":

    bagname = 'bag_' + datetime.now().strftime('%d_%m_%Y-%H_%M_%S')
    f8_bagname = "fig8_" + bagname
    mt_bagname = "multitraj_" + bagname

    command = "source install/setup.bash && ros2 launch crazyflie launch.py"
    launch_crazyswarm = Popen(command, shell=True, stderr=True, 
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)   
    time.sleep(1)
    command = f"mkdir results && mkdir bagfiles && mkdir bagfiles/{bagname}"
    create_dirs = Popen(command, shell=True, stderr=True, 
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid) 

    command = f"ros2 bag record -s mcap -o {f8_bagname} /tf"
    record_fig8_bag =  Popen(command, shell=True, stderr=True, cwd=f"bagfiles/{bagname}",
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid) 
    
    command = "ros2 run crazyflie_examples figure8"
    start_fig8 = Popen(command, shell=True, stderr=True, 
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)    
    time.sleep(20)
    os.killpg(os.getpgid(start_fig8.pid), signal.SIGTERM)  #kill figure8 flight process and all of its child processes
    os.killpg(os.getpgid(record_fig8_bag.pid), signal.SIGTERM) #kill rosbag figure8

    command = f"ros2 bag record -s mcap -o {mt_bagname} /tf"
    record_multitraj_bag = Popen(command, shell=True, stderr=True, 
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)    
    
    command = "ros2 run crazyflie_examples multi_trajectory"
    start_multitraj = Popen(command, shell=True, stderr=True, 
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)    
    time.sleep(80)
    os.killpg(os.getpgid(start_multitraj.pid), signal.SIGTERM)
    os.killpg(os.getpgid(record_multitraj_bag), signal.SIGTERM)

    os.killpg(os.getpgid(launch_crazyswarm.pid), signal.SIGTERM)   #kill crazyswarm

    print("Flight finished")

    #test done, now we compare the ideal and real trajectories

    #create a file that translates the .mcap format of the rosbag to .csv
    # NB : the filename is almost the same as the folder name but has _0 at the end
    writer = McapHandler()

    inputbag = "bagfiles/" + bagname + '/' + f8_bagname + '/' + f8_bagname + '_0' + '.mcap'
    output_csv = "bagfiles/" + bagname + '/' + f8_bagname + '/' + f8_bagname + '_0' + '.csv'
    writer.write_mcap_to_csv(inputbag, output_csv)
    output_pdf = "results/Results_fig8_"+ datetime.now().strftime('%d_%m_%Y-%H_%M_%S')
    rosbag_csv = output_csv

    test_file = "../crazyflie_examples/crazyflie_examples/data/figure8.csv"
    plotter = Plotter()
    plotter.create_figures(test_file, rosbag_csv, output_pdf)


    inputbag = "bagfiles/" + bagname + '/' + mt_bagname + '/' + mt_bagname + '_0' + '.mcap'
    output_csv = "bagfiles/" + bagname + '/' + mt_bagname + '/' + mt_bagname + '_0' + '.csv'
    writer.write_mcap_to_csv(inputbag, output_csv)
    output_pdf_2 = "results/Results_mt_"+ datetime.now().strftime('%d_%m_%Y-%H_%M_%S')
    rosbag_csv = output_csv
    test_file = "../crazyflie_examples/crazyflie_examples/data/multi_trajectory/traj0.csv"
    plotter.create_figures(test_file, rosbag_csv, output_pdf_2)

    exit()
