from change_reg_support import *
from historic_model import *

LINEAR = 'linear'
HISTORIC = 'historic'


def get_model(trace_name, steps=20, mode='linear'):
    
    if (mode==LINEAR):
        
        return get_linear_model(trace_name)
    
    elif (mode==HISTORIC):
        
        return get_historic_model(trace_name, steps)
    
    else:
        
        pass

    
def get_models_dict(mode='linear', steps=20, timestep='STEP_1'):

    model_dict = {}

    for elem in traces:
    
        if (mode==LINEAR):
            
            models, true_link_cap = get_linear_model(elem)
        
        elif (mode==HISTORIC):
            
            models, true_link_cap = get_historic_model(elem, steps)
        
        trial_dict = {}
        
        for i in range(0, TRIALS + 1):
            
            if (mode==LINEAR):
                
                model, X_new, X, rmse = models[timestep]["TRIAL_{}".format(i+1)]
            
            elif (mode==HISTORIC):
                
                model, X_new, X, rmse, opt, all_models, square_error_train, square_error_val = models["TRIAL_{}".format(i+1)]
    
            #Drop the observed throughput feature
            X = X[:,1:]
            #print(np.std(X[:,2]))
    
            #Dropping last element as going between timesteps
            cap = true_link_cap[int(timestep[-1:]):len(true_link_cap) - END_TIME_STEP]
    
            #Add the true throughput instead (so we can see correlation later on)
            Xp = np.hstack((cap[:,None], X))
            
            if (mode==LINEAR):
                
                trial_dict["TRIAL_{}".format(i+1)] = [model, rmse, Xp]
                
            elif (mode==HISTORIC):
                
                trial_dict["TRIAL_{}".format(i+1)] = [model, rmse, Xp, opt, all_models, square_error_train, square_error_val]
    
        model_dict[elem] = trial_dict
    
    if (mode==HISTORIC):
        
        #Want to have all modelss that were learnt w.r.t different history lengths as well
        return model_dict

    #For linear
    return model_dict
        