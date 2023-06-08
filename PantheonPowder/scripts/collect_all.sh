cd pantheon/

#var=$(cat ../traces.txt)

CC_SCHEMES="bbr copa cubic indigo ledbat pcc pcc_experimental sprout vegas verus vivace sprout-ewma sprout-fadi sprout-0 sprout-5 sprout-25 sprout-50 sprout-75 sprout-oracle"

#CC_SCHEMES="bbr verus sprout sprout-oracle"

RUNS=1

GRANULARITY=60

sudo src/experiments/setup.py --setup --schemes "$CC_SCHEMES"

while IFS=":" read line val
do
   DIR=${line}
   if [ -d ${DIR} ]; then
     rm -r ${DIR}
     echo "Removing previous data for ${DIR}..."
   fi
   TIME=$((val*60))
   echo $TIME
   echo $line
   mkdir "${line}"
   TRACE_UP=/usr/share/mahimahi/traces/${line}-driving.up
   TRACE_DOWN=/usr/share/mahimahi/traces/${line}-driving.down
   python oracle_generator.py ${TRACE_UP} ${GRANULARITY} #For sprout-oracle data
   src/experiments/test.py local --schemes "$CC_SCHEMES" --uplink-trace ${TRACE_UP} --downlink-trace ${TRACE_DOWN} --data-dir ${line} -t ${TIME} --run-times ${RUNS} --pkill-cleanup
   src/analysis/analyze.py --data-dir ${line}
done < ../traces.txt
