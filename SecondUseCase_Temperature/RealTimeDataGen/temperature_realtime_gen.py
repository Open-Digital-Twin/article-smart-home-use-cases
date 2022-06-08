from glob import glob
from itertools import zip_longest
import json
from time import sleep
from tracemalloc import stop
import pandas as pd
from kafka import KafkaProducer
from kafka import KafkaConsumer
import threading
import os
from datetime import datetime
import sys

producer = KafkaProducer(bootstrap_servers='localhost:9092')
topic_name = "temperature"
time_step = 15 #min
stop_producer = False
stop_consumer = False
#trigger_message = ""

user_leaving_time = datetime.strptime("12:00", "%H:%M")
user_arriving_time = datetime.strptime("18:00", "%H:%M")

def get_month_input():
    if len(sys.argv) < 2:
        print("input missinig")
        return None
    return sys.argv[1]
    
def get_stream_name():
    if len(sys.argv) < 3:
        print("stream name missinig")
        return None
    return sys.argv[2]

def generate_temperature_event(temperature, hour, min, day, month):
    json_msg = {
        "temperature": round(temperature, 2),
        "measured_time": f"{int(hour)}:{int(min)}",
        "date": f"{int(day)}/{int(month)}"
    }
    json_string = json.dumps(json_msg)
    print("publishing message", json_string)
    producer.send(topic_name, json_string.encode())

def parse_day(time_step, day_dataframe):

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

def parse_month(time_step, month_dataframe, days_on_month):

    global stop_producer

    for day in range(0, days_on_month):

        print('----------------------')
        print(f"DAY {day}")
        print('----------------------')

        day_initial_row = day * 24
        day_final_row = day_initial_row + 24

        day_dataframe = month_dataframe.iloc[day_initial_row:day_final_row, :]

        parse_day(time_step, day_dataframe)

        stop_producer = False
        sleep(5)

def write_on_file(file_to_append, trigger_message):

    dat_result = trigger_message["date"] + "," 
    dat_result += trigger_message["measured_time"] + ","
    dat_result += str(trigger_message["temperature"])

    file_to_append.write(dat_result + '\n')

def receive_heater_commands(file_to_append):
    global stop_producer
    global stop_consumer
    #global trigger_message

    consumer = KafkaConsumer("heater-actions")
    last_day_action_taken = ""

    for msg in consumer:
        if msg.value and json.loads(msg.value):

            msg_content = json.loads(msg.value)
            print('received message', msg_content)

            if "end-flag" in msg_content:
                return

            if msg_content["date"] == last_day_action_taken:
                print("received late message. Ignoring")
                continue
            
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

df = pd.read_csv('stutt.csv',
                 usecols=[0, 1, 2, 3, 6],
                 names=['year', 'month', 'day', 'hour', 'temperature'],
                 header=7,
                 low_memory=False)

month_number = get_month_input()
month_dataframe = get_month_dataframe(df, month_number)
days_on_month = get_number_days_month(month_dataframe)

print("days", days_on_month)
print(month_dataframe)

#parse_month(time_step, month_dataframe, days_on_month)
stream_name = get_stream_name()
months = ['JAN', 'FEV', 'MAR', 'APR']
filename = stream_name + months[int(month_number) - 1] + '.csv'

try:
    os.remove(filename)
except OSError:
    pass

f = open(filename, "a+")
f.write("date,actiontime,temperature\n")

consumer_thread = threading.Thread(target=receive_heater_commands, args=(f,))
publisher_thread = threading.Thread(target=parse_month, args=(time_step, month_dataframe, days_on_month))

print("starting threads")

consumer_thread.start()
publisher_thread.start()

publisher_thread.join()
print("month ended")
producer.send('heater-actions', json.dumps({"end-flag": 1}).encode())

consumer_thread.join()
print("consumer ended")

f.close()
