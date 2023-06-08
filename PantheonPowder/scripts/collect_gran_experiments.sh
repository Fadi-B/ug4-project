cd pantheon/

#var=$(cat ../traces.txt)

CC_SCHEMES="sprout-oracle"

RUNS=1
TIME=30 #Hard-code since we just want to look at granularity experiments

sudo src/experiments/setup.py --setup --schemes "$CC_SCHEMES"

# Making directory for granularity experiment data
if [ -d GRAN ]; then
     rm -r GRAN
     echo "Removing GRAN data..."
   fi

mkdir GRAN/

while IFS=":" read line val
do

  TRACE_UP=/usr/share/mahimahi/traces/${line}-driving.up
  TRACE_DOWN=/usr/share/mahimahi/traces/${line}-driving.down

  for i in {10..500..10}
  do
     GRANULARITY=${i}
     mkdir GRAN/"$line"/"$GRANULARITY"
     python oracle_generator.py ${TRACE_UP} ${GRANULARITY} #For sprout-oracle data
     src/experiments/test.py local --schemes "$CC_SCHEMES" --uplink-trace ${TRACE_UP} --downlink-trace ${TRACE_DOWN} --data-dir GRAN/${line}/${GRANULARITY} -t ${TIME} --run-times ${RUNS} --pkill-cleanup
     src/analysis/analyze.py --data-dir GRAN/${line}/${GRANULARITY}

  done

done < ../traces.txt
