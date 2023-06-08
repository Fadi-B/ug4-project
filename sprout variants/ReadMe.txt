IMPORTANT: The core of the files in this folder belongs to the author of Sprout Keith Winstein. I have been building upon the Sprout implementation to see whether I could replace their stochastic forecast with a more systematic version.

Note: Sprout-Fadi is generic in the sense that it is able to implement Sprout-Linear, GRU, LSTM, LIN-Historic etc. This is done
through changing the mode parameters at the top of the forecasting files and defining the corresponding forecast function/model

Note: For Sprout-Fadi to run you have to have a fdeep_model.json file in the the root directory (the directory from which the command is being run. By default this would be in the Pantheon folder. The fdeep_model.json will only be used if the NON_LINEAR variable is set to 1 in the kalman_filter.hh file.

Note: The actual Sprout files are too big and I have not bothered to include them here since all of them should be in the additions I made to the forked Pantheon repository.
