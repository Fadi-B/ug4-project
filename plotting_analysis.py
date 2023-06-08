import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

import trace_file_processor as tfp

#Load the trace data
rate, time = tfp.process_trace('traces/TMobile-LTE-driving.up')

#Adding tick time indicator for the rate - should probably add at an earlier stage
rate = np.concatenate(([500], rate))

#Delay factor is the delay in seconds for the receiver to observe data after trace experiment has begun
#This was derived experimentally from Pantheon - should double check exact value since it is an approx. right now
DELAY_FACTOR = 3.06


def plot_trace(rate, time):
    
    plt.figure(figsize=(7,5))
    plt.fill_between(time[0:58], 0, rate[1:58], facecolor='green')
    plt.show()

    
def read_data(filename):
    
    import csv
    
    data : list

    with open(filename, newline='') as csvfile:
        
        data = list(csv.reader(csvfile))
        
    return np.array([float(x[0]) for x in data])


def pre_process_data(data):
    
    for i in range(0, len(data)):

        if (math.isnan(data[i])):
            
            data[i] = 0
    
    return data


def check_data_length(data):
    
    trace_length = len(data[1:]) * data[0] #in sec
    return trace_length

def pad_data_with_starting_delay(data):
    
    TICK_TIME = data[0] / 1000
    
    #Number of pre-pends before we actually observe data
    iterations = int(DELAY_FACTOR / TICK_TIME)
    
    #Drop the tick time indicator at the start
    data = data[1:]
        
    for i in range (0, iterations):
        
        #Pre-pend with zeros as no data observed
        data = np.concatenate(([0], data))
    
    #Add the tick time indicator back
    data = np.concatenate(([TICK_TIME*1000], data))
    
    return data


#Ensure length of trace corresponds to length of data (to ensure consistent plotting)

def get_corresponding_trace_length(trace, data):
    
    tick_time = data[0] / 1000
    
    data_length = check_data_length(data) / 1000
    
    trace_index = (1/tick_time) * data_length
    
    #Ensure we add additional datapoints introduced for the delay of the data collection
    trace_index = trace_index + int(DELAY_FACTOR / tick_time)
    
    return int(trace_index)

def plot_data(data):
    
    TICK_TIME = data[0] / 1000
    
    x_coord = np.array([(TICK_TIME)*(i+1) for i in np.arange(len(data[1:]))])
    y_coord = data[1:]
    
    plt.fill_between(x_coord, 0, y_coord, facecolor='blue')
    plt.show()

"""

This takes an arbitrary number of lists of data
and plots them all on subplots to allow for
comparison

NOTE: The first argument has to be the true link capacity as otherwise
      the results will not be shifted correct in time

"""
def plot_all(*argv):
    
    TICK_TIME = argv[0][0] / 1000 #First entry in data sets is the tick time in ms
    CAPACITY_TRACE_INDEX = 0
    
    data_sets = len(argv)
    
    ROWS = data_sets
    COLUMNS = 1
    
    fig, axs = plt.subplots(ROWS, COLUMNS, figsize=(8, 8))
    
    fig.suptitle('Shows the trace and the corresponding congestion control metrics')
    
    color_list = ['pink', 'blue', 'purple', 'olive', 'cyan', 'red', 'orange', 'brown', 'gray']
    
    data = argv[CAPACITY_TRACE_INDEX]
    trace_plot_length = get_corresponding_trace_length(argv[CAPACITY_TRACE_INDEX], argv[1])
    
    titles = ["Link Capacity", "RTT Gradient", "Throughput"]
    
    for i in range(0, len(argv)):
        
        if (not (i == CAPACITY_TRACE_INDEX)):
            
            data = pad_data_with_starting_delay(argv[i])[1:] #Drop tick time indicator
            plot_length = len(data[1:]) + 1    # +1 to ensure we match the last element
            #print("NON-TRACE")
            #print(len(data))
            #print(plot_length)
        
        else:
            
            data = argv[i][1:trace_plot_length]
            plot_length = trace_plot_length - 1 # -1 to ensure we do not add additional datapoint
            
            #print("TRACE")
            #print(len(data))
            #print(plot_length)
            
        x_coord = np.array([(TICK_TIME)*(k+1) for k in np.arange(plot_length)])
        axs[i].fill_between(x_coord, 0, data, facecolor=color_list[i])
        
        #Label properly
        #axs[i].title.set_text(titles[i])
    
    