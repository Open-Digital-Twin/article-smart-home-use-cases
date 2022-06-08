"""
Input: the path of the CSV file that contains the simulation data.
Example input: dataset.csv

Operation: publishes the input to three MQTT topics.
The association column-topic is defined by the room_names dic in the main function

"""
from paho.mqtt import client as mqtt_client
import sys
import pandas as pd
import time

def get_file_name():
    if len(sys.argv) < 2:
        print("filename missinig")
        return None
    return sys.argv[1]
  
global client_connected
def connect_mqtt():
    global client_connected
    client_connected = -1
    def on_connect(client, userdata, flags, rc):
        global client_connected
        if rc == 0:
            client_connected = 1
            print("Connected to MQTT Broker!")
        else:
            client_connected = 0
            print("Failed to connect, return code %d\n", rc)
    
    # Set Connecting Client ID
    broker = 'broker.emqx.io'
    port = 1883
    client_id = 'house'
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    
    while client_connected == -1:
        time.sleep(1)
    if client_connected == 1:
        return client
    else:
        return None
    
def publish(msg, topic, client):
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

def generate_events_on_topic(topic_name, df, client):

    for index, row in df.iterrows():
        timestamp = row[0]
        temperature = row[1]
       
        msg = "{"+ f'"measured_time": {timestamp}, "temperature": {temperature}' + "}"
        publish(msg, topic_name, client)
        print("msg sent: ", msg)
        time.sleep(0.1)

def main():
    
    #File reading setup
    filename = get_file_name()
    if not filename:
        return
    df = pd.read_csv(filename,low_memory=False, usecols=[0,2,3,4])
    room_names = {'smallroomwindow':'T2', 'bigroom': 'T3', 'smallroom': 'T4'}

    #MQTT broker setup
    client = connect_mqtt()
  
    #File reading and publishing
    for room_name in room_names.keys():
        print("publishing room name = ", room_name, "thermometer name = ", room_names[room_name])
        sub_df = df[["time", room_names[room_name]]]
        generate_events_on_topic(room_name, sub_df, client)
main()
