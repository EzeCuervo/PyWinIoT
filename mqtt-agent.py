import paho.mqtt.client as mqtt
import yaml
import os
import psutil
import time
import subprocess 
import sys
import uptime

#TBD - Monitor config file changes and refresh values

# Import configuration for config.yaml
config_path = "config.yaml"
config_file = open(config_path)
config = yaml.load(config_file, Loader=yaml.FullLoader)

mqtt_server = []
apps = []
settings = []

# Get all settings from config.yaml
for key, value in config.items():
    if key == "settings":
        settings = value
    if key == "mqtt_server":
        mqtt_server = value
    if key == "apps":
        apps = value

# Set MQTT parameters
mqttServer = mqtt_server.get("server")
mqttPort = mqtt_server.get("port")
mqttUser = mqtt_server.get("userName")
mqttPwd = mqtt_server.get("password")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected to " + mqttServer + " result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    for key, value in apps.items():
        client.subscribe(settings.get("name")+"/agent/"+value.get("name")+"/start")
        if settings.get("debug") == True :
            print("Topic suscribed on: " + settings.get("name")+"/agent/"+value.get("name")+"/start")
    
# The callback for when a PUBLISH message is received from the server.str(msg.payload)
def on_message(client, userdata, msg):
    if settings.get("debug") == True :
        print(msg.topic + " recieved a package.")
    for key, value in apps.items():
        if msg.topic == str(settings.get("name")+"/agent/"+value.get("name")+"/start"):
            # Check if the process to be excecuted is already started
            psRunning = False
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                if proc.info.get("name") ==  value.get("process"):
                    psRunning = True
                    break
            if psRunning == False:
                # Exec command
                command = str(value.get('path')).replace('%APPDATA%', os.getenv('APPDATA'))+value.get('process')
                if settings.get("debug") == True :
                    print(command)                
                subprocess.Popen([command, ""])
                os._exit
            else:
                if settings.get("debug") == True :
                    print(value.get('process') + " is already running on " + settings.get("name"))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(mqttUser,mqttUser)
client.connect(mqttServer, mqttPort, 60)
client.loop_start()

while True:
    time.sleep(1)
    # Send percentage stats
    cpuPer = str(psutil.cpu_percent(interval=None))
    client.publish(settings.get("name")+"/agent/info/process", payload=cpuPer, qos=0, retain=False)
    if settings.get("debug") == True :
        print("publish sent to " + settings.get("name")+"/agent/process: " + cpuPer)
    uptimeReal = str(uptime.uptime())
    client.publish(settings.get("name")+"/agent/info/uptime", payload=uptimeReal, qos=0, retain=False)
    if settings.get("debug") == True :
        print("publish sent to " + settings.get("name")+"/agent/uptime: " + str(uptimeReal))
    time.sleep(5)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.