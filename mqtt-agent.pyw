import paho.mqtt.client as mqtt
import yaml
import os
import psutil
import socket
import re
import time
import subprocess 
import sys
import uptime
import json
import datetime
from PIL import Image
import pystray
from pystray import Menu, MenuItem

#TBD - Set Computer as Entity
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
    print("Connected to: " + mqttServer + " - Result code: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    # MQTT Auto Discovery for Home Assistant sensors
    configMsgProcess =  {
        "name": settings.get("name") + " processor used", 
        "unique_id": settings.get("name")+"_processor_used", 
        "state_topic": "homeassistant/sensor/"+settings.get("name")+"/state", 
        "unit_of_measurement": "%", 
        "icon": "mdi:cpu-64-bit",
        "value_template": "{{ value_json.process}}"
        }
    client.publish("homeassistant/sensor/"+settings.get("name")+"/config", payload=json.dumps(configMsgProcess), qos=0, retain=True)
    configMsgUptime =  {
        "name": settings.get("name") + " uptime",
        "unique_id": settings.get("name")+"_uptime",
        "state_topic": "homeassistant/sensor/"+settings.get("name")+"/state",
        "unit_of_measurement": "",
        "icon": "mdi:timer",
        "value_template": "{{ value_json.uptime}}"
        }
    client.publish("homeassistant/sensor/"+settings.get("name")+"U/config", payload=json.dumps(configMsgUptime), qos=0, retain=True)
    configMsgMemUsed =  {
        "name": settings.get("name") + " memory used",
        "unique_id": settings.get("name")+"_mem_used",
        "state_topic": "homeassistant/sensor/"+settings.get("name")+"/state",
        "unit_of_measurement": "%",
        "icon": "mdi:memory",
        "value_template": "{{ value_json.memUsed}}"
        }
    client.publish("homeassistant/sensor/"+settings.get("name")+"MU/config", payload=json.dumps(configMsgMemUsed), qos=0, retain=True)
    
    # MQTT Auto Discovery for Home Assistant switches   
    for key, value in apps.items():
        uniqueID = settings.get("name")+ "_" + str(value.get("name")).replace(" ","_")
        topicAppName = str(value.get("name")).replace(" ","")
        configSwitch = {
            "name": settings.get("name") + " " + value.get("name"),
            "unique_id":  uniqueID,
            "command_topic": "homeassistant/switch/" + settings.get("name") + "/" + topicAppName + "/set",
            "state_topic": "homeassistant/switch/" + settings.get("name") + "/" + topicAppName + "/state",
            "icon":   value.get("md-icon")
            }
        client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/config", payload=json.dumps(configSwitch), qos=0, retain=True)
        client.subscribe(configSwitch.get("command_topic"))
        if settings.get("debug") == True :
            print("Topic suscribed on: " + configSwitch.get("command_topic"))
    process_update_status(client)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    msg.payload = (msg.payload).decode("utf-8")
    if settings.get("debug") == True :
        print(msg.topic + " recieved a message: " + msg.payload)
    for key, value in apps.items():
        # Start an application
        topicAppName = str(value.get("name")).replace(" ","")
        topic = str("homeassistant/switch/" + settings.get("name") + "/" + topicAppName + "/set")
        if msg.topic == topic and msg.payload == "ON":
            if process_running(value.get("process")) == False:
                # Exec command
                command = str(value.get('path')).replace('%APPDATA%', os.getenv('APPDATA'))+value.get('process')
                if settings.get("debug") == True :
                    print(command)                
                subprocess.Popen(command)
                os._exit
                client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/state", payload="ON", qos=0, retain=True)
            else:
                if settings.get("debug") == True :
                    print(value.get('process') + " is already running on " + settings.get("name"))
                client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/state", payload="ON", qos=0, retain=True)
        # Stop an application
        if msg.topic == topic and msg.payload == "OFF":
            # Check if the process to be excecuted is already started
            if process_running(value.get("process")):
                if settings.get("debug") == True :
                    print(proc.info.get("name"))            
                os.system('taskkill /F /im "' +  value.get("process") + '" /T')
                client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/state", payload="OFF", qos=0, retain=True)
                break

def process_running(process):
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        if proc.info.get("name") ==  process:
            return True
    return False

def process_update_status(client):
    for key, value in apps.items():
        topicAppName = str(value.get("name")).replace(" ","")
        if process_running(value.get("process")):
            client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/state", payload="ON", qos=0, retain=True)
        else:
            client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/state", payload="OFF", qos=0, retain=True)

def exit_action(icon):
    icon.visible = False
    try:
        sys.exit(0)
    except SystemExit:
        print("Program terminated with SystemExit exception")
    finally:
        print("Cleanup")
    icon.stop()

def init_icon():
    icon = pystray.Icon('PyWinIoT')
    icon.menu = Menu(
        MenuItem('Exit', lambda : exit_action(icon)),
    )
    icon.icon = Image.open("pywiniot.png")
    icon.title = "PyWinIoT Agent"
    icon.run(setup)

def setup(icon):
    icon.visible = True
    noIpAddress = True
    ip_segment = settings.get("network")
    index = ip_segment.rfind(".")
    pattern = (ip_segment[0:index-1]+"\d").replace(".","\.")
    while noIpAddress:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        if re.match(pattern, ip_address):
            noIpAddress = False
            break
        else:
            time.sleep(5)
    client = mqtt.Client(client_id=settings.get("name"))
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqttUser,mqttUser)
    client.connect(mqttServer, mqttPort, 60)
    client.loop_start()
    while icon.visible:
        time.sleep(3) 
        # MQTT JSON Message
        cpuPer = str(psutil.cpu_percent(interval=None))
        uptimeReal = datetime.timedelta(seconds=uptime.uptime())
        memUsed = psutil.virtual_memory()[2]
        infoMsg = { 
            "process": cpuPer,
            "uptime": str(uptimeReal).split(".")[0].replace(",",""),
            "memUsed": memUsed
            }
        #Publish sensor state
        client.publish("homeassistant/sensor/"+settings.get("name")+"/state", payload=json.dumps(infoMsg), qos=0, retain=True)
        if settings.get("debug") == True :
            print("publish sent to homeassistant/" + settings.get("name")+"/state: " + str(infoMsg))
        process_update_status(client)
        time.sleep(settings.get("sensor_time"))

init_icon()