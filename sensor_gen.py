import os
#import paramiko
import random
import time
import json
from datetime import datetime
from threading import Thread



startTime = datetime.now()

infra_config = json.load(open("config/infra_config.json"))
#vm_config = json.load(open("config/vm_config.json"))
sensor_types =  json.load(open("config/sensor_types.json"))
deployment =  json.load(open("config/deployment.json"))
deployment_output = json.load(open("dump/infra/deployment_output.json"))
network_ip = json.load(open("config/network_ip.json"))
fog_ip = json.load(open("config/fog_ip.json"))
private_networks = infra_config["private_networks"]
public_networks = infra_config["public_networks"]
#all_devices_list = deployment_output.keys()
#print all_devices_list
#container_vm = vm_config["container_VM"]
#container_vm_names = container_vm.keys()

sensor_duration_secs = deployment["sensor_duration_secs"]

path = "violet"
sensor_path = path + "/sensors"
sensor_bin_path = sensor_path + "/bin"
sensor_data_path = sensor_path + "/data"

log_file = open("sensor_gen_log","w")

log_file.write("\n\n\n*****************************************Creating Sensors*******************************\n\n\n")

print
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print "             Copy data to other VMs            "
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print
log_file.write("\n\n\n***********************Copy data to other VMs*********************************\n\n\n")

sensors_data_gen = "sensors_data_gen"

devices = deployment_output.keys()

print
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print "           Create sensors                      "
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print

log_file.write("\n\n\n****************************Create Sensors*******************************************\n\n\n")

sensor_types_list = sensor_types["sensor_types"]

sensor_types_dict = {}

for sensor in sensor_types_list:
    sensor_id = str(sensor["id"])
    timestamp = str(sensor["timestamp"])
    dist_rate = str(sensor["dist_rate"])
    dist_value = str(sensor["dist_value"])

    if str(sensor["dist_rate"]) == "normal" :
        mean = float(sensor["rate_params"]["mean"])
        variance = float(sensor["rate_params"]["variance"])
        min_value = float(sensor["rate_params"]["min_value"])
        unit = sensor["rate_params"]["unit"]
        rate_params = str(mean) + "," + str(variance) + "," + str(min_value) + "," +unit
	if mean < variance or mean <= 0 or min_value <= 0:
		log_file.write("\nNormal dist_rate\nIncorrect initialization of distribute rate for sensor")
		print "Incorrect initialization of distribute rate for sensor"
    if str(sensor["dist_rate"]) == "uniform" :
        lower_limit = float(sensor["rate_params"]["lower_limit"])
        upper_limit = float(sensor["rate_params"]["upper_limit"])
        unit = sensor["rate_params"]["unit"]
        rate_params = str(lower_limit) + "," + str(upper_limit) + "," + unit
	if lower_limit <=0 or lower_limit >= upper_limit:
		log_file.write("\nUniform dist_rate\nIncorrect initialization of distribute rate for sensor")
		print "Incorrect initialization of distribute rate for sensor"

    if str(sensor["dist_rate"]) == "poisson" :
        lmbda = float(sensor["rate_params"]["lambda"])
        min_value = float(sensor["rate_params"]["min_value"])
        unit = sensor["rate_params"]["unit"]
        rate_params = str(lmbda) + "," + str(min_value) + "," + unit
	if lmbda <= 0 or min_value <= 0:
		log_file.write("\nPoisson dist_rate\nIncorrect initialization of distribute rate for sensor")
		print "Incorrect initialization of distribute rate for sensor"

    if str(sensor["dist_rate"]) == "user_defined" :
        path = sensor["rate_params"]["path"]
        path = path.split("/")[-1]
        unit = sensor["rate_params"]["unit"]
        rate_params = path + "," + unit

    if str(sensor["dist_value"]) == "normal" :
        mean = sensor["value_params"]["mean"]
        variance = sensor["value_params"]["variance"]
        min_value = sensor["value_params"]["min_value"]
        value_params = mean + "," + variance + "," + min_value

    if str(sensor["dist_value"]) == "uniform" :
        lower_limit = sensor["value_params"]["lower_limit"]
        upper_limit = sensor["value_params"]["upper_limit"]
        value_params = lower_limit + "," + upper_limit

    if str(sensor["dist_value"]) == "poisson" :
        lmbda = sensor["value_params"]["lambda"]
        min_value = sensor["value_params"]["min_value"]
        value_params = lmbda + "," + min_value

    if str(sensor["dist_value"]) == "user_defined" :
        path = sensor["value_params"]["path"]
        path = path.split("/")[-1]
        #min_value = sensor["value_params"]["min_value"]
        value_params = path + "," + min_value

    params = [sensor_id, timestamp, sensor_duration_secs, dist_rate, rate_params, dist_value, value_params]
    sensor_type = str(sensor["type"])
    sensor_types_dict[sensor_type] = params



for p in public_networks:
    devices = public_networks[p]["devices"]
    latency = public_networks[p]["latency_ms"]
    for f in devices:
        print "Copying required binary and data files for device - {0}".format(f)
        device_ip = fog_ip["public"][f]["ip"]
        device_port = fog_ip["public"][f]["port"]
        #print device_ip

        try:
            port = infra_config["devices"][f]["port"]
        except KeyError, e:
            print "setting port to default 5000"
            port = 5000

        
        commands = [
                "sshpass -p 'raspberry' ssh -p {0} pi@{1} 'mkdir -p {2}'".format(device_port,device_ip,sensor_bin_path),
                "sshpass -p 'raspberry' ssh -p {0} pi@{1} 'mkdir -p {2}'".format(device_port,device_ip,sensor_data_path),
                "sshpass -p 'raspberry' scp -P {3} -r {0}/bin pi@{1}:{2}".format(sensors_data_gen,device_ip,sensor_path,device_port),
                "sshpass -p 'raspberry' scp -P {3} -r {0}/data pi@{1}:{2}".format(sensors_data_gen,device_ip,sensor_path,device_port)
        ]

        for command in commands:
            print command
            os.system(command)

        

    	sensors = infra_config["devices"][f]["sensors"]
    	sensor_dict_list = []

    	print "Creating sensor for device - {0}".format(f)
    	for sensor in sensors:
    	    sensor_dict = {}
    	    sensor_type = sensor["sensor_type"]
    	    num_sensors = sensor["count"]
    	    link_list = []
	
            while num_sensors:
                sensor_file_name = sensor_type + "_" + str(num_sensors)
            	link = "http://"+device_ip+":"+str(port)+"/sensors/"+sensor_file_name
                #print link
            	link_list.append(link)
            	params = sensor_types_dict[sensor_type]
            	command = "sshpass -p 'raspberry' ssh -p {10} pi@{8} python {9}/data_gen.py {0} {1} {2} {3} {4} {5} {6} {7}".format(sensor_file_name,params[0],params[1],params[2],params[3],params[4],params[5],params[6],device_ip,sensor_bin_path,device_port)
                print command
            	os.system(command)
            	num_sensors -= 1

            sensor_dict = {
            	"sensor_type":sensor["sensor_type"],
            	"links":link_list
            	}
            sensor_dict_list.append(sensor_dict)

    	commands = [
                #"sshpass -p 'raspberry' ssh pi@{0} sudo tc qdisc del dev eth0 root netem".format(device_ip),
                "sshpass -p 'raspberry' ssh -p {1} pi@{0} sudo tc qdisc del dev wlan0 root netem".format(device_ip,device_port),
                #"sshpass -p 'raspberry' ssh pi@{0} sudo tc qdisc add dev eth0 root netem delay {1}ms".format(device_ip,latency),
                "sshpass -p 'raspberry' ssh -p {2} pi@{0} sudo tc qdisc add dev wlan0 root netem delay {1}ms".format(device_ip,latency,device_port),
                "sshpass -p 'raspberry' ssh -p {4} pi@{0} '/home/pi/.local/bin/gunicorn --chdir {1} -D -w 4 --bind {2}:{3} wsgi'".format(device_ip,sensor_bin_path,device_ip,port,device_port)
                ]
    	#log_file.write(command+"\n")
        for command in commands:    
            print command
    	    os.system(command)
        #stdin,stdout,stderr = c.exec_command(command)
    	#log_file.write(stdout.read()+"\n")
    	#log_file.write(stderr.read()+"\n")

    	deployment_output[f]["sensors"] = sensor_dict_list


for p in private_networks:
    devices = private_networks[p]["devices"]
    latency = private_networks[p]["latency_ms"]
    gw = private_networks[p]["gateway"]
    pub_gw_ip = fog_ip["public"][gw]["ip"]
    gw_port = fog_ip["public"][gw]["port"]
    pvt_gw_ip = fog_ip["private"][gw]
    print gw,pub_gw_ip
    
    commands = [
        "sshpass -p 'raspberry' ssh -p {1} pi@{0} sudo tc qdisc del dev eth0 root netem".format(pub_gw_ip,gw_port),
        "sshpass -p 'raspberry' ssh -p {2} pi@{0} sudo tc qdisc add dev eth0 root netem delay {1}ms".format(pub_gw_ip,latency,gw_port)
        ]

    for command in commands:
        print command
        os.system(command)



    for d in devices:
        print "Copying required binary and data files for device - {0}".format(d)
        nw_name_list = deployment_output[d]["private_networks"].keys()
        device_ip = deployment_output[d]["private_networks"][nw_name_list[0]]
        #print d,device_ip
        try:
            port = infra_config["devices"][d]["port"]
        except KeyError, e:
            print "setting port to default 5000"
            port = 5000

        
        commands = [
                "sshpass -p 'raspberry' ssh -p {3} pi@{0} sshpass -p 'raspberry' ssh pi@{1} 'mkdir -p {2}'".format(pub_gw_ip,device_ip,sensor_bin_path,gw_port),
                "sshpass -p 'raspberry' ssh -p {3} pi@{0} sshpass -p 'raspberry' ssh pi@{1} 'mkdir -p {2}'".format(pub_gw_ip,device_ip,sensor_data_path,gw_port),
                "sshpass -p 'raspberry' ssh -p {4} pi@{0} sshpass -p 'raspberry' scp -r {1}/bin pi@{2}:{3}".format(pub_gw_ip,sensors_data_gen,device_ip,sensor_path,gw_port),
                "sshpass -p 'raspberry' ssh -p {4} pi@{0} sshpass -p 'raspberry' scp -r {1}/data pi@{2}:{3}".format(pub_gw_ip,sensors_data_gen,device_ip,sensor_path,gw_port)
        ]
        
        for command in commands:
            print command
            os.system(command)

        

    	sensors = infra_config["devices"][d]["sensors"]
    	sensor_dict_list = []

    	print "Creating sensor for device - {0}".format(d)
    	for sensor in sensors:
    	    sensor_dict = {}
    	    sensor_type = sensor["sensor_type"]
    	    num_sensors = sensor["count"]
    	    link_list = []
	
            while num_sensors:
                sensor_file_name = sensor_type + "_" + str(num_sensors)
            	link = "http://"+device_ip+":"+str(port)+"/sensors/"+sensor_file_name
                #print link
            	link_list.append(link)
            	params = sensor_types_dict[sensor_type]
            	command = "sshpass -p 'raspberry' ssh -p {11} pi@{10} sshpass -p 'raspberry' ssh pi@{8} python {9}/data_gen.py {0} {1} {2} {3} {4} {5} {6} {7}".format(sensor_file_name,params[0],params[1],params[2],params[3],params[4],params[5],params[6],device_ip,sensor_bin_path,pub_gw_ip,gw_port)
                print command
            	os.system(command)
            	num_sensors -= 1

            sensor_dict = {
            	"sensor_type":sensor["sensor_type"],
            	"links":link_list
            	}
            sensor_dict_list.append(sensor_dict)

    	commands = [
                #"sshpass -p 'raspberry' ssh pi@{0} sshpass -p 'raspberry' ssh pi@{1} sudo ufw allow {2}".format(gw_ip,device_ip,port),
                "sshpass -p 'raspberry' ssh -p {2} pi@{0} sshpass -p 'raspberry' ssh pi@{1} sudo tc qdisc del dev eth0 root netem".format(pub_gw_ip,device_ip,gw_port),
                "sshpass -p 'raspberry' ssh -p {2} pi@{0} sshpass -p 'raspberry' ssh pi@{1} sudo tc qdisc del dev wlan0 root netem".format(pub_gw_ip,device_ip,gw_port),
                "sshpass -p 'raspberry' ssh -p {3} pi@{0} sshpass -p 'raspberry' ssh pi@{1} sudo tc qdisc add dev eth0 root netem delay {2}ms".format(pub_gw_ip,device_ip,latency,gw_port),
                "sshpass -p 'raspberry' ssh -p {3} pi@{0} sshpass -p 'raspberry' ssh pi@{1} sudo tc qdisc add dev wlan0 root netem delay {2}ms".format(pub_gw_ip,device_ip,latency,gw_port),
                "sshpass -p 'raspberry' ssh -p {5} pi@{0} sshpass -p 'raspberry' ssh pi@{1} '/home/pi/.local/bin/gunicorn -D --chdir {2} -w 4 --bind {3}:{4} wsgi'".format(pub_gw_ip,device_ip,sensor_bin_path,device_ip,port,gw_port)
                ]
    	#log_file.write(command+"\n")
        for command in commands:    
            print command
    	    os.system(command)
        #stdin,stdout,stderr = c.exec_command(command)
    	#log_file.write(stdout.read()+"\n")
    	#log_file.write(stderr.read()+"\n")

    	deployment_output[d]["sensors"] = sensor_dict_list





print "\n\nDeployment Ouput with sensor creation\n\n"
print deployment_output

log_file.close()


with open('dump/infra/deployment_output.json','w') as file:
    file.write(json.dumps(deployment_output))

print datetime.now() - startTime

