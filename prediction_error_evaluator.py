import numpy as np


"""

Computes the RMSE error based on the provided model

"""
def RMSE(X, yy, ww, bb):
    
    predictions = X@ww + bb
    
    return np.sqrt(np.mean((predictions-yy)**2))