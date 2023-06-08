#imports

import numpy as np

from data_analyzer import *
from support import *
from prediction_error_evaluator import *


from change_reg_support import *

#Loading and processing relevant data
data = get_all_trial_datasets()
processed_train_data = get_all_trial_processed_datasets(data)

def root_mean_square_error(Xin, y_true, v, C_optimal):
    
    w = v[0]
    b = v[1]
    
    pred = Xin[:,:3*C_optimal]@w + b
    square_error = (y_true - pred).T@(y_true - pred)
    
    return np.sqrt((1/(len(Xin))) * square_error)


#Iterate over dataset backwards and adjust it as required

#Will look at a history of 20 cong. signals

STEPS = 20

def get_dataset_for_cong_signal_history(X, steps):

    X_adj = np.zeros((X.shape[0], (X.shape[1] - 1)*steps))

    for i in range(len(X)-1, -1, -1):
    
        #To loop over history of 20
        for j in range(0, steps):
        
            if (i - j < 0):
            
                data = np.repeat(0, 3)
        
            else:
            
                data = X[i - j][1:] #Dropping throughput feature as do not want to condition on it
        
            start_index = 3*j
        
            X_adj[i][start_index + 0] = data[0]     #RTT grad
            X_adj[i][start_index + 1] = data[1]     #Queue Delay
            X_adj[i][start_index + 2] = data[2]     #Inter Arrival time
    
    return X_adj



def train_historic_model(X_adj, y, steps):
    
    np.random.seed(3) #So we can reproduce our results
    
    X_proc = np.hstack((X_adj, y[:,None])) #Add labels to dataset since we will shuffle it around for robustness
    shuff_data = X_proc#np.random.permutation(X_proc) #Shuffle
    
    columns = shuff_data.shape[1]
    #Defining the data splits
    
    
    #print(X_proc.shape)

    #train_size_index = int(np.ceil(0.7*len(shuff_data))) #70% for training
    #temp = len(shuff_data) - train_size_index
    #val_size_index = int(train_size_index + int(temp/2)) #15% for val and test resp.
    #test_size_index = int(val_size_index + int(temp/2))

    #X_shuf_train = shuff_data[:train_size_index,:columns - 1]
    #X_shuf_val = shuff_data[train_size_index:val_size_index,:columns - 1]
    #X_shuf_test = shuff_data[val_size_index:,:columns - 1]

    #y_shuf_train = shuff_data[:train_size_index,columns - 1:columns].T[0]
    #y_shuf_val = shuff_data[train_size_index:val_size_index,columns - 1:columns].T[0]
    #y_shuf_test = shuff_data[val_size_index:,columns - 1:columns].T[0]
    
    
    train_size_index = int(np.ceil(0.7*len(shuff_data))) #70% for training

    X_shuf_train = shuff_data[:train_size_index,:columns - 1]
    X_shuf_val = shuff_data[train_size_index:,:columns - 1]
    
    y_shuf_train = shuff_data[:train_size_index,columns - 1]
    y_shuf_val = shuff_data[train_size_index:,columns - 1]
    

    #Investigating what history length is the best

    models = []

    for C in range(1, steps + 1): #Need at least 1 datapoint

        w_fit, b_fit = fit_linreg_natural(X_shuf_train[:,:3*C], y_shuf_train, 30)
        models.append(np.array((w_fit, b_fit), dtype=object))
    
    
    
    min_square_error_train = root_mean_square_error(X_shuf_train, y_shuf_train, models[0], 1)
    min_square_error_val = root_mean_square_error(X_shuf_val, y_shuf_val, models[0], 1)

    #Will hold training error for models of different histroy lengths
    square_error_train = []

    #Will hold validation error for models of different history lengths
    square_error_val = []

    square_error_train.append(min_square_error_train)
    square_error_val.append(min_square_error_val)

    opt_C_train = 1
    opt_C_val = 1

    for i in range(1, len(models)):
    
        min_square_error_train_new = root_mean_square_error(X_shuf_train, y_shuf_train, models[i], i + 1)
        min_square_error_val_new = root_mean_square_error(X_shuf_val, y_shuf_val, models[i], i + 1)
    
        square_error_train.append(min_square_error_train_new)
        square_error_val.append(min_square_error_val_new)
    
        if (min_square_error_train_new < min_square_error_train):
        
            opt_C_train = i + 1
            min_square_error_train = min_square_error_train_new
    
        if (min_square_error_val_new < min_square_error_val):
        
            opt_C_val = i + 1
            min_square_error_val = min_square_error_val_new
    
    #print("RMSE Train: {}".format(square_error_train))
    #print("RMSE Val: {}".format(square_error_val))
    
    return models, opt_C_val, X_shuf_val, y_shuf_val, square_error_train, square_error_val

def get_historic_model(trace_name, steps):
    
    models_dict = {}
    
    #Will not be accessible after new_process data created as it will be replaced with change in each timestep instead
    true_link_capacity = processed_train_data[trace_name][LABELS][DROP_FROM:]
    
    new_processed = process_labels_and_dataset(processed_train_data)

   
    for i in range(0, TRIALS):
    
        X = new_processed[trace_name][PROCESSED_DATASETS][i][DROP_FROM:,:] #Dropping first few data points to outlier drop
        y = new_processed[trace_name][LABELS][DROP_FROM:] #The labels are now the change in throughput between time steps

        X_adj = get_dataset_for_cong_signal_history(X, steps)
        models, opt, X_shuf_val, y_shuf_val, square_error_train, square_error_val = train_historic_model(X_adj, y, steps)
        
        predictor_best_val = models[opt - 1]
        rmse_value = root_mean_square_error(X_shuf_val, y_shuf_val, predictor_best_val, opt)
        
        #will containe everything with respect to opt_c
        models_dict["TRIAL_{}".format(i+1)] = [predictor_best_val, X_adj, X, rmse_value, opt, models, square_error_train, square_error_val]
 
    return models_dict, true_link_capacity

SINGLE = 'single'
ALL = 'all'

#Mode can either be single or all. Using all will plot the curves for all traces on the same plot
def plot_historic_optimization_curve(trace_name, steps, models_dict={}, mode='single'):
    
    fig, axs = plt.subplots(1, 1, figsize=(7, 4))
    #print("afafafaf")
    square_error_train = []
    square_error_val = []
    
    #Will hold colors for train and val for the diff. traces
    color_sets = [('#1f77b4', 'orange'), ('forestgreen', 'limegreen'), ('aquamarine','lightseagreen'), ('cadetblue','powderblue'), ('deeppink', 'hotpink')]
    
    provided = False
    
    if bool(models_dict):
        provided = True
    
    #traces is defined in change_reg_support.py
    i = 0
    for trace in traces: 
    
        if (mode==SINGLE and (not trace==trace_name)): 
            continue 
        elif (mode==ALL):
            trace_name=trace
            print(trace_name)
            
        if provided:
        
            _, _, _, opt, _, square_error_train, square_error_val = models_dict[trace_name]["TRIAL_1"]
    
        else:
        
            models_dict, true_link_capacity = get_historic_model(trace_name, steps)
            _, _, _, _, opt, _, square_error_train, square_error_val = models_dict["TRIAL_1"]
    
        print("Optimal Value for Trial 1: {}".format(opt))
    
        train_err = np.array(square_error_train)
        val_err = np.array(square_error_val)
    
        for i in range(1, TRIALS):
        
            if provided:
        
                _, _, _, opt, _, square_error_train, square_error_val = models_dict[trace_name]["TRIAL_{}".format(i+1)]
        
            else:
            
                _, _, _, _, opt, _, square_error_train, square_error_val = models_dict["TRIAL_{}".format(i+1)]
        
            print("Optimal Value for Trial {}: {}".format(i+1, opt))
        
            train_err = np.vstack((train_err, square_error_train))
            val_err = np.vstack((val_err, square_error_val))
    
        #Need to get the mean and std across rows
    
        train_err_ave = np.mean(train_err, axis=0)
    
        #print(train_err_ave)
    
        train_err_std = np.std(train_err, axis=0)
    
        val_err_ave = np.mean(val_err, axis=0)
        val_err_std = np.std(val_err, axis=0)
    
        x_axis = np.arange(steps + 1)[1:]
    
        axs.plot(x_axis, train_err_ave, label=trace_name + ': Train', color=color_sets[i][0])
        axs.plot(x_axis, val_err_ave, label=trace_name + ': Val', color=color_sets[i][1])
    
        width = 1
        cap = 3
    
        axs.errorbar(x_axis, train_err_ave, train_err_std, capsize=cap, elinewidth=width, color=color_sets[i][0])
        axs.errorbar(x_axis, val_err_ave, val_err_std, capsize=cap, elinewidth=width, color=color_sets[i][1])
    
        axs.set_xlabel("Historic Length")
        axs.set_ylabel("RMSE")
        
        if (mode==ALL):
            axs.set_title("Shows train and validation RMSEs for the tuning", pad=20)
        else:
            axs.set_title(trace_name + ": Five 2 minute duration trials", pad=20)
    
        axs.grid()
        axs.legend()
        
        i = i + 1
    
    return
