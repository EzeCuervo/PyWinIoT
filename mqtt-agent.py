import paho.mqtt.client as mqtt
import yaml
import os
import psutil
import time
import subprocess 
import sys
import uptime
import json
import datetime

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
    client.publish("homeassistant/sensor/"+settings.get("name")+"/config", payload=json.dumps(configMsgProcess), qos=0, retain=False)
    configMsgUptime =  {
        "name": settings.get("name") + " uptime",
        "unique_id": settings.get("name")+"_uptime",
        "state_topic": "homeassistant/sensor/"+settings.get("name")+"/state",
        "unit_of_measurement": "",
        "icon": "mdi:timer",
        "value_template": "{{ value_json.uptime}}"
        }
    client.publish("homeassistant/sensor/"+settings.get("name")+"U/config", payload=json.dumps(configMsgUptime), qos=0, retain=False)
    
    # MQTT Auto Discovery for Home Assistant switches   
    for key, value in apps.items():
        uniqueID = str(value.get("name")).replace(" ","_")
        topicAppName = str(value.get("name")).replace(" ","")
        configSwitch = {
            "name": settings.get("name") + " " + value.get("name"),
            "unique_id": settings.get("name")+"_" + uniqueID,
            "command_topic": "homeassistant/switch/" + settings.get("name") + "/" + topicAppName + "/set",
            "state_topic": "homeassistant/switch/" + settings.get("name") + "/" + topicAppName + "/state",
            "icon":   value.get("md-icon")
            }
        client.publish("homeassistant/switch/"+ settings.get("name") + "/" + topicAppName + "/config", payload=json.dumps(configSwitch), qos=0, retain=False)
        client.subscribe(configSwitch.get("command_topic"))
        if settings.get("debug") == True :
            print("Topic suscribed on: " + configSwitch.get("command_topic"))
    
# The callback for when a PUBLISH message is received from the server.str(msg.payload)
def on_message(client, userdata, msg):
    msg.payload = (msg.payload).decode("utf-8")
    if settings.get("debug") == True :
        print(msg.topic + " recieved a message: " + msg.payload)
    for key, value in apps.items():
        # Start an application
        topic = str("homeassistant/switch/" + settings.get("name") + "/" + value.get("name") + "/set")
        if msg.topic == topic and msg.payload == "ON":
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
                subprocess.Popen(command)
                os._exit
                client.publish("homeassistant/switch/"+ settings.get("name") + "/" + value.get("name") + "/state", payload="ON", qos=0, retain=False)
            else:
                if settings.get("debug") == True :
                    print(value.get('process') + " is already running on " + settings.get("name"))
                client.publish("homeassistant/switch/"+ settings.get("name") + "/" + value.get("name") + "/state", payload="ON", qos=0, retain=False)
        # Stop an application
        if msg.topic == topic and msg.payload == "OFF":
            # Check if the process to be excecuted is already started
            psRunning = False
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                if proc.info.get("name") ==  value.get("process"):
                    if settings.get("debug") == True :
                        print(proc.info.get("name"))            
                    os.system('taskkill /F /im "' +  value.get("process") + '" /T')
                    client.publish("homeassistant/switch/"+ settings.get("name") + "/" + value.get("name") + "/state", payload="OFF", qos=0, retain=False)
                    break

client = mqtt.Client(client_id=settings.get("name"))
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(mqttUser,mqttUser)
client.connect(mqttServer, mqttPort, 60)
client.loop_start()

while True:
    time.sleep(3) 
    # MQTT JSON Message
    cpuPer = str(psutil.cpu_percent(interval=None))
    uptimeReal = datetime.timedelta(seconds=uptime.uptime())
    infoMsg = { 
        "process": cpuPer,
        "uptime": str(uptimeReal).split(".")[0].replace(",","")
        }
    #Publish sensor state
    client.publish("homeassistant/sensor/"+settings.get("name")+"/state", payload=json.dumps(infoMsg), qos=0, retain=False)
    if settings.get("debug") == True :
        print("publish sent to homeassistant/" + settings.get("name")+"/state: " + str(infoMsg))

    time.sleep(settings.get("sensor_time"))