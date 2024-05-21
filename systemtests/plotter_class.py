import matplotlib.pyplot as plt
import os
import sys 
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
import numpy as np
from crazyflie_py.uav_trajectory import Trajectory
from pathlib import Path


class Plotter:

    def __init__(self, sim_backend = False):
        self.params = {'experiment':'1','trajectory':'','motors':'standard motors(CF)', 'propellers':'standard propellers(CF)'}
        self.bag_times = np.empty([0])
        self.bag_x = np.empty([0])
        self.bag_y = np.empty([0])
        self.bag_z = np.empty([0])
        self.ideal_traj_x = np.empty([0])
        self.ideal_traj_y = np.empty([0])
        self.ideal_traj_z = np.empty([0])
        self.euclidian_dist = np.empty([0])
        self.deviation = [] #list of all indexes where euclidian_distance(ideal - recorded) > EPSILON
        self.test_name = None

        self.SIM = sim_backend      #indicates if we are plotting data from real life test or from a simulated test. Default is false (real life test)
        self.EPSILON = 0.15 # euclidian distance in [m] between ideal and recorded trajectory under which the drone has to stay to pass the test (NB : epsilon is doubled for multi_trajectory test)
        self.ideal_takeoff = 0.6
        self.ideal_traj_start = 5.6
        self.ALLOWED_DEV_POINTS = 0.05  #allowed percentage of datapoints whose deviation > EPSILON while still passing test (currently % for fig8 and 10% for mt)
        # self.DELAY_CONST_FIG8 = 0#1.3 #this is the delay constant which I found by adding up all the time.sleep() etc in the figure8.py file. 
        # self.DELAY_CONST_MT = 0 #5.5
        # if self.SIM :                #It allows to temporally adjust the ideal and real trajectories on the graph. Could this be implemented in a better (not hardcoded) way ?
        #     self.DELAY_CONST_FIG8 = 0#-0.45  #for an unknown reason, the delay constants with the sim_backend is different
        #     self.DELAY_CONST_MT = 0#-0.3
        self.ALTITUDE_CONST_FIG8 = 1 #this is the altitude given for the takeoff in figure8.py. I should find a better solution than a symbolic constant ?
    
    def file_guard(self, pdf_path):
        msg = None
        if os.path.exists(pdf_path):
            msg = input("file already exists, overwrite? [y/n]: ")
            if msg == "n":
                print("exiting...")
                sys.exit(0)
            elif msg == "y":
                print("overwriting...")
                os.remove(pdf_path)
            else:
                print("invalid msg...")
                self.file_guard(pdf_path)
        return
    


    def read_csv_and_set_arrays(self, ideal_csvfile, rosbag_csvfile):
        '''Method that reads the csv data of the ideal test trajectory and of the actual recorded trajectory and initializes the attribute arrays'''

        
        #get ideal trajectory data
        self.ideal_traj_csv = Trajectory()
        try:
            path_to_ideal_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)),ideal_csvfile)
            self.ideal_traj_csv.loadcsv(path_to_ideal_csv)
        except FileNotFoundError:
            print("Plotter : File not found " + path_to_ideal_csv)
            exit(1)


        #get rosbag data
        rosbag_data = np.loadtxt(rosbag_csvfile, delimiter=",")
        
        self.bag_times = np.array(rosbag_data[:,0])
        self.bag_x = np.array(rosbag_data[:,1])
        self.bag_y = np.array(rosbag_data[:,2])
        self.bag_z = np.array(rosbag_data[:,3])
    
        self.adjust_arrays()
        bag_arrays_size = len(self.bag_times)
        print("number of datapoints in self.bag_*: ",bag_arrays_size)
        
        with open(rosbag_csvfile) as f:
                lines = f.readlines()
                second_to_lastline = lines[-2] #get 2nd to last line, where tajeoff time is written as comment
                lastline = lines[-1] #get last line of csv file, where the traj start time is written as comment

        print("lastline", lastline)
        self.traj_start_time = float(lastline[lastline.find(":") + 1 :])  #get the "takeoff" time from last line of csv
        print(self.traj_start_time)
        print("2nd to lastline", second_to_lastline)
        self.takeoff_time = float(second_to_lastline[second_to_lastline.find(":") + 1 :])  #get the "takeoff" time from last line of csv
        print(self.takeoff_time)

        offset1 = (self.ideal_takeoff - self.takeoff_time) - 0.15
        offset2 = (self.ideal_traj_start - self.traj_start_time) + 0
        print(f"{offset1} {offset2} {offset1 - offset2}")


        #####calculate ideal trajectory points corresponding to the times of recorded points 

        self.ideal_traj_x = np.empty([bag_arrays_size])
        self.ideal_traj_y = np.empty([bag_arrays_size])
        self.ideal_traj_z = np.empty([bag_arrays_size])
        self.euclidian_dist = np.empty([bag_arrays_size])
        #self.offset_times = self.bag_times - offset1 

        #for testing
        self.ideal_traj_no_x = np.empty([bag_arrays_size])
        self.ideal_traj_no_y = np.empty([bag_arrays_size])
        self.ideal_traj_no_z = np.empty([bag_arrays_size])

        no_match_in_idealcsv=[]

        delay = offset1
        # if self.test_name == "fig8":
        #     delay = self.DELAY_CONST_FIG8
        # elif self.test_name == "mt":
        #     delay = self.DELAY_CONST_MT

        self.dot_list = []########testing
        
        for i in range(bag_arrays_size):  
            try:
                if(self.bag_times[i] < 0):
                    self.dot_list.append(self.bag_times[i])
                pos = self.ideal_traj_csv.eval(self.bag_times[i] + delay).pos
                pos_no = self.ideal_traj_csv.eval(self.bag_times[i]).pos
            except AssertionError: 
                no_match_in_idealcsv.append(i)
                pos = [0,0,0]  #for all recorded datapoints who cannot be matched to a corresponding ideal position we assume the drone is on its ground start position (ie those datapoints are before takeoff or after landing)
                pos_no = [0,0,0]
               
            self.ideal_traj_x[i], self.ideal_traj_y[i], self.ideal_traj_z[i]= pos[0], pos[1], pos[2]
            self.ideal_traj_no_x[i], self.ideal_traj_no_y[i], self.ideal_traj_no_z[i]= pos_no[0], pos_no[1], pos_no[2]

            self.euclidian_dist[i] = np.linalg.norm([self.ideal_traj_x[i]-self.bag_x[i], 
                                                self.ideal_traj_y[i]-self.bag_y[i], self.ideal_traj_z[i]-self.bag_z[i]])
            if self.euclidian_dist[i] > self.EPSILON:
                self.deviation.append(i)
            
        self.no_match_warning(no_match_in_idealcsv)


    def no_match_warning(self, unmatched_values:list):
        ''' A method which prints a warning saying how many (if any) recorded datapoints could not be matched to an ideal datapoint'''

        no_match_arr = np.array(unmatched_values)

        if no_match_arr.size == 0:
            return
        
        split_index_arr = []

        for i in range(no_match_arr.size - 1):                    #find indexes which are not consecutive
            if(no_match_arr[i+1] != no_match_arr[i]+1):
                split_index_arr.append(i+1)

        banana_split = np.split(no_match_arr, split_index_arr)     #split array into sub-array of consecutive indexes -> each sub-array is a timerange for which ideal positions weren't able to calculated
        print(f"{len(no_match_arr)} recorded positions weren't able to be matched with a specified ideal position and were given the default (0,0,0) ideal position instead.")
        print("Probable reason : their timestamp is before the start of the ideal trajectory or after its end.")
        if len(banana_split)==2:
            timerange1_start = self.bag_times[banana_split[0][0]]
            timerange1_end= self.bag_times[banana_split[0][1]]
            timerange2_start = self.bag_times[banana_split[1][0]]
            timerange2_end = self.bag_times[banana_split[1][1]]
            print(f"These datapoints correspond to the time ranges [{timerange1_start} , {timerange1_end}] and [{timerange2_start} , {timerange2_end}]")



    def adjust_arrays(self):
        ''' Method that trims the self.bag_* attributes to get rid of the datapoints where the drone is immobile on the ground and makes self.bag_times start at 0 [s]'''

        print(f"rosbag initial length {(self.bag_times[-1]-self.bag_times[0]) }s")

        #get rid of datapoints with timestamps that don't make sense
        self.nonsensical = []
        time = -1
        for index,t in enumerate(self.bag_times):
            if t > time:
                time = t
            else:
                self.nonsensical.append(index)

        if self.nonsensical: #if self.nonsensical is not empty
            self.unmodified_bag_times = self.bag_times
            self.unmodified_bag_x = self.bag_x
            self.unmodified_bag_y = self.bag_y
            self.unmodified_bag_z = self.bag_z
            self.bag_times = np.delete(self.bag_times, self.nonsensical)
            self.bag_x = np.delete(self.bag_x, self.nonsensical)
            self.bag_y = np.delete(self.bag_y, self.nonsensical)
            self.bag_z = np.delete(self.bag_z, self.nonsensical)
            print(f"{len(self.nonsensical)} datapoints were ignored because because their timestamp didn't make sense. They go from index {self.nonsensical[0]} to {self.nonsensical[-1]}")




        #find the takeoff time and landing times
        ground_level = self.bag_z[0]
        airborne = False
        takeoff_index = None
        landing_index = None
        i=0
        for z_coord in self.bag_z:
            if not(airborne) and z_coord > ground_level + ground_level*(0.1): #when altitude of the drone is 10% higher than the ground level, it started takeoff
                takeoff_index = i
                airborne = True
                print(f"takeoff time is {self.bag_times[takeoff_index]}s")
            if airborne and z_coord <= ground_level + ground_level*(0.1): #find when it lands again
                landing_index = i
                print(f"landing time is {self.bag_times[landing_index]}s")
                break
            i+=1



        assert (takeoff_index != None) and (landing_index != None), "Plotter : couldn't find drone takeoff or landing"


        ####get rid of datapoints before takeoff and after landing in bag_times, bag_x, bag_y, bag_y   

        assert len(self.bag_times) == len(self.bag_x) == len(self.bag_y) == len(self.bag_z), "Plotter : self.bag_* aren't the same size before trimming"
        index_arr = np.arange(len(self.bag_times))
        slicing_arr = np.delete(index_arr, index_arr[takeoff_index:landing_index+1])  #in our slicing array we take out all the indexes of when the drone is in flight so that it only contains the indexes of when the drone is on the ground

        # #delete the datapoints where drone is on the ground
        # self.bag_times = np.delete(self.bag_times, slicing_arr)
        # self.bag_x = np.delete(self.bag_x, slicing_arr)
        # self.bag_y = np.delete(self.bag_y, slicing_arr)
        # self.bag_z = np.delete(self.bag_z, slicing_arr)

        assert len(self.bag_times) == len(self.bag_x) == len(self.bag_y) == len(self.bag_z), "Plotter : self.bag_* aren't the same size after trimming"

        print(f"trimmed bag_times starts: {self.bag_times[0]}s and ends: {self.bag_times[-1]}, size: {len(self.bag_times)}")



    def create_figures(self, ideal_csvfile:str, rosbag_csvfile:str, pdfname:str, overwrite=False):
        '''Method that creates the pdf with the plots'''

        #check which test we are plotting : figure8 or multi_trajectory or another one
        if("figure8" in rosbag_csvfile):
            self.test_name = "fig8"
            self.params["trajectory"] = "figure8"
            print("Plotting fig8 test data")
        elif "multi_trajectory" in rosbag_csvfile:
            self.test_name = "mt"
            self.params["trajectory"] = "multi_trajectory"
            self.EPSILON *= 2  #multi_trajectory test has way more difficulties
            self.ALLOWED_DEV_POINTS *= 2
            print("Plotting multi_trajectory test data")
        else:
            self.test_name = "undefined"
            self.params["trajectory"] = "undefined"
            print("Plotting unspecified test data")


        self.read_csv_and_set_arrays(ideal_csvfile,rosbag_csvfile)
        offset_list = self.find_temporal_offset() 
        if len(offset_list) == 1:
            offset_string = f"temporal offset : {offset_list[0]}s \n"
        elif len(offset_list) ==2:
            offset_string = f"averaged temporal offset : {(offset_list[0]+offset_list[1])/2}s \n"
        
        test_result="failed"
        passed, percentage = self.test_passed()
        if passed:
            test_result = "passed"
        
        #create PDF to save figures
        if(pdfname[-4:] != ".pdf"):
            pdfname= pdfname + '.pdf'

        #check if user wants to overwrite the report file
        if not overwrite :
            self.file_guard(pdfname)
        pdf_pages = PdfPages(pdfname)

        #create title page
        if "figure8" in ideal_csvfile:
            name = "Figure8"
        elif "multi_trajectory" in ideal_csvfile:
            name = "Multi_trajectory"
        else:
            name = "Unnamed test"
            print("Plotter : test name not defined")

        text = f'{name} trajectory test'
        title_text_settings = f'Settings:\n'
        title_text_parameters = f'Parameters:\n'
        for key, value in self.params.items():
            title_text_parameters += f"    {key}: {value}\n"
        title_text_results = f'Results: test {test_result}\n' + offset_string + f"acceptable deviation EPSILON: {self.EPSILON}[m]\n"
        title_text_results += f"percentage of points > EPSILON : {percentage:.4f}%\n" + f'max error : '

        title_text = text + "\n" + title_text_settings + "\n" + title_text_parameters + "\n" + title_text_results
        fig = plt.figure(figsize=(5,8))
        fig.text(0.1, 0.1, title_text, size=11)
    

        pdf_pages.savefig(fig)
    
   
        #create plots
        fig, ax = plt.subplots()
        ax.plot(self.bag_times, self.ideal_traj_x, label='Ideal trajectory', linestyle="--", linewidth=1, zorder=10)
        ax.plot(self.bag_times, self.bag_x, label='Recorded trajectory')
        ax.plot(self.bag_times, self.ideal_traj_no_x, label='nonoffset Ideal trajectory', linestyle=":", linewidth=1, zorder=10, color='c')
        ax.axvline(x=self.takeoff_time, color="r")
        ax.axvline(x=self.traj_start_time, color = "g")
        ax.axvline(x=5.6, color="b", linestyle="--")
        ax.axvline(x=0.6, color="b", linestyle="--", linewidth=1)
        ax.set_xlabel('time [s]')
        ax.set_ylabel('x position [m]')  
        ax.set_title("Trajectory x")
        
        #####testing
        for i in range(len(self.dot_list)):
            ax.plot(self.dot_list[i], 0.25, 'ro')
        
        ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax.minorticks_on()
        fig.tight_layout(pad = 4)
        fig.legend()
        
        pdf_pages.savefig(fig) 
          
        fig2, ax2 = plt.subplots()
        ax2.plot(self.bag_times, self.ideal_traj_y, label='Ideal trajectory', linestyle="--", linewidth=1, zorder=10)
        ax2.plot(self.bag_times, self.bag_y, label='Recorded trajectory')
        ax2.axvline(x=self.takeoff_time, color="r")
        ax2.axvline(x=self.traj_start_time, color = "g")
        ax2.axvline(x=5.6, color="b", linestyle="--")
        ax2.axvline(x=0.6, color="b", linestyle="--", linewidth=1)
        ax2.set_xlabel('time [s]')
        ax2.set_ylabel('y position [m]')  
        ax2.set_title("trajectory y")
        ax2.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax2.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax2.minorticks_on()
        fig2.tight_layout(pad = 4) 
        fig2.legend()
        pdf_pages.savefig(fig2) 
          

        fig3, ax3 = plt.subplots()
        ax3.plot(self.bag_times, self.ideal_traj_z, label='Ideal trajectory', linestyle="--", linewidth=1, zorder=10)
        ax3.plot(self.bag_times, self.bag_z, label='Recorded trajectory')
        # ax3.axvline(x=self.takeoff_time, color="r")
        # ax3.axvline(x=self.traj_start_time, color = "g")
        # ax3.axvline(x=5.6, color="b", linestyle="--")
        # ax3.axvline(x=0.6, color="b", linestyle="--", linewidth=1)
        #####testing
        # for i in range(len(self.dot_list)):
            # ax3.plot(self.dot_list[i], 0.25, 'ro')
        ax3.set_xlabel('time [s]')
        ax3.set_ylabel('z position [m]')   
        ax3.set_title("Trajectory z")
        ax3.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax3.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax3.minorticks_on()
        fig3.tight_layout(pad = 4)
        fig3.legend()
        pdf_pages.savefig(fig3) 
 
        fig4, ax4 = plt.subplots()
        ax4.plot(self.bag_times, self.euclidian_dist)
        ax4.axvline(x=self.takeoff_time, color="r")
        ax4.axvline(x=self.traj_start_time, color = "g")
        ax4.axvline(x=5.6, color="b", linestyle="--")
        ax4.axvline(x=0.6, color="b", linestyle="--", linewidth=1)
        ax4.set_xlabel('time [s]')
        ax4.set_ylabel('Euclidean distance [m]')
        ax4.set_title('Deviation between ideal and recorded trajectories')
        fig4.tight_layout(pad=4)
        ax4.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax4.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax4.minorticks_on()
        pdf_pages.savefig(fig4)


        fig5,ax5 = plt.subplots()
        ax5.plot(self.ideal_traj_x, self.ideal_traj_y, label='Ideal trajectory', linestyle="--", linewidth=1, zorder=10)
        ax5.plot(self.bag_x, self.bag_y, label='Recorded trajectory')
        ax5.set_xlabel('x [m]')
        ax5.set_ylabel('y [m]')
        ax5.set_title('2D visualization')
        fig5.tight_layout(pad=4)
        ax5.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax5.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax5.minorticks_on()
        pdf_pages.savefig(fig5)


        fig6 = plt.figure()
        ax6 = fig6.add_subplot(projection="3d")
        ax6.plot3D(self.ideal_traj_x,self.ideal_traj_y,self.ALTITUDE_CONST_FIG8, label='Ideal trajectory', linestyle="--", linewidth=1, zorder=10)
        ax6.plot3D(self.bag_x,self.bag_y,self.bag_z, label='Recorded trajectory', linewidth=1)
        ax6.grid(True)
        ax6.set_title('3D visualization')
        ax6.set_xlabel('x [m]')
        ax6.set_ylabel('y [m]')
        ax6.set_zlabel('z [m]')
        plt.close(fig6)
        plt.tight_layout(pad=4)
        pdf_pages.savefig(fig6)


        # bag_reduced = self.bag_times[:100]
        # ideal_z_reduced = self.ideal_traj_z[:100]
        # z_reduced = self.bag_z[:100]

        # fig7, ax7 = plt.subplots()
        # ax7.plot(bag_reduced, ideal_z_reduced, label='Ideal trajectory', linestyle="--", linewidth=1, zorder=10)
        # ax7.plot(bag_reduced,z_reduced, label='Recorded trajectory', linewidth=0.1)

        # for i in range(len(bag_reduced)):
        #     # print(bag_reduced[i])
        #     a = bag_reduced[i]
        #     b=z_reduced[i]
        #     ax7.plot(bag_reduced[i], z_reduced[i], 'ro')

        # ax7.set_xlabel('time [s]')
        # ax7.set_ylabel('z position [m]')   
        # ax7.set_title("test z")
        # ax7.grid(which='major', color='#DDDDDD', linewidth=0.8)
        # ax7.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        # ax7.minorticks_on()
        # fig7.tight_layout(pad = 4)
        # fig7.legend()
        # pdf_pages.savefig(fig7) 

        #check if nonsensical timestamps were detected and deleted. If yes, plot the original t, x, y and z arrays to
        #visualize the problem
        if self.nonsensical:  
            indexes = np.arange(len(self.unmodified_bag_times))
            fig8,ax8 = plt.subplots()
            ax8.plot(indexes, self.unmodified_bag_times, label='time', linestyle="--", linewidth=1, zorder=10)
            ax8.plot(indexes, self.unmodified_bag_y, label='y', linestyle="--", linewidth=1, zorder=10)
            ax8.plot(indexes, self.unmodified_bag_z, label='z', linestyle="--", linewidth=1, zorder=10)
            ax8.set_xlabel('index')
            ax8.set_ylabel('arrays t, x, y, z')
            ax8.set_title('Visualization of unmodified t, x, y and z arrays')
            fig8.tight_layout(pad=4)
            ax8.grid(which='major', color='#DDDDDD', linewidth=0.8)
            ax8.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.8)
            ax8.minorticks_on()
            #create rectangle to highlight where the error is
            anchor = (self.nonsensical[0]-15, np.min(self.unmodified_bag_times)-0.5)
            up_boundary= self.unmodified_bag_times[self.nonsensical[-1]] + 0.1
            rect = Rectangle(anchor, width=len(self.nonsensical)+ 30, height=up_boundary, color='r', label="nonsensical", lw=0.1, fill=False)
            # rect = Rectangle((-1,-1), 1000, 3, color="r", lw=0.5, fill=False)
            ax8.add_patch(rect)
            fig8.legend()
            pdf_pages.savefig(fig8)


            fig9,ax9 = plt.subplots()
            # ax9 = plt.scatter(self.unmodified_bag_times, self.unmodified_bag_x, c="r", s=0.1)
            # ax9 = plt.scatter(self.unmodified_bag_times, self.unmodified_bag_y, c="c", s=0.1)
            # ax9 = plt.scatter(self.unmodified_bag_times, self.unmodified_bag_z, c="b", s=0.1)
            ax9 = plt.scatter(self.bag_times, self.bag_x, c="g", s=0.01, marker='.')
            ax9 = plt.scatter(self.bag_times, self.bag_y, c="c", s=0.01, marker='.')
            ax9 = plt.scatter(self.bag_times, self.bag_z, c="b", s=0.01, marker='.')

            ns_times = np.array(self.unmodified_bag_times[self.nonsensical])
            ns_x = np.array(self.unmodified_bag_x[self.nonsensical])
            ns_y = np.array(self.unmodified_bag_y[self.nonsensical])
            ns_z = np.array(self.unmodified_bag_z[self.nonsensical])
            print(f"len (ns_times) = {len(ns_times)}")
            ax9 = plt.scatter(ns_times, ns_x, c="m", s=0.1, marker='v')
            ax9 = plt.scatter(ns_times, ns_y, c="y", s=0.1, marker='<')
            ax9 = plt.scatter(ns_times, ns_z, c="r", s=0.1, marker='^')
            pdf_pages.savefig(fig9)



        pdf_pages.close()

        print("Results saved in " + pdfname)

    def test_passed(self) -> tuple :
        '''Returns a tuple containing (bool:passed, float:percentage). If the deviation between recorded and ideal trajectories of the drone didn't exceed 
        EPSILON for more than ALLOWED_DEV_POINTS % of datapoints, the boolean passed is True. Otherwise it is false. float:percentage is the percentage
        of points which whose deviation is less than EPSILON'''

        nb_dev_points = len(self.deviation)
        threshold = self.ALLOWED_DEV_POINTS * len(self.bag_times)
        percentage = (len(self.deviation) / len(self.bag_times)) * 100 

        if nb_dev_points < threshold:
            print(f"Test {self.test_name} passed : {percentage:.4f}% of datapoints had deviation larger than {self.EPSILON}m ({self.ALLOWED_DEV_POINTS * 100}% max for pass)")
            return (True, percentage)
        else:
            print(f"Test {self.test_name} failed : The deviation between ideal and recorded trajectories is greater than {self.EPSILON}m for {percentage:8.4f}% of  datapoints")
            return (False, percentage)
        
    def find_temporal_offset(self) -> list :
        ''' Returns a list containing the on-graph temporal offset between real and ideal trajectory. If offset is different for x and y axis, returns both in the same list'''
        peak_x = self.bag_x.argmax()  #find index of extremum value of real trajectory along x axis 
        peak_time_x = self.bag_times[peak_x] #find corresponding time 
        peak_x_ideal = self.ideal_traj_x.argmax() #find index of extremum value of ideal traj along x axis
        peak_time_x_ideal = self.bag_times[peak_x_ideal] #find corresponding time
        offset_x = peak_time_x_ideal - peak_time_x

        peak_y = self.bag_y.argmax()  #find index of extremum value of real trajectory along y ayis 
        peak_time_y = self.bag_times[peak_y] #find corresponding time 
        peak_y_ideal = self.ideal_traj_y.argmax() #find index of extremum value of ideal traj along y ayis
        peak_time_y_ideal = self.bag_times[peak_y_ideal] #find corresponding time
        offset_y = peak_time_y_ideal - peak_time_y

        if offset_x == offset_y:
            # print(f"On-graph temporal offset is {offset_x}s, delay const is {self.DELAY_CONST_FIG8} so uncorrected/absolute offset is {offset_x-self.DELAY_CONST_FIG8}")
            return [offset_x]
        else : 
            # print(f"On-graph temporal offsets are {offset_x} & {offset_y} secs, delay const is {self.DELAY_CONST_FIG8}")
            return [offset_x, offset_y]


if __name__=="__main__":
    
    #command line utility 

    # from argparse import ArgumentParser, Namespace
    # parser = ArgumentParser(description="Creates a pdf plotting the recorded trajectory of a drone against its desired trajectory")
    # parser.add_argument("desired_trajectory", type=str, help=".csv file containing (time,x,y,z) of the ideal/desired drone trajectory")
    # parser.add_argument("recorded_trajectory", type=str, help=".csv file containing (time,x,y,z) of the recorded drone trajectory")
    # parser.add_argument("pdf", type=str, help="name of the pdf file you want to create/overwrite")
    # parser.add_argument("--open", help="Open the pdf directly after it is created", action="store_true")
    # parser.add_argument("--overwrite", action="store_true", help="If the given pdf already exists, overwrites it without asking")
    # args : Namespace = parser.parse_args()

    # plotter = Plotter()
    # plotter.create_figures(args.desired_trajectory, args.recorded_trajectory, args.pdf, overwrite=args.overwrite)
    # if args.open:
    #     import subprocess
    #     subprocess.call(["xdg-open", args.pdf])


    paul = Plotter()
    paul.create_figures("/home/julien/ros2_ws/src/crazyswarm2/systemtests/figure8_ideal_traj.csv", "/home/julien/ros2_ws/results/test_figure8/test_figure8_0.csv", "test1.pdf", overwrite=True)
    import subprocess
    subprocess.call(["xdg-open", "test1.pdf"])


