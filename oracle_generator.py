import numpy as np
import trace_file_processor as tp

import sys
import os

### Pantheon start up delay measured experimentally - Might vary between experiments slightly ###
PANTH_DELAY_FACTOR = 3.128

def create_oracle_data(trace, granularity, delay_factor, oracle_filename):
    
    rate, time = tp.process_trace(trace, granularity)
    
    # Will hold the index of the entries in the trace that should be ignored
    # as pantheon starts a bit later
    ignore_index = 0
    
    for i in range(0, len(time)):
        
        # Should be careful here since if it is larger than 3.06
        # (e.g when using non-divisible granularity like 7ms) then might want
        # to include that instead of throwing it away as the pantheon delay itself is 3.06
        
        if (time[i] >= PANTH_DELAY_FACTOR):
            
            ignore_index = i

            # Break to ensure we do not loop alter true value of ignore_index  
            break
    
    rate_oracle = rate[ignore_index + 1:]
    rate_oracle = np.concatenate(([granularity], rate_oracle)) #Add granularity at head of list
    
    # The time array is not used in the bytes version
    tp.store_to_csv(rate_oracle, np.array([]), granularity, oracle_filename, version="bytes")
    
    return

def read_oracle(path):
    tmp = []
    with open(path, 'r') as f:
        lines = f.readlines()
        count = 0
        for l in lines:
            #To skip the granularity
            if count == 0:
                count = count + 1
                continue
            line = l.replace("\n","")
            tmp.append(float(line))
    return tmp

def main():
    
    oracle_name = "oracle.txt"

    trace_file = sys.argv[0]
    granularity = sys.argv[1]
    
    
    #Check if file exists since we want to create brand new oracles
    if (os.path.isfile(oracle_name)):
        
        os.remove(oracle_name)

    
    create_oracle_data(trace_file, granularity, PANTH_DELAY_FACTOR, oracle_name)

if __name__ == '__main__':
    main()