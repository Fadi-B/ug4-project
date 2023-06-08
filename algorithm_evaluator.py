#imports

import numpy as np
import matplotlib.pyplot as plt

from data_analyzer import *
from support import *
from prediction_error_evaluator import *


from change_reg_support import *

### CONSTANTS ###

DIM = 5
DROP_FROM = 6

#Loading and processing relevant data
data = get_all_trial_datasets()
processed_train_data = get_all_trial_processed_datasets(data)

new_processed = process_labels_and_dataset(processed_train_data, STEP_1)

def get_change_rmse(X, y):
    
    square_error = []

    for i in range(0, len(y) - 1):
    
        current = X[i]
    
        next_timestep = y[i]
    
        error = (next_timestep - current)**2
    
        square_error.append(error)

    rmse = np.sqrt(np.mean(square_error))
    
    return rmse

# Note: I have by default set sprout-ewma to use weight 1/4

def get_rmse_sprout_ewma(trace, alpha=1/4):
    
    true_link_capacity = processed_train_data[trace][LABELS][DROP_FROM:]  #Dropping first few data points to to outlier drop

    X = new_processed[trace][PROCESSED_DATASETS][50][DROP_FROM:,:] #Dropping first few data points to outlier drop

    #Only care about the throughput value for sprout-ma
    X = X[:,0]
    
    print(X.shape)
    
    # To calculate RMSE of a sprout-MA then note that it operates by assuming that there will be NO change in throughput
    # (in other words it continues at the same rate) based on the current measured one.
    # 
    # Hence, we are looking for how many entries were "zero" in the change. We are interested in how well an average
    # can actually predict the future change

    # In other words if the values at the corresponding time steps in the X and y array match then that is correct otherwise
    # we incur a penalty equivalent to the difference.

    # However, since we dropped an element from X in the process function, need to drop an element from the true_link_capacity
    # array to ensure we start at correct times.

    y = true_link_capacity[1:len(true_link_capacity) - 1]
    
    X_ewma = []

    # Create the ewma sequence based on the current data
    # Note: if alpha set to 1 then will simply be a moving average
    for i in range(0, len(X) -1):
    
        if (i == 0):
        
            X_ewma.append(X[i])
    
        else:
        
            value = (1-alpha)*X_ewma[i - 1] + alpha*X[i]
            X_ewma.append(value)

    X_ewma = np.array(X_ewma)
    
    rmse = get_change_rmse(X_ewma, y)
    
    print(rmse)
    
    return rmse

def get_min_ewma_alpha(trace):
    
    alphas = np.arange(0,1, 0.01)
    
    rmses = []
    
    for alpha in alphas:
        
        rmses.append(get_rmse_sprout_ewma(trace, alpha))
    
    index = 0
    
    for i in range(1, len(rmses)):
        
        rmse = rmses[i]
        
        if (rmses[index] > rmse):
            
            index = i
    
    return alphas[index]

def plot_sprout_ewma_rmse_vs_alpha(trace):
    
    alphas = np.arange(0,1, 0.01)
    
    rmses = []
    
    for alpha in alphas:
        
        rmses.append(get_rmse_sprout_ewma(trace, alpha))
    
    fig, axs = plt.subplots(figsize=(7, 4))
    
    axs.set_title("Sprout-EWMA RMSE vs weight", pad=20, fontsize=12)
    axs.set_xlabel("Alpha (Dimensionless)")
    axs.set_ylabel("RMSE (Mbit/s)")
    
    axs.grid()
    
    axs.plot(alphas, rmses)