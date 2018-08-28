import os
import paramiko
import random
import time
import json
import threading
import sys
from datetime import datetime
from threading import Thread
from numpy import median

startTime = datetime.now()

infra_config = json.load(open("config/infra_config.json"))
deployment =  json.load(open("config/deployment.json"))
device_types =  json.load(open("config/device_types.json"))
deployment_output = json.load(open("dump/infra/deployment_output.json"))

private_networks_dict = infra_config["private_networks"]
public_networks_dict = infra_config["public_networks"]

all_devices_list = infra_config["devices"].keys()

network_dict = {}
coremark_avg = coremark_list = []
coremark_devices_all = {}

print
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print "               iwconfig script                 "
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print


print "********************************************************"

iwconfig_result = []
iwconfig_dict = {}

#p = sys.argv[1]
#print "\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@\nNETWORK - {0}\n\n".format(p)
#p_dict = private_networks_dict[p]
#gw = p_dict["gateway"]
gw = "Fog-4"

pub_network = deployment_output[gw]["public_networks"].keys()
gw_host = deployment_output[gw]["public_networks"][pub_network[0]]["ip"]
gw_port = deployment_output[gw]["public_networks"][pub_network[0]]["port"]
gw_user = "pi"
gw_key = "/Users/shreyas/pi_key"

k = paramiko.RSAKey.from_private_key_file(gw_key)
gw_client = paramiko.SSHClient()
gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)

print "Starting iwconfig test in {}".format(gw)

command = "sudo iwconfig wlan0 | grep \"Bit\" | awk '{{print $2}}'"

for i in range(0,1000):
    stdin , stdout, stderr = gw_client.exec_command(command)
    result = stdout.read()
    result = result.split("\n")[0].split("=")[1]
    print "{}".format(result)
    iwconfig_result.append(float(result))

iwconfig_dict[gw] = iwconfig_result
gw_client.close()

with open('dump/iwconfig_test_{}'.format(p),'w') as file:
    file.write(json.dumps(iwconfig_dict))
