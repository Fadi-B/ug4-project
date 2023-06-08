
#imports

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import math

import trace_file_processor as tfp
import plotting_analysis as pt

#for the customized linear least squares
from support import *

#for customized probabilistic linear least squares
from probabilistic_regression_support import *


### IMPORTANT CONSTANTS ###

DELAY_FACTOR = 3.07
TICK_TIME = 60

#To index each trial dataset
TRIAL_1 = 0
TRIAL_2 = 1
TRIAL_3 = 2
TRIAL_4 = 3
TRIAL_5 = 4

TRIALS = 1

#To index labels and proccessed datasets
LABELS = 0
PROCESSED_DATASETS = 1
AVERAGE = TRIALS #Since processed dataset array will have labels + trials = 1 + TRIALS size

#To index features in datasets
RTT_GRAD_INDEX = 0
THROUGHPUT_INDEX = 1
QUEUEING_DELAY_INDEX = 2
INTER_ARRIVAL_INDEX = 3


#If we want to normalize
NORMALIZE=False

path = 'TRAIN-DATA/'
directories = ['ATT-LTE', 'TMobile-LTE', 'Verizon-LTE', 'TMobile-UMTS', 'Verizon-EVDO']

def get_minimum_length_of_data(data):
    
    N = len(data)

    minimum_length = len(data[0][0])
    
    #indicates which trial in first entry and which feature in second entry
    where = (0,0)
    
    #Defining constants for readibility
    WHICH_TRIAL = 0
    WHICH_FEATURE = 1
    
    #Find trial of minimum length for processing
    for i in range(0, N):
        
        rtt_grad_data, throughput, queue_delay, inter_arrival = data[i]
        
        if (len(rtt_grad_data[1:]) < minimum_length):
            
            minimum_length = len(rtt_grad_data[1:])
            where = (i,0)
        
        if (len(throughput[1:]) < minimum_length):
            
            minimum_length = len(throughput[1:])
            where = (i,1)
        
        if (len(queue_delay[1:]) < minimum_length):
            
            minimum_length = len(queue_delay[1:])
            where = (i,2)
        
        if (len(inter_arrival[1:]) < minimum_length):
            
            minimum_length = len(inter_arrival[1:])
            where = (i,3)
    
    return data[where[WHICH_TRIAL]][where[WHICH_FEATURE]], minimum_length



#Processing the input datasets

def process_input_datasets(data, minimum_length):
        
    N = len(data)
    
    datasets = []
    
    average = []
    
    for i in range(0, N):
    
        rtt_grad_data, throughput, queue_delay, inter_arrival = data[i]
    
        #Drop tick indicator
        rtt_grad_data = rtt_grad_data[1:]
        throughput = throughput[1:]
        queue_delay = queue_delay[1:]
        inter_arrival = inter_arrival[1:]
        
        
        
        while (len(throughput) > minimum_length):
             throughput = throughput[:len(throughput) - 1]#Ensure they match
        
        while (len(rtt_grad_data) > minimum_length):
             rtt_grad_data = rtt_grad_data[:len(rtt_grad_data) - 1]#Ensure they match
        
        while (len(queue_delay) > minimum_length):
             queue_delay = queue_delay[:len(queue_delay) - 1]#Ensure they match
        
        while (len(inter_arrival) > minimum_length):
             inter_arrival = inter_arrival[:len(inter_arrival) - 1]#Ensure they match
                
        
        #Each row holds a single vector state at consecutive times 
        #X = np.hstack((rtt_grad_data[:,None], throughput[:,None], queue_delay[:,None], inter_arrival[:,None]))
        
        #We want to standardize the features for fair comparison of importance later on
        X_pre = np.hstack((rtt_grad_data[:,None], queue_delay[:,None], inter_arrival[:,None]))
        
        u = np.mean(X_pre, axis=0)
        sigma = np.std(X_pre, axis=0)
        
        if NORMALIZE:
            
            X_pre = (X_pre - u)/sigma
        
        X = np.hstack((throughput[:,None], X_pre))
        
        # For computing average later on
        if len(average) > 0:
            
            average = np.vstack((average, [X]))
        else:
            average = np.array([X])
        
        #print(np.std(X[:,2]))
        
        datasets.append(X)
    
    average = np.mean(average, axis=0)
    
    #Average of all trials will be at the end of the dataset list
    datasets.append(average)
    
    return datasets


def process_target_trace(trace_name, DELAY_FACTOR, tick_time, sample_dataset):
    
    #Holds actual link capacity at a particular time
    y, _ = tfp.process_trace(trace_name, ms_per_bin=tick_time)

    #To ensure we have the 
    START_INDEX = int(math.floor(DELAY_FACTOR/(tick_time / 1000)))
    END_INDEX = pt.get_corresponding_trace_length(y, np.concatenate(([tick_time], sample_dataset)))
    
    #print("start: {} \n".format(START_INDEX))
    #print("end: {} \n".format(END_INDEX))

    y = y[START_INDEX:END_INDEX + 1] #Ensure we include the last element as we want to 'forecast' (end at time k + 1, whereas
                                     #the input data sets end at time k)

    #Dropping the first element of y means that it will start at time t + 1, whereas the input datasets start at
    #time t. This will allow us to consider what to expect for time t + 1, given the curren time t. We will
    #start by learning the transformation based on this

    y = y[1:]

    return np.array(y)


#Doing analysis

def find_transformations(datasetss, y):
    
    N = len(datasetss)
    
    models = []
    
    for i in range(0, N):
    
        #Arbitrary regularization
        alpha = 120
    
        X = datasetss[i]

        w, b = fit_linreg_gradopt(X, y, alpha)
        
        models.append((w,b))
    
    return models


""" 

Will return a dictionary that contains all pairs of datasets for each trace.
The dictionary is indexed using the trace name and it holds an array for each
trace containing [(rtt_grad_data_run_1, throughput_data_run_1), ...]. Each tuple
represents a pair of data that can be processed into a dataset for training.

"""

def get_all_trial_datasets():
    
    N = TRIALS
    data = {}

    for direct in directories:
    
        dataset = []
    
        for i in range(1, N + 1):
        
            #read in all the features that are relevant
            inter_arrival = pt.read_data(path + direct + '/inter_arrival_data_run_{}.csv'.format(i))
            queue_delay = pt.read_data(path + direct + '/queue_delay_data_run_{}.csv'.format(i))
            rtt_grad_data = pt.read_data(path + direct + '/rtt_grad_data_run_{}.csv'.format(i))
            throughput = pt.read_data(path + direct + '/throughput_data_run_{}.csv'.format(i))
        
            #pre-processing to ensure no nan values present - treated as 0
            rtt_grad_data = pt.pre_process_data(rtt_grad_data)
            throughput = pt.pre_process_data(throughput)
            
            #NOTE: First value for these datasets is always nan. Might be a bug during collection.
            #      We will treat it as zero here, but we might want to remove the datapoint altogether
            #
            #      Was a bug in the data collection framework that was fixed
            inter_arrival = pt.pre_process_data(inter_arrival)
            queue_delay = pt.pre_process_data(queue_delay)
        
            dataset.append((rtt_grad_data, throughput, queue_delay, inter_arrival))
    

        data[direct] = dataset
    
    return data

""" 

Will return a dictionary that contains the proccessed datasets for all
trials for each trace. The trace name is used to access the dictionary
to get a tuple (y, processed_datasets).

The entry y in the tuple is the true link capacity, whereas the processed_datasets
is an array containing the X train data for each trial (starts at trial 1)

"""
def get_all_trial_processed_datasets(data):
    
    processed_train_data = {}
    
    for direct in data:
    
        dataset = data[direct]
    
        #IMPORTANT: THIS IS THE ISSUE. WE CANNOT HAVE TRIALS OF DIFFERENT LENGTHS (USING DIFF TICK TIMES)
        #           This is because otherwise this min function will give us the minimum one irrespective of tick time used
        min_trace, min_data_length = get_minimum_length_of_data(dataset)
    
        processed_datasets = process_input_datasets(dataset, min_data_length)

        y = process_target_trace('traces/' + direct + '-driving.up', DELAY_FACTOR, TICK_TIME, min_trace[1:])
    
        #Ensure nothing has gone wrong during the processing
        
        #print(len(y))
        #print(len(processed_datasets[0]))
        
        assert(len(y) == len(processed_datasets[0]))

        processed_train_data[direct] = (y, processed_datasets)
    
    return processed_train_data


def get_all_trials_models(processed_train_data, ):
    
    models = {}
    
    for direct in processed_train_data:
    
        labels, train_data = processed_train_data[direct]
    
        models[direct] = find_transformations(train_data, labels)
    
    return models


#Now, examining how the transformation looks

def plot_transformation(model, X, Xnew, y):
    
    w = model[0]
    b = model[1]
    
    predicted = Xnew@w + b #These hold the predictions for times t+1 -> k+1
    x_coord = [x*(TICK_TIME / 1000) for x in np.arange(len(y))]

    plt.figure(figsize=(18, 8))
    plt.grid()
    plt.plot(x_coord, y, color="violet", label="actual hidden state")
    plt.plot(x_coord, X[:,1], color="royalblue", label="observed")
    plt.plot(x_coord, predicted, color="green", label="Predicted")

    plt.legend()
    plt.show()