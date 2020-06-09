import paho.mqtt.client as mqtt
import yaml
import os
import psutil

# Import configuration for config.yaml
config_path = "config.yaml"
config_file = open(config_path)
config = yaml.load(config_file, Loader=yaml.FullLoader)

# Set MQTT parameters
mqttServer = config.get("mqtt_server").get("server")
mqttPort = config.get("mqtt_server").get("port")
mqttUser = config.get("mqtt_server").get("userName")
mqttPwd = config.get("mqtt_server").get("password")

# Get all declared items in config.yaml
for key, value in config.items():
    print(key + " " + str(value))

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected to " + mqttServer + " result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    client.subscribe("agent/plex/status")

# The callback for when a PUBLISH message is received from the server.str(msg.payload)


def on_message(client, userdata, msg):
    if msg.topic == "agent/plex/status":
        existsFlag = 0
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            if proc.info.get("name") ==  "Calculator.exe":
                existsFlag = 1
                break
        if existsFlag == 1:
            print("status: on")
        else:
            print("status: off")
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(mqttUser,mqttUser)
client.connect(mqttServer, mqttPort, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
