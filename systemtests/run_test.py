#!/usr/bin/env python3   
from subprocess import Popen, PIPE
import time
import os
import signal
from mcap_handler import McapHandler
from datetime import datetime
from plotter_class import Plotter
from pathlib import Path


if __name__ == "__main__":
 
    path = Path(__file__)           #Path(__file__) should be "/home/github/actions-runner/_work/crazyswarm2/crazyswarm2/ros2_ws/src/crazyswarm2/systemtests/newsub.py" ; path.parents[0]=.../systemstests

    bagname = 'bag_' + datetime.now().strftime('%d_%m_%Y-%H_%M_%S')
    f8_bagname = "fig8_" + bagname
    mt_bagname = "multitraj_" + bagname
    src = "source " + str(path.parents[3].joinpath("install/setup.bash"))  # -> "source /home/github/actions-runner/_work/crazyswarm2/crazyswarm2/ros2_ws/install/setup.bash"
    
    #create the folder where we will record the different bags and the folder where the results pdf will be saved
    bagfolder = (path.parents[3].joinpath(f"bagfiles/{bagname}"))  # /home/github/actions-runner/_work/crazyswarm2/crazyswarm2/ros2_ws/bagfiles/bag_d_m_Y-H_M_S
    os.makedirs(bagfolder, exist_ok=True) 
    os.makedirs(path.parents[3].joinpath("results"), exist_ok=True)  # /home/github/actions-runner/_work/crazyswarm2/crazyswarm2/ros2_ws/results
    
   
 
    command = f"{src} && ros2 launch crazyflie launch.py"
    launch_crazyswarm = Popen(command, shell=True, stderr=True, 
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)   
    time.sleep(1)



    command = f"{src} && ros2 bag record -s mcap -o {f8_bagname} /tf"
    record_fig8_bag =  Popen(command, shell=True, stderr=True, cwd=bagfolder,
                            stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid) 

    

    command = f"{src} && ros2 run crazyflie_examples figure8"
    start_fig8 = Popen(command, shell=True, stderr=True, 
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)    
    

    #wait, startf8 and start_mt and the while loop are there to allow us to ^C during flightest (zB if the drone crashes) but still kill all child processes
    #they could be removed if we don't have humans overlooking the test
    wait=True
    startf8=time.time()
    while wait and time.time()<(startf8+20):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            wait = False

    os.killpg(os.getpgid(start_fig8.pid), signal.SIGTERM)  #kill figure8 flight process and all of its child processes
    os.killpg(os.getpgid(record_fig8_bag.pid), signal.SIGTERM) #kill rosbag figure8


    command = f"{src} && ros2 bag record -s mcap -o {mt_bagname} /tf"
    record_multitraj_bag = Popen(command, shell=True, stderr=True, cwd = bagfolder,
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)  

    command = f"{src} && ros2 run crazyflie_examples multi_trajectory"
    start_multitraj = Popen(command, shell=True, stderr=True, 
                       stdout=True, text=True, executable="/bin/bash", preexec_fn=os.setsid)    
    

    start_mt = time.time()
    while wait and time.time()<(start_mt+80):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            wait = False
    
    print('kill')
    os.killpg(os.getpgid(start_multitraj.pid), signal.SIGTERM)
    os.killpg(os.getpgid(record_multitraj_bag.pid), signal.SIGTERM)

    os.killpg(os.getpgid(launch_crazyswarm.pid), signal.SIGTERM)   #kill crazyswarm

    print("Flight finished")

    #test done, now we create the results pdf 

    #create a file that translates the .mcap format of the rosbag to .csv
    # NB : the filename is almost the same as the folder name but has _0 at the end
    inputbag = str(bagfolder) + '/' + f8_bagname + '/' + f8_bagname + '_0' + '.mcap'
    output_csv = str(bagfolder) + '/' + f8_bagname + '/' + f8_bagname + '_0' + '.csv'
    writer = McapHandler()
    writer.write_mcap_to_csv(inputbag, output_csv)  #translate bag from mcap to csv
    output_pdf = str(path.parents[3].joinpath("results/Results_fig8_"+ datetime.now().strftime('%d_%m_%Y-%H_%M_%S')))
    rosbag_csv = output_csv
    test_file = "../crazyflie_examples/crazyflie_examples/data/figure8.csv"
    plotter = Plotter()
    plotter.create_figures(test_file, rosbag_csv, output_pdf) #plot the data



    inputbag = str(bagfolder) + '/' + mt_bagname + '/' + mt_bagname + '_0' + '.mcap'
    output_csv = str(bagfolder) + '/' + mt_bagname + '/' + mt_bagname + '_0' + '.csv'
    writer.write_mcap_to_csv(inputbag, output_csv)
    output_pdf_2 = str(path.parents[3].joinpath("results/Results_mt_"+ datetime.now().strftime('%d_%m_%Y-%H_%M_%S')))
    rosbag_csv = output_csv
    test_file = "../crazyflie_examples/crazyflie_examples/data/multi_trajectory/traj0.csv"
    plotter.create_figures(test_file, rosbag_csv, output_pdf_2)

    exit()
