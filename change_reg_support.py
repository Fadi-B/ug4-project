### CONSTANTS ###

DIM = 5
DROP_FROM = 6


#imports

import numpy as np

from data_analyzer import *
from support import *
from prediction_error_evaluator import *

import copy

#Loading and processing relevant data
data = get_all_trial_datasets()
processed_train_data = get_all_trial_processed_datasets(data)

# Constants for end and start indices for the true link capacity
# Useful when determining which time step we are forecasting into (e.g t+1 or t+2) 
START_TIME_STEP = 1
END_TIME_STEP = 1

STEP_0 = 0
STEP_1 = 1
STEP_2 = 2
STEP_3 = 3
STEP_4 = 4
STEP_5 = 5
STEP_6 = 6
STEP_7 = 7
STEP_8 = 8

#Constants for the features to be dropped

BW_IGNORE = 0
RTT_GRAD_IGNORE = 1
QUEUE_DELAY_IGNORE = 2
INTER_ARRIVAL_IGNORE = 3

traces = ['TMobile-LTE', 'TMobile-UMTS', 'ATT-LTE', 'Verizon-LTE', 'Verizon-EVDO']

"""

NOT: IMPORTANT! This function will edit the original
     processed_train_data array.

Will process such that we have labels indicating

                        y_{t+1} - y_{t}

Note: We should double-check that we are not misaligning the
      time steps as processed train data already drops first y element
      
      Okay, so this processing will make it such that the first entry is the
      change from timestep t+1 -> t+2. This is because in previous processing
      we already drop the first element at time t.
      
      To compensate for this, we should drop the first datapoint in the dataset
      before doing our learning as that corresponds to time t, but now we want to
      ensure we start at time t+1 and forecast the change into t+2.
      
      This way we can do the learning for the forecast using the data returned
      by this function with any additional adjustments.
      
      step is which time step to forecast
      
      
      For step 0, we have labels as y_{t+2}-y_{t+1}
      and observations starting at y_{t+1}. This is
      forecasting 1 step ahead into the future
      
"""
def process_labels_and_dataset(processed_data, step):

    #Creating a deep copy is EXTREMELY IMPORTANT. Have been headbutting it for a while to figure this stupid shit out
    new_processed_data = copy.deepcopy(processed_data)
    
    #print("Start")
    
    for key in new_processed_data:
        
        labels = new_processed_data[key][LABELS]
        
        ### Processing the labels ###
        new_labels = []
        
        for i in range(step, len(labels) - END_TIME_STEP):
            
            current = labels[i]
            nextt = labels[i + 1]
            
            diff = nextt - current
            
            new_labels.append(diff)
        
        new_labels = np.array(new_labels)
        
        to_list = list(new_processed_data[key])
        to_list[LABELS] = new_labels
        
        new_processed_data[key] = tuple(to_list)
        
        ### Processing the datasets ###
        
        for i in range(0, TRIALS + 1): # +1 for the average of all trials at end of list
            
            X = np.copy(new_processed_data[key][PROCESSED_DATASETS][i])
            
            #print(np.std(X[:,3]))
            
            #Dropping first element to start at t + 1
            new_processed_data[key][PROCESSED_DATASETS][i] = X[1:X.shape[0]-step]
        
    return new_processed_data

"""
The drop parameter will determine what feature
we should exclude in learning the transformation.

Drop:
 - > 0 : ignore the estimated throughput
 - > 1 : ignore the rtt gradient
 - > 2 : ignore the queueing delay
 - > 3 : ignore the inter arrival time
"""
def get_linear_model(trace_name, drop=BW_IGNORE):
    
    models_dict = {}
    
    #Will not be accessible after new_process data created as it will be replaced with change in each timestep instead
    true_link_capacity = processed_train_data[trace_name][LABELS][:]
    
    new_processed_0 = process_labels_and_dataset(processed_train_data, STEP_0)
    new_processed_1 = process_labels_and_dataset(processed_train_data, STEP_1)
    new_processed_2 = process_labels_and_dataset(processed_train_data, STEP_2)
    new_processed_3 = process_labels_and_dataset(processed_train_data, STEP_3)
    new_processed_4 = process_labels_and_dataset(processed_train_data, STEP_4)
    new_processed_5 = process_labels_and_dataset(processed_train_data, STEP_5)
    new_processed_6 = process_labels_and_dataset(processed_train_data, STEP_6)
    new_processed_7 = process_labels_and_dataset(processed_train_data, STEP_7)
    new_processed_8 = process_labels_and_dataset(processed_train_data, STEP_8)
    
    new_processed = [new_processed_0, new_processed_1, new_processed_2, new_processed_3, new_processed_4, new_processed_5, new_processed_6, new_processed_7, new_processed_8]
    
    models_dict['STEP_0'] = {}
    models_dict['STEP_1'] = {}
    models_dict['STEP_2'] = {}
    models_dict['STEP_3'] = {}
    models_dict['STEP_4'] = {}
    models_dict['STEP_5'] = {}
    models_dict['STEP_6'] = {}
    models_dict['STEP_7'] = {}
    models_dict['STEP_8'] = {}
    
    j = 0
    
    for elem in new_processed:
    
        for i in range(0, TRIALS + 1):
    
            X = elem[trace_name][PROCESSED_DATASETS][i][:,:] #Dropping first few data points to outlier drop
            y = elem[trace_name][LABELS][:] #The labels are now the change in throughput between time steps
        
            #For now I am always dropping the current BW feature
            X_new = X[:,1:] #Dropping the pure throughput feature as we do not want to condition on it
        
            if (drop == BW_IGNORE):
            
                pass
        
            elif (drop == RTT_GRAD_IGNORE):
            
                #Dropping RTT Grad. column
                X_new = X_new[:,RTT_GRAD_IGNORE:]
            
            elif (drop == QUEUE_DELAY_IGNORE):
            
                temp_1 = X_new[:,0][:,None] #Just contains rtt grad now
                temp_2 = X_new[:,QUEUE_DELAY_IGNORE:]#[:,None] #Just contains inter arrival now
            
                #print(temp_1.shape)
                #print(temp_2.shape)
                #print(temp_2)
                X_new = np.hstack((temp_1, temp_2))
            
                #print(X_new.shape)
        
            elif (drop == INTER_ARRIVAL_IGNORE):
            
                X_new = X_new[:,:INTER_ARRIVAL_IGNORE - 1]
                #print(X_new.shape)
        
            else:
                pass
            

            #Fitting Simple Linear Regression
            w, b = fit_linreg_natural(X_new, y, 30)
            rmse_value = RMSE(X_new, y, w, b)
        
            models_dict['STEP_{}'.format(j)]["TRIAL_{}".format(i+1)] = [np.array([w, b], dtype=object), X_new, X, rmse_value]
            
        j = j + 1
 
    return models_dict, true_link_capacity


def get_predicted_sequence(model, X, start_point):
    
    w = model[0]
    b = model[1]
    
    predicted_change = X@w + b #These hold the predictions for times t+1 -> k+1
    
    #Computing the predicted throughput based on predicted change
    #predicted = y + predicted_change

    #Ideally want to start at true link capacity starting point and see how accurate we can predict henceforth
    predicted = [start_point]

    for i in range(1, len(predicted_change)):
    
        predicted.append(predicted[i - 1] + predicted_change[i])
    
    return predicted


def plot_pred(model, X, predicted, trace_name, true_capacity):
    
    w = model[0]
    b = model[1]
    
    #y = y[:len(y) - 1]
    #predicted_change = Xnew@w + b #These hold the predictions for times t+1 -> k+1
    
    #Computing the predicted throughput based on predicted change
    #predicted = y + predicted_change
    
    x_coord = [x*(TICK_TIME / 1000) for x in np.arange(len(true_capacity) - 1)]

    plt.figure(figsize=(16, 6))
    plt.grid()
    
    #The -1 is because we are considering changes between timesteps and so we will have 1 less data point
    plt.plot(x_coord, true_capacity[:len(true_capacity) - 1], color="violet", label="Ground Truth")
    plt.plot(x_coord, X[:,0], color="royalblue", label="Observed")
    plt.plot(x_coord, predicted, color="green", label="Predicted")
    
    plt.xlabel("Time (s)", fontsize=14)
    plt.ylabel("Throughput (Mbit/s)", fontsize=14)

    plt.legend()
    plt.show()
    
    
"""

Example Usage:


trace_name = 'TMobile-UMTS'

model, X_new, X, true_link_cap, rmse = get_linear_model(trace_name)
pred_seq = get_predicted_sequence(model, X_new, true_link_cap[1])
plot_pred(model, X, pred_seq, trace_name, true_link_cap)


"""