#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "USE: $0 <PCAP trace> <Destination IP>"
    echo "Example: ./run_pantheon.sh example.pcap 155.98.38.41"
    exit 1
fi

if [ ! -f "/local/repository/scripts/pantheon/ready" ]; then
    echo "Please wait, Pantheon is being installed."
    exit 1
fi

BASE_DIR="/local/repository/scripts"

cd $BASE_DIR

# Generating Pantheon trace out of a PCAP trace
mkdir -p "$BASE_DIR/tmp_pantheon_traces/"
PCAP_BASENAME=$(basename -- "$1")
PANTHEON_TRACE=${PCAP_BASENAME%.*}.x
./pcap_to_pantheon.py $1 $2 tmp_pantheon_traces/$PANTHEON_TRACE

# Emulate with Pantheon
cd pantheon
mkdir -p outputs/
PANTHEON_OUTPUT_DIR=$BASE_DIR/pantheon/outputs/${PANTHEON_TRACE%.*}
rm -Rf $PANTHEON_OUTPUT_DIR 2> /dev/null
mkdir $PANTHEON_OUTPUT_DIR

CC_SCHEMES="bbr copa cubic pcc sprout vegas verus vivace"

./src/experiments/test.py local --schemes "$CC_SCHEMES" --uplink-trace ../tmp_pantheon_traces/$PANTHEON_TRACE --data-dir $PANTHEON_OUTPUT_DIR

# Analyze emulation
src/analysis/analyze.py --data-dir $PANTHEON_OUTPUT_DIR

date
echo ""
echo ""
echo "Pantheon emulation completed using: $CC_SCHEMES"
echo "Run the following command to get the report:"
echo "scp $(whoami)@$(hostname):$PANTHEON_OUTPUT_DIR/pantheon_report.pdf ."