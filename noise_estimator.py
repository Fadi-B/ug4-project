
import numpy as np

from change_reg_support import *

from models import *

#Constants

DIM = 5
DROP_FROM = 6

#Loading and processing relevant data
data = get_all_trial_datasets()
processed_train_data = get_all_trial_processed_datasets(data)







"""

When estimating the transformation matrix we looked at
what linear transformation would be best suitable to take
us from state x_t to x_t+1 for all x.

We are using the observed RTTGrad, QueueDelay, Interarrival
time as the ground truth for the hidden state and that the only
thing that will be uncertain is how we estimate the true
change in the link capacity for the next time step.

Hence, we are mainly interested in the residuals for that prediction
as the residuals for the other predictions will be 0 assuming that the
values we have are the ground truth

    -> For now, I am not so sure whether it matters if we assume them to be
       ground truth or not since I am assuming that between experiments they
       might potentially have a systematic shift but not a random one.
    -> Not so sure how valid that assumption would be though, but it simplifies
       things for me right now.


@Parameters

 -> Hidden_state: Will be the true change in link capacity between time steps
 -> X: Will be our 'true' state dimensions that we use to predict the change in link capacity.
       Will use this to look at how our predictions from this are inline with our hidden state
 -> model: Holds the parameters of our transformation model
 -> D: Dimensions we are using

"""

def estimate_system_noise_cov(hidden_state, X, model, D):
    
    ww = model[0]
    bb = model[1]
    
    predictions = X@ww + bb
    
    #residuals for the change in link capacity
    residuals_change = (hidden_state - predictions)[:,None]
    
    rmse = np.sqrt(np.mean(residuals_change**2))
    print(rmse)
    print(np.std(residuals_change))
    
    #Residuals for bias, RTTGrad, QueueDelay and Interarrival time will be 0
    
    res_rest = np.zeros_like(residuals_change)
    
    res_data = res_rest
    
    for i in range (1, D):
    
        if i == 1:
            
            res_data = np.hstack((res_data, residuals_change))
        
        else:
            
            res_data = np.hstack((res_data, res_rest))
    
    #Practically the variance of the residuals
    noise_cov = np.cov(res_data.T)
    
    return noise_cov
    
"""

Estimating the observation noise covariance will require us to
look at how what we observe is different from the actual hidden
state, which in this case (for simplicity) will be the 
throughput observed versus the actual one.

@Parameters

    -> Hidden_state: The true throughput
    -> Observation: The throughput recorded at the receiver


This is still related to the change in throughput error estimated
in the system_noise_cov as we they will be part of the same dimension entry

The rest of the dimension entries will practically be 0 following the same 
argument as provided for the estimate_system_noise_cov matrix.

"""
def estimate_observation_noise_cov(hidden_state, observation, D):
    
    #We do not have a noiseless correction matrix in our design so things simplify
    residuals = (hidden_state - observation)[:,None]
    
    #Residuals for bias, RTTGrad, QueueDelay and Interarrival time will be 0
    
    res_rest = np.zeros_like(residuals)
    
    res_data = res_rest
    
    for i in range (1, D):
    
        if i == 1:
            
            res_data = np.hstack((res_data, residuals))
        
        else:
            
            res_data = np.hstack((res_data, res_rest))
            
    observation_noise_cov = np.cov(res_data.T)
    
    return observation_noise_cov


"""

Will give the system and observation noise variances.

returns: dict of system_noise_variance, observartion_noise_variance for each trial

"""

def get_noise_variances(trace, timestep='STEP_0'):
    
    noise_dict = {}

    true_link_capacity = processed_train_data[trace][LABELS][DROP_FROM:]  #Dropping first few data points to outlier drop

    new_processed = process_labels_and_dataset(processed_train_data, int(timestep[-1:]))
    
    model_dict = get_models_dict(timestep=timestep)
    
    for i in range(0, TRIALS):

        X = new_processed[trace][PROCESSED_DATASETS][i][DROP_FROM:,:] #Dropping first few data points to outlier drop

        y = new_processed[trace][LABELS][DROP_FROM:] #The labels are now the change in throughput between time steps

        system_noise = estimate_system_noise_cov(y, X[:,1:], model_dict[trace]['TRIAL_{}'.format(i+1)][0], DIM)

        #Note true_link_capacity is truth at t+1 whereas X is observed at t. We drop first element such that they overlap in this case
        #since we are interested in the observation in this case and not prediction
        observation_noise = estimate_observation_noise_cov(true_link_capacity[START_TIME_STEP:len(true_link_capacity)-1], X[1:,0], DIM)
    
        sys_n = system_noise[1][1]
        obs_n = observation_noise[1][1]
    
        noise_dict['TRIAL_{}'.format(i+1)] = (np.sqrt(sys_n), np.sqrt(obs_n))
    
    return noise_dict



    