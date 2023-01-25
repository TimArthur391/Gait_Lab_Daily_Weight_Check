#Import all required modules
import ViconNexus
import numpy as np
import sys
import tkMessageBox
import Tkinter as tk
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from csv import writer
import datetime

vicon = ViconNexus.ViconNexus()
root = tk.Tk()
root.withdraw()

#Add paths for common versions of Vicon
try:
    sys.path.append( 'C:\\Anaconda32\\Lib\\site-packages')
    sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.6\\SDK\\Python')
    sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.6\\SDK\\Win32')
    sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.3\\SDK\\Python')
    sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.3\\SDK\\Win32')
    sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.8\\SDK\\Python')
    sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.8\\SDK\\Win32')
except IndexError:
    tkMessageBox.showinfo('Error', 'System check has failed; versions of Vicon Nexus are missing from this machine')
    sys.exit(1)

#define filter functions
def butter_lowpass(cutoff, fs, order):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a
def butter_lowpass_filter(data, cutoff, fs, order):
    b, a = butter_lowpass(cutoff, fs, order)
    y = filtfilt(b, a, data)
    return y

#define csv writer function
def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'ab') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(list_of_elem)
        f_object.close()

#Initialize variables
calibrationWeight = 25 #kg
graivty = 9.81 #ms^-2
tolerance = 5 #%
lowerWeightThreshold = 0.01*(100-tolerance)*calibrationWeight*graivty
upperWeightThreshold = 0.01*(100+tolerance)*calibrationWeight*graivty
forcePlateNames = ['Force Plate 1 5559', 'Force Plate 2 5558', 'Force Plate 3 5560']
file_name = 'T:/Projects/FP_Weight_Test/FP_Weight_Test_Log.csv'
Date = (datetime.datetime.now()).strftime("%x")


#Perform system checks
try:
    SubjectName = vicon.GetSubjectNames()
    DeviceNames = vicon.GetDeviceNames()
    FrameRate = vicon.GetFrameRate()
    FrameCount = vicon.GetFrameCount()
    #Check all force plates are connected
    if not any(elem in forcePlateNames for elem in DeviceNames):
        tkMessageBox.showinfo('Error', 'System check has failed; there is an issue with communication to 1 or more force plates')
        sys.exit(1) 
except IndexError:
    tkMessageBox.showinfo('Error', 'System check has failed; there is an issue with communication to Vicon Nexus')
    sys.exit(1) 

#Acquire the mean force of each force plate
#Also collect median, min and max in case of failure
FP_means = []
FP_medians = []
FP_maxs = []
FP_mins = []
FP_stds = []
for FP in forcePlateNames:
    #Get force plate information
    forcePlateID = int(vicon.GetDeviceIDFromName(FP)) 
    deviceRate = vicon.GetDeviceDetails(forcePlateID)[2]
    SamplesPerFrame = deviceRate / FrameRate
    totalSamples = int(SamplesPerFrame) * int(FrameCount)
    
    #Initialize arrays
    outputArray = np.empty([3,totalSamples])
    forceFilteredData = np.empty([3,totalSamples])
    
    #Collect, filter and average vertical force from each force plate
    outputArray = (np.array(vicon.GetDeviceChannel(forcePlateID,1,3)))
    forceFilteredData[0] = (butter_lowpass_filter(outputArray[0], 6, int(deviceRate), 2))
    FP_means.append((np.mean(np.power(forceFilteredData[0], 2)))**0.5)
    
    FP_medians.append((np.median(np.power(forceFilteredData[0], 2)))**0.5)
    FP_maxs.append((max(np.power(forceFilteredData[0], 2)))**0.5)
    FP_mins.append((min(np.power(forceFilteredData[0], 2)))**0.5)
    FP_stds.append((np.std(np.power(forceFilteredData[0], 2)))**0.5)

#Check if any of the force plates are measuring aprox. 25kg
#Confirm with the user, then record the result
list_of_elem = []
if (FP_means[0] > lowerWeightThreshold) and (FP_means[0] < upperWeightThreshold):
    tkMessageBox.showinfo('Force Plate Checker', 'Force Plate 1: Passed')
    list_of_elem = [Date, 'Force Plate 1', str(round(FP_means[0])), str(round(FP_stds[0])), str(round(FP_mins[0])), str(round(FP_maxs[0])), str(round(FP_medians[0]))]
    append_list_as_row(file_name, list_of_elem)
elif (FP_means[1] > lowerWeightThreshold) and (FP_means[1] < upperWeightThreshold):
    tkMessageBox.showinfo('Force Plate Checker', 'Force Plate 2: Passed')
    list_of_elem = [Date, 'Force Plate 2', str(round(FP_means[1])), str(round(FP_stds[1])), str(round(FP_mins[1])), str(round(FP_maxs[1])), str(round(FP_medians[1]))]
    append_list_as_row(file_name, list_of_elem)
elif (FP_means[2] > lowerWeightThreshold) and (FP_means[2] < upperWeightThreshold):
    tkMessageBox.showinfo('Force Plate Checker', 'Force Plate 3: Passed')
    append_list_as_row(file_name, list_of_elem)
    list_of_elem = [Date, 'Force Plate 3', str(round(FP_means[2])), str(round(FP_stds[2])), str(round(FP_mins[2])), str(round(FP_maxs[2])), str(round(FP_medians[2]))]
    append_list_as_row(file_name, list_of_elem)
else:
    tkMessageBox.showinfo('Force Plate Checker', 'FAILED! \n'
    '\n Force Plate 1: mean = ' + str(round(FP_means[0])) + ', min = ' + str(round(FP_mins[0])) + ', max = ' + str(round(FP_maxs[0])) +
    '\n Force Plate 2: mean = ' + str(round(FP_means[1])) + ', min = ' + str(round(FP_mins[1])) + ', max = ' + str(round(FP_maxs[1])) +
    '\n Force Plate 3: mean = ' + str(round(FP_means[2])) + ', min = ' + str(round(FP_mins[2])) + ', max = ' + str(round(FP_maxs[2]))
    )