

""" IMPORTANT: This code was reused from the MLPR coursework at university of Edinburgh and adapted as required"""

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import cho_factor, cho_solve


def params_unwrap(param_vec, shapes, sizes):
    """Helper routine for minimize_list"""
    args = []
    pos = 0
    for i in range(len(shapes)):
        sz = sizes[i]
        args.append(param_vec[pos:pos+sz].reshape(shapes[i]))
        pos += sz
    return args


def params_wrap(param_list):
    """Helper routine for minimize_list"""
    param_list = [np.array(x) for x in param_list]
    shapes = [x.shape for x in param_list]
    sizes = [x.size for x in param_list]
    param_vec = np.zeros(sum(sizes))
    pos = 0
    for param in param_list:
        sz = param.size
        param_vec[pos:pos+sz] = param.ravel()
        pos += sz
    unwrap = lambda pvec: params_unwrap(pvec, shapes, sizes)
    return param_vec, unwrap


def minimize_list(cost, init_list, args):
    """Optimize a list of arrays (wrapper of scipy.optimize.minimize)

    The input function "cost" should take a list of parameters,
    followed by any extra arguments:
        cost(init_list, *args)
    should return the cost of the initial condition, and a list in the same
    format as init_list giving gradients of the cost wrt the parameters.

    The options to the optimizer have been hard-coded. You may wish
    to change disp to True to get more diagnostics. You may want to
    decrease maxiter while debugging. Although please report all results
    in Q2-5 using maxiter=500.
    """
    opt = {'maxiter': 500, 'disp': False}
    init, unwrap = params_wrap(init_list)
    def wrap_cost(vec, *args):
        E, params_bar = cost(unwrap(vec), *args)
        vec_bar, _ = params_wrap(params_bar)
        return E, vec_bar
    res = minimize(wrap_cost, init, args, 'L-BFGS-B', jac=True, options=opt)
    return unwrap(res.x)

def linreg_natural(params, X, yy, alpha):
    """Regularized least squares cost function and gradients

    Can be optimized with minimize_list -- see fit_linreg_gradopt for a
    demonstration.

    Inputs:
    params: tuple (ww, bb): weights ww (D,), bias bb scalar
         X: N,D design matrix of input features
        yy: N,  real-valued targets
     alpha: regularization constant

    Outputs: (E, [ww_bar, bb_bar]), cost and gradients
    """
    # Unpack parameters from list
    ww, bb = params

    # forward computation of error
    ff = np.dot(X, ww) + bb
    res = ff - yy
    E = np.dot(res, res) + alpha*np.dot(ww, ww)

    # reverse computation of gradients
    ff_bar = 2*res
    bb_bar = np.sum(ff_bar)
    ww_bar = np.dot(X.T, ff_bar) + 2*alpha*ww

    return E, [ww_bar, bb_bar]

def fit_linreg_natural(X, yy, alpha):
    
    D = X.shape[1]
    args = (X, yy, alpha)
    init = (np.zeros(D), np.array(0))
    ww, bb = minimize_list(linreg_natural, init, args)
    
    return ww, bb

def linreg_cost(params, X, yy, alpha):
    """Regularized least squares cost function and gradients

    Can be optimized with minimize_list -- see fit_linreg_gradopt for a
    demonstration.

    Inputs:
    params: tuple (ww, bb): weights ww (D,), bias bb scalar
         X: N,D design matrix of input features
        yy: N,  real-valued targets
     alpha: regularization constant

    Outputs: (E, [ww_bar, bb_bar]), cost and gradients
    """
    # Unpack parameters from list
    ww, bb = params

    # forward computation of error
    ff = np.dot(X, ww) + bb
    res = ff - yy
    E = np.dot(res, res) + alpha*res

    # reverse computation of gradients
    #i need to double check my notes I did on this
    #res_bar = 2*res + res
    res_bar = 2*res + alpha
    ff_bar = res_bar
    bb_bar = np.sum(ff_bar)
    ww_bar = np.dot(X.T, ff_bar)

    return E, [ww_bar, bb_bar]


def fit_linreg_gradopt(X, yy, alpha):
    
    D = X.shape[1]
    args = (X, yy, alpha)
    init = (np.zeros(D), np.array(0))
    ww, bb = minimize_list(linreg_cost, init, args)
    
    return ww, bb

def logreg_cost(params, X, yy, alpha):
    """Regularized logistic regression cost function and gradients

    Can be optimized with minimize_list -- see fit_linreg_gradopt for a
    demonstration of fitting a similar function.

    Inputs:
    params: tuple (ww, bb): weights ww (D,), bias bb scalar
         X: N,D design matrix of input features
        yy: N,  real-valued targets
     alpha: regularization constant

    Outputs: (E, [ww_bar, bb_bar]), cost and gradients
    """
    # Unpack parameters from list
    ww, bb = params

    # Force targets to be +/- 1
    yy = 2*(yy==1) - 1

    # forward computation of error
    aa = yy*(np.dot(X, ww) + bb)
    #print(aa)
    sigma = 1/(1 + np.exp(-aa))
    E = -np.sum(np.log(sigma)) + alpha*np.dot(ww, ww)

    # reverse computation of gradients
    aa_bar = sigma - 1
    bb_bar = np.dot(aa_bar, yy)
    ww_bar = np.dot(X.T, yy*aa_bar) + 2*alpha*ww

    return E, (ww_bar, bb_bar)