#!/usr/bin/env python3

import sys
import subprocess

def tshark(pcap, ip):
    cmd = 'tshark -r {0} -Y "ip.dst == {1} && not(tcp.analysis.retransmission || tcp.analysis.fast_retransmission) && not(ssh)" -T fields -e frame.time_relative -e frame.len'.format(pcap, ip)
    output = subprocess.check_output(cmd, shell=True).strip().decode()
    return output.splitlines()

def generateOutput(lines, file):
    output = ''
    for l in lines:
        output += str(int(float(l.split()[0])*1000)) + '\n'
    with open(file, 'w') as f:
        f.write(output)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('USE: {0} <PCAP file> <Destination IP> <Output File (Pantheon trace)>'.format(sys.argv[0]))
        exit(1)
    lines = tshark(sys.argv[1], sys.argv[2])
    generateOutput(lines, sys.argv[3])

