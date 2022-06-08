"""
Inupt: 
1 - a number of month (1 for January, 2 for February and so on)
2 - a stream name (can be any name. It is used for naming the output file)

Output: A heater routine file. Examples can be seen on the "HaterRoutineFiles" folder

Operation: It publishes the temperature measurements in the stutt.csv file in the MQTT topic named temperature.
It generates 3 intermidiate values between 2 rows, so we simulate temperature measurements 15 by 15 minutes
It also subscribes the heater-actions MQTT topic.

"""

import json
import pandas as pd
import os
from datetime import datetime
import sys
from paho.mqtt import client as mqtt_client
from time import sleep

topic_to_publish = "temperature"
topic_to_subscribe = "heater-actions"
time_step = 15 #min
stop_producer = False
stop_consumer = False
client_connected = False
client = None
file_to_append = None

user_leaving_time = datetime.strptime("12:00", "%H:%M")
user_arriving_time = datetime.strptime("18:00", "%H:%M")

def get_month_input():
    if len(sys.argv) < 2:
        print("input missinig")
        return None
    return sys.argv[1]
    
def get_stream_name_input():
    if len(sys.argv) < 3:
        print("stream name missinig")
        return None
    return sys.argv[2]
     
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
    client.on_message = on_message
    client.connect(broker, port)
    client.loop_start()
    
    while client_connected == -1:
        sleep(1)
    if client_connected == 1:
        return client
    else:
        return None

def publish(msg, topic):
    global client
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

def generate_temperature_event(temperature, hour, minute, day, month):
    json_msg = {
        "temperature": round(temperature, 2),
        "measured_time": f"{int(hour)}:{int(minute)}",
        "date": f"{int(day)}/{int(month)}"
    }
    json_string = json.dumps(json_msg)
    publish(json_string.encode(), topic_to_publish)

def parse_day(day_dataframe):

    global stop_producer
    #global stop_consumer

    inter_steps = int(60 / time_step) #amount
    day = day_dataframe.iloc[1]["day"]
    month = day_dataframe.iloc[1]["month"]

    for index, row in day_dataframe.iloc[:-1, :].iterrows():
        current_hour = row['hour']
        current_hour_datetime = datetime.strptime(f"{int(current_hour)}:00", "%H:00")
        if current_hour_datetime < user_leaving_time or current_hour_datetime > user_arriving_time:
            continue

        next_row = day_dataframe.loc[index + 1]
        temp_diff = next_row['temperature'] - row['temperature']
        inter_increment = temp_diff / inter_steps
        
        previous_temp = row['temperature']
        previous_min = 0

        for _ in range(0, inter_steps):
            if stop_producer:
                return
            generate_temperature_event(previous_temp, current_hour, previous_min, day, month)
            
            previous_temp += inter_increment
            previous_min += time_step
            sleep(2)
        
    last_row = day_dataframe.iloc[-1]
    generate_temperature_event(last_row['temperature'], last_row['hour'], 0, day, month)
    #stop_consumer = True
    print("day ending")

def parse_month(month_dataframe, days_on_month):

    global stop_producer

    for day in range(0, days_on_month):

        print('----------------------')
        print(f"DAY {day}")
        print('----------------------')

        day_initial_row = day * 24
        day_final_row = day_initial_row + 24

        day_dataframe = month_dataframe.iloc[day_initial_row:day_final_row, :]

        parse_day(day_dataframe)

        stop_producer = False
        sleep(5)

def write_on_file(file_to_append, trigger_message):

    dat_result = trigger_message["date"] + "," 
    dat_result += trigger_message["measured_time"] + ","
    dat_result += str(trigger_message["temperature"])

    file_to_append.write(dat_result + '\n')

def on_message(client, userdata, message):
    global stop_producer
    global stop_consumer
    global file_to_append

    last_day_action_taken = ""
    if not message:
        print("no message")
        return 
    msg_content = json.loads(message.payload.decode())

    if not msg_content:
        print("could not parse message")
        return

    print('received message', msg_content)

    if "end-flag" in msg_content:
        return

    if msg_content["date"] == last_day_action_taken:
        print("received late message. Ignoring")
        return

    if "skip-day" in msg_content:
        stop_producer = True
        last_day_action_taken = msg_content["date"]
        msg_content["measured_time"] = 'None'
        write_on_file(file_to_append, msg_content) 

    if msg_content["should_turn_on"] == 1:
        #trigger_message = msg_content
        stop_producer = True
        last_day_action_taken = msg_content["date"]
        write_on_file(file_to_append, msg_content) 

def get_month_dataframe(full_df, month_number):
    return full_df[ full_df['month'] == int(month_number) ]

def get_number_days_month(month_df):
    return int(len(month_df) / 24)
    
def main():
    
    #File reading setup
    df = pd.read_csv('stutt.csv',
                 usecols=[0, 1, 2, 3, 6],
                 names=['year', 'month', 'day', 'hour', 'temperature'],
                 header=7,
                 low_memory=False)

    month_number = get_month_input()
    month_dataframe = get_month_dataframe(df, month_number)
    days_on_month = get_number_days_month(month_dataframe)
    
    stream_name = get_stream_name_input()
    months = ['JAN', 'FEV', 'MAR', 'APR']
    filename = stream_name + months[int(month_number) - 1] + '.csv'

    try:
        os.remove(filename)
    except OSError:
        pass
        
    global file_to_append
    file_to_append = open(filename, "a+")
    file_to_append.write("date,actiontime,temperature\n")
    
    #MQTT broker setup
    global client
    client = connect_mqtt()
    client.subscribe('heater-actions', 0)

    parse_month(month_dataframe, days_on_month)

    file_to_append.close()
    
main()


