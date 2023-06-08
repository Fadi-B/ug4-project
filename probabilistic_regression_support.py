import numpy as np
from support import *

def sigmoid(z):
    
    return 1/(1+np.exp(-z))

def apply_logreg(X, ww, bb):
    
    return sigmoid(X@ww + bb)

def fit_logreg_gradopt(X, yy, alpha):
    
    D = X.shape[1]
    args = (X, yy, alpha)
    init = (np.zeros(D), np.array(0))
    ww, bb = minimize_list(logreg_cost, init, args)
    return ww, bb

"""
This computes and returns the K logistic classifiers
"""

def invented_classification_models(X_train, y_train, K):
    
    
    mx = np.max(y_train); mn = np.min(y_train); hh = (mx-mn)/(K+1)
    thresholds = np.linspace(mn+hh, mx-hh, num=K, endpoint=True)

    models = [] #Will contain all the logistic reg. models

    for kk in range(K):
    
        labels = y_train > thresholds[kk]
    
        #Fitting logistic regression to these labels
        ww, bb = fit_logreg_gradopt(X_train, labels, alpha=30)
    
        models.append((ww, bb))
    
    return models

"""
This transforms the input matrix into a new
design matrix whose features are the predictions
of each of the logistic classifier models
"""
def invented_classification_transform(Xin, models, K):
    
    X = apply_logreg(Xin, models[0][0], models[0][1])[:,None]
    
    #Looping over the logistic reg. models
    for kk in range(1, K):
    
        model = models[kk]
    
        pred = apply_logreg(Xin, model[0], model[1])
    
        X = np.hstack((X, pred[:,None]))
    
    return X

def fit_prob_linear_reg(X_train, y_train, K=20):
    
    #Get the logistic classifier models
    models = invented_classification_models(X_train, y_train, K)

    #Create new design matrices from X_train and X_val
    X_train_log = invented_classification_transform(X_train, models, K)
    #X_val_log = invented_classification_transform(X_val, models, K)

    #Fitting a regularized linear regression model to the transformed datasets
    w_log_train, b_log_train = fit_linreg_gradopt(X_train_log, y_train, alpha=120)

    #train_log_RMSE = RMSE(X_train_log, y_train, w_log_train, b_log_train)
    #val_log_RMSE = RMSE(X_val_log, y_val, w_log_train, b_log_train)

    #print("RMSE Train = {:.8f} and RMSE Val = {:.8f}".format(train_log_RMSE, val_log_RMSE))
    
    return w_log_train, b_log_train, X_train_log