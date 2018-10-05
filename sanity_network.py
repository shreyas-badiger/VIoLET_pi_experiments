import os
import paramiko
import random
import time
import json
import threading
import sys
from datetime import datetime
from threading import Thread

startTime = datetime.now()

network_type = sys.argv[1]
network = sys.argv[2]


infra_config = json.load(open("config/infra_config.json"))
deployment =  json.load(open("config/deployment.json"))
device_types =  json.load(open("config/device_types.json"))
deployment_output = json.load(open("dump/infra/deployment_output.json"))

private_networks_dict = infra_config["private_networks"]
public_networks_dict = infra_config["public_networks"]

network_dict = {}

if network_type == "pvt":
    gw = private_networks_dict[network]["gateway"]
    devices = private_networks_dict[network]["devices"]
    network_dict = private_networks_dict
    network_t = "private_networks"
elif network_type == "pub":
    devices = public_networks_dict[network]["devices"]
    network_dict = public_networks_dict
    network_t = "public_networks"
else:
    print "Wrong network type. It has to be either \"pvt\" or \"pub\""
    sys.exit()


print
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print "               Sanity check                   "
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print

iperf = {}
print "**************************** [Sanity] Bandwidth, gateway, latency allocation****************************"
print "-------------------------------------------------------------"
print "{0}\n".format(network)
print "Expected BW - {0}Mbps\nExpected Latency -{1}ms".format(network_dict[network]["bandwidth_mbps"],network_dict[network]["latency_ms"])
print "-------------------------------------------------------------\n"

iperf["expected_bandwidth_mbps"] = network_dict[network]["bandwidth_mbps"]
iperf["expected_latency_ms"] = network_dict[network]["latency_ms"]


#BANDWIDTH
print "*****BANDWIDTH*****"
num_connected_devices = len(devices)
iperf_numbers = {}
latency_numbers = {}
if network_type == "pub":
    for i in range(0,num_connected_devices):
        device1 = devices[i]
        device1_host = deployment_output[device1][network_t][network]["ip"]
        device1_port = deployment_output[device1][network_t][network]["port"]
        device1_user = "pi"
        device1_key = "/Users/shreyas/pi_key"

    	for j in range(i+1,num_connected_devices):
            iperf_i = {}

            k = paramiko.RSAKey.from_private_key_file(device1_key)

    	    device1_client = paramiko.SSHClient()
    	    device1_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    device1_client.connect(hostname = device1_host, port = device1_port, username = device1_user, pkey = k)

            command = "iperf3 -s -p 4343"
            stdin , stdout, stderr = device1_client.exec_command(command)
            ip = deployment_output[device1][network_t][network]["device_ip"]

	    device1_client.close()
	    device2 = devices[j]
            print "{0} --> {1}".format(device2, device1)


            if device2 == "Fog-4":
                gw = "Fog-1"
                pub_network = deployment_output[gw]["public_networks"].keys()
                gw_host = deployment_output[gw]["public_networks"][pub_network[0]]["ip"]
                gw_port = int(deployment_output[gw]["public_networks"][pub_network[0]]["port"])
                gw_user = "pi"
                gw_key = "/Users/shreyas/pi_key"
                k = paramiko.RSAKey.from_private_key_file(gw_key)

    	        gw_client2 = paramiko.SSHClient()
    	        gw_client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	        gw_client2.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
                gw_client2_transport = gw_client2.get_transport()

	        device2_host = deployment_output[device2][network_t][network]["device_ip"]
                device2_port = 22
                device2_user = "ubuntu"
	        local_addr = (gw_host, gw_port)
	        dest_addr = (device2_host, device2_port)
                #print "local_addr ={} dest_addr ={} gw_port={} device2_port={}".format(local_addr,dest_addr,gw_port,device2_port)
	        gw_client2_channel = gw_client2_transport.open_channel("direct-tcpip", dest_addr, local_addr)

                device2_client = paramiko.SSHClient()
                device2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	        device2_client.connect(hostname = device2_host, username = device2_user, pkey = k, sock = gw_client2_channel)

            else:
                device2_host = deployment_output[device2][network_t][network]["ip"]
                device2_port = deployment_output[device2][network_t][network]["port"]
                device2_user = "pi"
    	        device2_client = paramiko.SSHClient()
    	        device2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	        device2_client.connect(hostname = device2_host, port = device2_port, username = device2_user, pkey = k)

            if device2 != "Fog-4":
                command = "sudo iwconfig wlan0 | grep \"Bit\" | awk '{{print $2}}'"
    	        stdin , stdout, stderr = device2_client.exec_command(command)
    	        result = stdout.read()
    	        result = result.split("\n")[0].split("=")[1]
    	        print "expected - {}".format(result)
	        iperf_i["expected_bandwidth_mbps"] = result

	    command = "iperf3 -c {0} -p 4343 | grep sender | awk '{{print $7}}' &".format(ip)
	    stdin , stdout, stderr = device2_client.exec_command(command)
	    bw = stdout.read()
	    bw = bw.replace(' ','')[:-1]
	    print "Observed BW - {0}Mbps".format(bw)
	    iperf_i["device1"] = device1
	    iperf_i["device2"] = device2
	    iperf_i["observed_bandwidth_mbps"] = bw
	    iperf_numbers[device1+"_"+device2]= iperf_i

    	    command = "fping -e -c20 -t500 {0} | grep bytes".format(ip)
    	    stdin , stdout, stderr = device2_client.exec_command(command,timeout = 500)

	    latency_i = {}
    	    latency_i["device_1"] = device1
    	    latency_i["device_2"] = device2

            output = stdout.read()
    	    output = output.split("\n")
    	    if(len(output)>1):
                output = output[1].split(" ")
                if(output[5]):
		    print "Observed latency - {0}ms (rtt)\n".format(output[5])
            	    latency_i["observed_latency_ms"]= output[5]
                latency_numbers[device1+"_"+device2] = latency_i
    	    else:
       	        print "ERROR! {0} <-> {1} are either not connected or not in same network".format(device1,device2)
	    device1_client.close()
            device2_client.close()

    iperf["bandwidth_numbers"] = iperf_numbers
    iperf["latency_numbers"] = latency_numbers



if network_type == "pvt":
    pub_network = deployment_output[gw]["public_networks"].keys()
    gw_host = deployment_output[gw]["public_networks"][pub_network[0]]["ip"]
    gw_port = deployment_output[gw]["public_networks"][pub_network[0]]["port"]
    gw_user = "pi"
    gw_key = "/Users/shreyas/pi_key"

    for i in range(0,num_connected_devices):
        iperf_i = {}
    	k = paramiko.RSAKey.from_private_key_file(gw_key)
    	gw_client = paramiko.SSHClient()
    	gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)

        command = "iperf3 -s -p 4343"
        stdin , stdout, stderr = gw_client.exec_command(command)
        ip = deployment_output[gw][network_t][network]

	gw_client.close()

    	gw_client2 = paramiko.SSHClient()
    	gw_client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	gw_client2.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
        gw_client2_transport = gw_client2.get_transport()

	device2 = devices[i]
	device2_host = deployment_output[device2][network_t][network]
        device2_port = 22
        device2_user = "pi"
	local_addr = (gw_host, gw_port)
	dest_addr = (device2_host, device2_port)
        print "local_addr ={} dest_addr ={} gw_port={} device2_port={}".format(local_addr,dest_addr,gw_port,device2_port)
	gw_client2_channel = gw_client2_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        device2_client = paramiko.SSHClient()
        device2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	device2_client.connect(hostname = device2_host, username = device2_user, pkey = k, sock = gw_client2_channel)

	command = "iperf3 -c {0} -p 4343 | grep sender | awk '{{print $7}}' &".format(ip)
	stdin , stdout, stderr = device2_client.exec_command(command)
        print stderr.read()

	bw = stdout.read()
	bw = bw.replace(' ','')[:-1]
	print "\t{0} <-> {1} [{2}Mbps]".format(gw, device2, bw)
	iperf_i["device1"] = gw
	iperf_i["device2"] = device2
	iperf_i["observed_bandwidth_mbps"] = bw
	iperf_numbers[gw+"_"+device2]= iperf_i

	gw_client2.close()
	device2_client.close()


    for i in range(0,num_connected_devices):
    	for j in range(i+1,num_connected_devices):
            iperf_i = {}
    	    k = paramiko.RSAKey.from_private_key_file(gw_key)
    	    gw_client = paramiko.SSHClient()
    	    gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
            gw_client_transport = gw_client.get_transport()

	    device1 = devices[i]
            device1_host = deployment_output[device1][network_t][network]
            device1_port = 22
            device1_user = "pi"
	    local_addr = (gw_host, gw_port)
	    dest_addr = (device1_host, device1_port)
	    gw_client_channel = gw_client_transport.open_channel("direct-tcpip", dest_addr, local_addr)

            device1_client = paramiko.SSHClient()
            device1_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    device1_client.connect(hostname = device1_host, username = device1_user, pkey = k, sock = gw_client_channel)

            command = "iperf3 -s -p 4343"
            stdin , stdout, stderr = device1_client.exec_command(command)
            ip = deployment_output[device1][network_t][network]

            device1_client.close()
	    gw_client.close()


            k = paramiko.RSAKey.from_private_key_file(gw_key)
    	    gw_client2 = paramiko.SSHClient()
    	    gw_client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	    gw_client2.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
            gw_client2_transport = gw_client2.get_transport()

	    device2 = devices[j]
	    device2_host = deployment_output[device2][network_t][network]
            device2_port = 22
            device2_user = "pi"
	    local_addr = (gw_host, gw_port)
	    dest_addr = (device2_host, device2_port)
	    gw_client2_channel = gw_client2_transport.open_channel("direct-tcpip", dest_addr, local_addr)

            device2_client = paramiko.SSHClient()
            device2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    device2_client.connect(hostname = device2_host, username = device2_user, pkey = k, sock = gw_client2_channel)

	    command = "iperf3 -c {0} -p 4343 | grep sender | awk '{{print $7}}' &".format(ip)
	    stdin , stdout, stderr = device2_client.exec_command(command)
            print stderr.read()

	    bw = stdout.read()
	    bw = bw.replace(' ','')[:-1]
	    print "\t{0} <-> {1} [{2}Mbps]".format(device1, device2, bw)
	    iperf_i["device1"] = device1
	    iperf_i["device2"] = device2
	    iperf_i["observed_bandwidth_mbps"] = bw
	    iperf_numbers[device1+"_"+device2]= iperf_i

	    gw_client2.close()
	    device2_client.close()

    iperf["bandwidth_numbers"] = iperf_numbers

    #Latency
    print "*****LATENCY*****"
    num_connected_devices = len(devices)
    latency_numbers = {}

    for i in range(0,num_connected_devices):
        device1 = devices[i]
        for j in range(i+1,num_connected_devices):
            k = paramiko.RSAKey.from_private_key_file(gw_key)
    	    gw_client2 = paramiko.SSHClient()
    	    gw_client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	    gw_client2.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
            gw_client2_transport = gw_client2.get_transport()

	    device2 = devices[j]
	    device2_host = deployment_output[device2][network_t][network]
            device2_port = 22
            device2_user = "pi"
	    local_addr = (gw_host, gw_port)
	    dest_addr = (device2_host, device2_port)
	    gw_client2_channel = gw_client2_transport.open_channel("direct-tcpip", dest_addr, local_addr)

            device2_client = paramiko.SSHClient()
            device2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    device2_client.connect(hostname = device2_host, username = device2_user, pkey = k, sock = gw_client2_channel)

	    latency_i = {}
    	    latency_i["device_1"] = device1
    	    latency_i["device_2"] = device2

            ip = deployment_output[device1][network_t][network]

    	    command = "fping -e -c2 -t500 {0} | grep bytes".format(ip)
    	    stdin , stdout, stderr = device2_client.exec_command(command,timeout = 5)

            output = stdout.read()
    	    output = output.split("\n")
    	    if(len(output)>1):
                output = output[1].split(" ")
                if(output[5]):
		    print "{0} -> {1} [{2}ms (rtt)]".format(device1, device2, output[5])
            	    latency_i["observed_latency_ms"]= output[5]
                latency_numbers[device1+"_"+device2] = latency_i
    	    else:
       	        print "ERROR! {0} <-> {1} are either not connected or not in same network".format(device1,device2)
            device2_client.close()

    iperf["latency_numbers"] = latency_numbers

with open("dump/sanity/sanity_{0}".format(network),'w') as file:
    file.write(json.dumps(iperf))

print "{0} - {1}".format(network,datetime.now() - startTime)
