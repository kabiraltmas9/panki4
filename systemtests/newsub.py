#!/usr/bin/env python3   
from subprocess import Popen
import time
import os
import signal
from mcap_read_write import McapHandler
from datetime import datetime
from pathlib import Path
from plotter_class import Plotter


if __name__ == "__main__":

    command = "source install/setup.bash && ros2 launch crazyflie launch.py"
    launch_crazyswarm = Popen(command, shell=True, stderr=True, 
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)   
    time.sleep(3)
    bagname = 'bag_' + datetime.now().strftime('%d_%m_%Y-%H:%M:%S')
    command = f"mkdir bagfiles && cd bagfiles && ros2 bag record -s mcap -o {bagname} /tf"
    start_rosbag =  Popen(command, shell=True, stderr=True, 
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid) 
    command = "ros2 run crazyflie_examples figure8"
    start_test = Popen(command, shell=True, stderr=True, 
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)    
    time.sleep(30)
    os.killpg(os.getpgid(start_test.pid), signal.SIGTERM)  #kill start_test process and all of its child processes
    os.killpg(os.getpgid(start_rosbag.pid), signal.SIGTERM) #kill rosbag
    os.killpg(os.getpgid(launch_crazyswarm.pid), signal.SIGTERM)   #kill crazyswarm

    print("Flight finished")

    #test done, now we compare the ideal and real trajectories

    #create a file that translates the .mcap format of the rosbag to .csv
    writer = McapHandler()
    #path = str(Path(__file__).parent /"bags/tfbag.mcap")

    ### attention le bagname est different du bagfile par un _0 
    inputbag = "bagfiles/" + bagname + '/' + bagname + '_0' + '.mcap'
    output_csv = "bagfiles/" + bagname + '/' + bagname + '_0' + '.csv'

    writer.write_mcap_to_csv(inputbag, output_csv)

    output_pdf = "bagfiles/" + bagname + '/' + 'Results_'+ datetime.now().strftime('%d_%m_%Y-%H:%M:%S')

    rosbag_csv = output_csv

    test_file = "src/crazyswarm2/crazyflie_examples/crazyflie_examples/data/figure8.csv"
    paul = Plotter()
    paul.create_figures(test_file, rosbag_csv, output_pdf)

    exit()
