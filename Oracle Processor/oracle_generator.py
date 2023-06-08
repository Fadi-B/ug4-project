import numpy as np
import trace_file_processor as tp

import sys
import os

### Pantheon start up delay measured experimentally - Might vary between experiments slightly ###
PANTH_DELAY_FACTOR = 3.128 #3.128 #Seems to be this on average - cannot do better estimation than this tbh

def create_oracle_data(trace, granularity, delay_factor, oracle_filename):
    
    rate, time = tp.process_trace(trace, granularity)
    
    # Will hold the index of the entries in the trace that should be ignored
    # as pantheon starts a bit later
    ignore_index = -1
    
    for i in range(0, len(time)):
        
        # Should be careful here since if it is larger than 3.06
        # (e.g when using non-divisible granularity like 7ms) then might want
        # to include that instead of throwing it away as the pantheon delay itself is 3.06
        
        if (time[i] >= PANTH_DELAY_FACTOR):
            
            ignore_index = i

            # Break to ensure we do not loop alter true value of ignore_index  
            break
    
    rate_oracle = rate[ignore_index + 1:]

    N = 3

    #rate_oracle = np.convolve(rate_oracle, np.ones((N,))/N, mode='valid')

    rate_oracle = np.concatenate(([granularity], rate_oracle)) #Add granularity at head of list
    
    # The time array is not used in the bytes version
    tp.store_to_csv(rate_oracle, time, granularity, oracle_filename, version="bytes")
    
    return

def main():
    
    oracle_name = "oracle.txt"

    trace_file = sys.argv[1]
    granularity = float(sys.argv[2])
    
    
    #Check if file exists since we want to create brand new oracles
    if (os.path.isfile(oracle_name)):
        
        os.remove(oracle_name)

    if (os.path.isfile("elapsed_time.txt")):
        
        os.remove("elapsed_time.txt")

    
    create_oracle_data(trace_file, granularity, PANTH_DELAY_FACTOR, oracle_name)

    with open(r"oracle.txt", 'r') as fp:

    	for count, line in enumerate(fp):

          pass

    f = open("oracle_size.txt", "w")
    f.write(str(count + 1))
    f.close()

if __name__ == '__main__':
    main()
