cd pantheon/

#var=$(cat ../traces.txt)

CC_SCHEMES="sprout-ma"

RUNS=1
#TIME=30 #Hard-code since we just want to look at granularity experiments

GRANULARITY=60

sudo src/experiments/setup.py --setup --schemes "$CC_SCHEMES"

mkdir TRAIN-DATA/

# For naming the different trials
i=0

while IFS=":" read line val
do

   DIR=TRAIN-DATA/${line}
   if [ -d ${DIR} ]; then
     rm -r ${DIR}
     echo "Removing previous data for ${DIR}..."
   fi

   mkdir TRAIN-DATA/"${line}"

   for i in {1..5..1}
   do

   	TIME=$((val*60))

   	TRACE_UP=/usr/share/mahimahi/traces/${line}-driving.up
   	TRACE_DOWN=/usr/share/mahimahi/traces/${line}-driving.down

   	src/experiments/test.py local --schemes "$CC_SCHEMES" --uplink-trace ${TRACE_UP} --downlink-trace ${TRACE_DOWN} -t ${TIME} --run-times ${RUNS} --pkill-cleanup
   	#src/analysis/analyze.py --data-dir TRAIN-DATA/${line}

   	mv rtt_grad_data.csv TRAIN-DATA/${line}/rtt_grad_data_run_${i}.csv
   	mv throughput_data.csv TRAIN-DATA/${line}/throughput_data_run_${i}.csv
   	mv inter_arrival_data.csv TRAIN-DATA/${line}/inter_arrival_data_run_${i}.csv
   	mv queue_delay_data.csv TRAIN-DATA/${line}/queue_delay_data_run_${i}.csv

   done

done < ../traces.txt
