cd pantheon/

#var=$(cat ../traces.txt)

CC_SCHEMES="sprout sprout-oracle cubic"

RUNS=1
#TIME=30 #Hard-code since we just want to look at granularity experiments

GRANULARITY=60

sudo src/experiments/setup.py --setup --schemes "$CC_SCHEMES"

mkdir ORACLE/

while IFS=":" read line val
do

   DIR=ORACLE/${line}
   if [ -d ${DIR} ]; then
     rm -r ${DIR}
     echo "Removing previous data for ${DIR}..."
   fi

   mkdir ORACLE/"${line}"

   TIME=$((val*60))

   TRACE_UP=/usr/share/mahimahi/traces/${line}-driving.up
   TRACE_DOWN=/usr/share/mahimahi/traces/${line}-driving.down
   python oracle_generator.py ${TRACE_UP} ${GRANULARITY} #For sprout-oracle data
   src/experiments/test.py local --schemes "$CC_SCHEMES" --uplink-trace ${TRACE_UP} --downlink-trace ${TRACE_DOWN} --data-dir ORACLE/${line} -t ${TIME} --run-times ${RUNS} --pkill-cleanup
   src/analysis/analyze.py --data-dir ORACLE/${line}

done < ../traces.txt
