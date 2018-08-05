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
flag = sys.argv[1]
flag = int(flag)

print
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print "               Sanity check                   "
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print


print "**************************** [Sanity] CPU allocation****************************"

if flag == 1:
    print '**********PART-1**********'
    for p in private_networks_dict:
        print "\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@\nNETWORK - {0}\n\n".format(p)
        p_dict = private_networks_dict[p]
        gw = p_dict["gateway"]
        devices = p_dict["devices"]

        pub_network =deployment_output[gw]["public_networks"].keys()
        gw_host = deployment_output[gw]["public_networks"][pub_network[0]]["ip"]
        gw_port = deployment_output[gw]["public_networks"][pub_network[0]]["port"]
        gw_user = "pi"
        gw_key = "/Users/shreyas/pi_key"
        k = paramiko.RSAKey.from_private_key_file(gw_key)
        gw_client = paramiko.SSHClient()
        gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)

        gw_path_cm_exe = "/home/pi/coremark/coremark.exe"
        gw_path_cm_script = "/home/pi/coremark/c_coremark.py"
        gw_key_path = "/home/pi/.ssh/id_rsa"
        pvt_dev_path = "/home/pi"

        print "Starting coremark in gateway"

        commands = [
        "cd /home/pi/coremark && python {0} &".format(gw_path_cm_script)
        ]

        for command in commands:
            stdin , stdout, stderr = gw_client.exec_command(command)
            print stdout.read()
            print stderr.read()

        gw_client.close()

        for d in devices:
            gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
            gw_client_transport = gw_client.get_transport()

            pvt_network = deployment_output[d]["private_networks"].keys()
            pvt_dev_host = deployment_output[d]["private_networks"][pvt_network[0]]
            pvt_dev_port = 22
            pvt_dev_user = "pi"
            local_addr = (gw_host, gw_port)
            dest_addr = (pvt_dev_host, pvt_dev_port)
            gw_client_channel = gw_client_transport.open_channel("direct-tcpip", dest_addr, local_addr)
            pvt_dev_client = paramiko.SSHClient()
            pvt_dev_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            pvt_dev_client.connect(hostname = pvt_dev_host, username = pvt_dev_user, pkey = k, sock = gw_client_channel)

            print "\n\nCopying coremark files to {0}".format(d)

            commands = [
            "scp -i {0} {1} {2}@{3}:{4}".format(gw_key_path, gw_path_cm_exe, pvt_dev_user, pvt_dev_host, pvt_dev_path),
            "scp -i {0} {1} {2}@{3}:{4}".format(gw_key_path, gw_path_cm_script, pvt_dev_user, pvt_dev_host, pvt_dev_path)
            ]

            for command in commands:
                stdin , stdout, stderr = gw_client.exec_command(command)

            time.sleep(1)
            command = "python {0}/c_coremark.py &".format(pvt_dev_path)
            stdin , stdout, stderr = pvt_dev_client.exec_command(command)


if flag == 2:
    print '**********PART-2**********'

    f_pi3b_delta = open("dump/sanity/f_pi3b_delta", "w")
    f_pi3b_p_delta = open("dump/sanity/f_pi3b_p_delta", "w")

    f_pi3b = open("dump/sanity/f_pi3b", "w")
    f_pi3b_p = open("dump/sanity/f_pi3b_p", "w")
    f_cm_all = open("dump/sanity/f_cm_all","w")

    cm_d = {}
    coremark= []


    print "Collecting numbers"


    for p in private_networks_dict:
        print "\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@\nNETWORK - {0}\n\n".format(p)
        p_dict = private_networks_dict[p]
        gw = p_dict["gateway"]
        devices = p_dict["devices"]

        pub_network =deployment_output[gw]["public_networks"].keys()
        gw_host = deployment_output[gw]["public_networks"][pub_network[0]]["ip"]
        gw_port = deployment_output[gw]["public_networks"][pub_network[0]]["port"]
        gw_user = "pi"
        gw_key = "/Users/shreyas/pi_key"
        k = paramiko.RSAKey.from_private_key_file(gw_key)
        gw_client = paramiko.SSHClient()
        gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)

        print "\n\nCollecting numbers in {0}".format(gw)
        command = "cat results-coremark | grep \"CoreMark 1.0\" | awk '{{print $4}}'"
        stdin , stdout, stderr = gw_client.exec_command(command)
        print stderr.read()

        observed_coremark = stdout.read()
        observed_coremark = observed_coremark.split("\n")
        observed_coremark.pop()
        for i in observed_coremark:
            coremark.append(float(i))
        coremark.sort()

        c_median = median(coremark)
        if len(coremark) != 0:
            c_avg = float(sum(coremark)) /float(len(coremark))
        else:
            c_avg = 0
            print "len(coremark) = 0"

        d_type = infra_config["devices"][gw]["device_type"]
        expected_coremark = device_types[d_type]["coremark"]
        cm_d["device_type"] = d_type
        coremark_str = []
        for c_str in coremark:
            coremark_str.append(str(c_str))

        cm_d["coremark"] = coremark_str
        cm_d["n"] = len(coremark_str)
        cm_d["mean"] = str(c_avg)
        cm_d["median"] = str(c_median)

        coremark_devices_all[gw] = cm_d
        for cm in coremark:
            f_cm_all.write(gw+"\t"+d_type+"\t"+str(cm)+"\n")


        print "\ndevice - {0} \n  device_type = {1} \n  expected coremark = {2} observed coremark = {3}\n\n".format(gw, d_type, expected_coremark, c_avg)

        delta = (float(c_avg) - float(expected_coremark)) / float(expected_coremark) * 100
        print delta

        if d_type == "Pi3B":
            f_pi3b_delta.write(str(delta)+"\n")
            f_pi3b.write(str(c_avg)+","+str(c_median)+"\n")
        elif d_type == "Pi3B+":
            f_pi3b_p_delta.write(str(delta)+"\n")
            f_pi3b_p.write(str(c_avg)+","+str(c_median)+"\n")

        gw_client.close()

        for d in devices:
            k = paramiko.RSAKey.from_private_key_file(gw_key)
            gw_client = paramiko.SSHClient()
            gw_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            gw_client.connect(hostname = gw_host, port = gw_port, username = gw_user, pkey = k)
            gw_client_transport = gw_client.get_transport()

            pvt_network = deployment_output[d]["private_networks"].keys()
            pvt_dev_host = deployment_output[d]["private_networks"][pvt_network[0]]
            pvt_dev_port = 22
            pvt_dev_user = "pi"
            local_addr = (gw_host, gw_port)
            dest_addr = (pvt_dev_host, pvt_dev_port)
            gw_client_channel = gw_client_transport.open_channel("direct-tcpip", dest_addr, local_addr)
            pvt_dev_client = paramiko.SSHClient()
            pvt_dev_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            pvt_dev_client.connect(hostname = pvt_dev_host, username = pvt_dev_user, pkey = k, sock = gw_client_channel)


            print "\n\nCollecting numbers in {0}".format(d)
            command = "cat results-coremark | grep \"CoreMark 1.0\" | awk '{{print $4}}'"
            stdin , stdout, stderr = pvt_dev_client.exec_command(command)
            print stderr.read()

            observed_coremark = stdout.read()
            observed_coremark = observed_coremark.split("\n")
            observed_coremark.pop()
            for i in observed_coremark:
                coremark.append(float(i))
            coremark.sort()

            c_median = median(coremark)
            if len(coremark) != 0:
                c_avg = float(sum(coremark)) /float(len(coremark))
            else:
                c_avg = 0
                print "len(coremark) = 0"

            d_type = infra_config["devices"][d]["device_type"]
            expected_coremark = device_types[d_type]["coremark"]
            cm_d["device_type"] = d_type
            coremark_str = []
            for c_str in coremark:
                coremark_str.append(str(c_str))

            cm_d["coremark"] = coremark_str
            cm_d["n"] = len(coremark_str)
            cm_d["mean"] = str(c_avg)
            cm_d["median"] = str(c_median)

            coremark_devices_all[d] = cm_d
            for cm in coremark:
                f_cm_all.write(d+"\t"+d_type+"\t"+str(cm)+"\n")


            print "\ndevice - {0} \n  device_type = {1} \n  expected coremark = {2} observed coremark = {3}\n\n".format(d, d_type, expected_coremark, c_avg)

            delta = (float(c_avg) - float(expected_coremark)) / float(expected_coremark) * 100
            print delta

            if d_type == "Pi3B":
                f_pi3b_delta.write(str(delta)+"\n")
                f_pi3b.write(str(c_avg)+","+str(c_median)+"\n")
            elif d_type == "Pi3B+":
                f_pi3b_p_delta.write(str(delta)+"\n")
                f_pi3b_p.write(str(c_avg)+","+str(c_median)+"\n")

            pvt_dev_client.close()


    f_pi3b.close()
    f_pi3b_delta.close()
    f_pi3b_p.close()
    f_pi3b_p_delta.close()

    f_cm_all.close()

    with open('dump/sanity/cm_device_all','w') as file:
        file.write(json.dumps(coremark_devices_all))
