import os
import paramiko
import random
import time
import json
import sys
from datetime import datetime
from threading import Thread

startTime = datetime.now()

cm_device_all = json.load(open("cm_device_all"))

devices = cm_device_all.keys()

f_Pi3B_p = open("f_Pi3B_p","w")
f_Pi3B = open("f_Pi3B","w")

pi3b_p = {}
pi3b = {}

for d in devices:
    if cm_device_all[d]["device_type"] == "Pi3B+":
        pi3b_p[d] = cm_device_all[d]
    elif cm_device_all[d]["device_type"] == "Pi3B":
        pi3b[d] = cm_device_all[d]

"""
pi3b_p_devices = pi3b_p.keys()
for p in pi3b_p_devices:
    print p
    cm = pi3b_p[p]["coremark"]
    for c in cm:
        print c
    time.sleep(15)
"""

pi3b_devices = pi3b.keys()
for p in pi3b_devices:
    print p
    cm = pi3b[p]["coremark"]
    for c in cm:
        print c
    time.sleep(15)



"""
for i in range(0, 205):
    for j in range(0,len(pi3b_p_devices)):

        d = pi3b_p_devices[j]
        cm = pi3b_p[d]["coremark"]
        if(i < len(cm)):
            f_Pi3B_p.write(cm[i]+",")
        else:
            f_Pi3B_p.write(",")

    f_Pi3B_p.write("\n")
"""














"""
sanity = {}

latency_delta = open("latency_delta","w")
for i in range(1,len(sys.argv)):
    sanity[i] = json.load(open(sys.argv[i])) #sys.argv[i]

#print sanity
print "latency"
print
sanity_i = {}
for i in sanity:
    sanity_i = sanity[i]
    for j in sanity_i["latency_numbers"]:
        latency = sanity_i["latency_numbers"][j]
        if(latency["observed_latency_ms"]):
            diff = float(latency["observed_latency_ms"]) - (2*float(sanity_i["expected_latency_ms"]))
            per = diff / (2*float(sanity_i["expected_latency_ms"])) * 100
            print per
            latency_delta.write(str(per)+"\n")
latency_delta.close()


bandwidth_delta = open("bandwidth_delta","w")
print
print "bandwidth"
print

sanity_i = {}
for i in sanity:
    sanity_i = sanity[i]
    for j in sanity_i["bandwidth_numbers"]:
        bw = sanity_i["bandwidth_numbers"][j]
        if(bw["observed_bandwidth_mbps"]):
            diff = float(bw["observed_bandwidth_mbps"]) - float(sanity_i["expected_bandwidth_mbps"])
            per = diff/(float(sanity_i["expected_bandwidth_mbps"])) * 100
            print per
            bandwidth_delta.write(str(per)+"\n")
bandwidth_delta.close()
"""
