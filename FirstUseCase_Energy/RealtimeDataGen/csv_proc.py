import pandas as pd
from paho.mqtt import client as mqtt_client
import time
import json

broker = 'broker.emqx.io'
port = 1883
client_id = 'house'
# username = 'emqx'
# password = 'public'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    #client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(msg, topic):
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

client = connect_mqtt()
client.loop_start()

df = pd.read_csv('HomeC.csv', low_memory=False)
df.head()
df.columns = [col.replace(' [kW]', '') for col in df.columns]
df['Furnace'] = df[['Furnace 1','Furnace 2']].mean(axis=1)
equipments_cols = ['Microwave', 'Dishwasher', 'Fridge', 'Furnace']
df = df.reset_index() 
for index, row in df.iterrows():
    for equipment in equipments_cols:
        if row[equipment]:
            #json_data = {"index": index, "equipment": equipment, "power": row[equipment]}
            #row[equipment]
            measured_time = time.time()
            publish('{"equipment": ' + f'"{equipment}", "power": {row[equipment]}, ' + '"measured_time": ' + f'{measured_time}' + '}', "equipment")
            #publish('{"name": "laura","power": 90.87}', "equipments") #JSON KEYS AND STRING VALUES MUST HAVE DOUBLE QUOTES
    time.sleep(1) #seconds
