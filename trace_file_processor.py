#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import csv

### Note that ms_per_bin will define the granularity ###

def ms_to_bin(timestamp, first_timestamp, ms_per_bin):
    
    return int((timestamp - first_timestamp)/ms_per_bin)

def bin_to_sec(bin_ID, ms_per_bin):
    
    return bin_ID * ms_per_bin / 1000

"""
The trace files will simply be
a list of timestamps.

"""

def get_bin_capacities(file, ms_per_bin):
    
    MSS = 1400

    trace = open(file)
    
    first_timestamp = None
    
    capacities = {}
    
    while True:
        
        line = trace.readline()
        
        if not line:
            
            break
    
        timestamp = float(line)
        bits = MSS * 8
        
        if (first_timestamp == None):
            first_timestamp = timestamp
        
        bin_ID = ms_to_bin(timestamp, first_timestamp, ms_per_bin)
        
        capacities[bin_ID] = capacities.get(bin_ID, 0) + bits
    
    return capacities


def convert_bins_into_link_rate(capacities, ms_per_bin):
    
    bins = capacities.keys()
    
    link_capacity = []
    link_capacity_times = []
    
    
    for bin_ID in range(min(bins), max(bins) + 1):
        
        #Note the division by ms_per_bin*1000 is to convert to Mbps
        link_capacity.append(capacities.get(bin_ID, 0) / (ms_per_bin*1000))
        link_capacity_times.append(bin_to_sec(bin_ID, ms_per_bin))
    
    return link_capacity, link_capacity_times


def process_trace(file, ms_per_bin=500):
    
    capacities = get_bin_capacities(file, ms_per_bin)
    
    rate, time = convert_bins_into_link_rate(capacities, ms_per_bin)
    
    return rate, time



#Store the values in a csv file

def store_to_csv(rate, time, ms_per_bin, filename, version="throughput"):
    
    granularity = rate[0]
    rate = rate[1:]
    
    byte_data = ((ms_per_bin*1000) * np.array(rate)) / 8 
    
    if (version == "throughput"):
    
        combined = np.hstack((np.array(time)[:,None], np.array(rate)[:,None]))
    
    else:
        
        #combined = np.hstack((np.array(time)[:,None], np.array(byte_data)[:,None]))
        byte_data = np.concatenate(([granularity], byte_data))
        combined = np.array(byte_data)[:,None]

    start = True

    with open(filename, "w") as file:
    
        writer = csv.writer(file)
    
        if (start):
            
            if (version == "throughput"):
                
                writer.writerows([["Time", "Rate"]])
            
            elif (version == "bytes"):
                
                pass
                #writer.writerows([["Time", "Bytes"]])
            
            else:
                
                raise Exception("ERROR: INVALID VERSION PROVIDED")
            
            start = False
        
        writer.writerows(combined)
       
    
    with open("elapsed_time.txt", "w") as file:
        
        writer = csv.writer(file)
        #Will be useful to have corresponding time as well
        writer.writerows(np.array(time)[:,None])
        
