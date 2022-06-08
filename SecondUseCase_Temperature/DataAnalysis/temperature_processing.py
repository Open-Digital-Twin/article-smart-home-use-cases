""""
Input: 
1- Kafka topic name. Options: smallroomwindow, smallroom, bigroom

Operation: Subscribes to Kafka's temperature topic. 
Creates a Kafka Stream from the Kafka topic stated on the input
Makes queries to the stream created to see if the heater should be turned on or not.
Publishes the decision on the heater-actions topic.

"""

from kafka import KafkaProducer
from kafka import KafkaConsumer
from ksql import KSQLAPI
from datetime import datetime

import json
import sys

consumer = KafkaConsumer("temperature")
client = KSQLAPI('http://localhost:8088')
producer = KafkaProducer(bootstrap_servers='localhost:9092')

target_temperature = 20
target_temperature_did_change = True
simulated_time_target_temperature = ""
target_time_string = "18:00"
last_day_action_taken = ""

TEMPERATURE_COL = 0
MEASURED_TIME_COL = 1

def get_topic_name():
    if len(sys.argv) < 2:
        print("stream name missinig")
        return None
    return sys.argv[1]

def get_query_id(event):
    query_desc = event
    query_desc = query_desc.strip()
    query_desc = query_desc[1:-1]
    query_desc_json = json.loads(query_desc)
    return query_desc_json["header"]["queryId"]

def get_columns_from_message(item):
    item = item.strip()
    item = item[0:-1]
    json_msg = json.loads(item)
    return json_msg["row"]["columns"]

def get_closest_simulated_temperature(stream_name, temperature):
    
    if temperature < 0 and temperature > -0.1:
        temperature = -0.1
    elif temperature > 0 and temperature < 0.1:
        temperature = 0.1
    ksql_string = f"select * from {stream_name} where temperature >= {temperature} emit changes limit 1;"
    streamProperties = {"ksql.streams.auto.offset.reset": "earliest"}
    query = client.query(ksql_string, stream_properties=streamProperties)
    
    _ = get_query_id(next(query))

    for result in query:
        print("new result")
        columns = get_columns_from_message(result)
        time = columns[MEASURED_TIME_COL]
        return time
    
    #client.close_query(queryId)
    return None

def send_heater_command(should_turn_on, trigger_message_json):
    global last_day_action_taken
    trigger_message_json["should_turn_on"] = int(should_turn_on)
    if should_turn_on or "skip-day" in trigger_message_json:
        last_day_action_taken = trigger_message_json["date"]
    json_string = json.dumps(trigger_message_json) # = "{" + f'"should_turn_on": {int(should_turn_on)}, "measured_time": "{measured_time}"' + "}"
    print("json msg", json_string)
    producer.send("heater-actions", json_string.encode())

def prepare_ksql(stream_name, topic_name):

    client.ksql(f"DROP stream if exists {stream_name + 'dummy'}")
    client.ksql(f'DROP stream if exists {stream_name}')

    streamProperties = {"ksql.streams.auto.offset.reset": "earliest"}

    ksql_string = f"CREATE STREAM {stream_name + 'stream'} (temperature double, measured_time double) WITH (KAFKA_TOPIC='{topic_name}', PARTITIONS=1, REPLICAS=1, VALUE_FORMAT='JSON');"
    client.ksql(ksql_string, stream_properties=streamProperties)
    print("created stream")

    # this is to for further processing in results_processing.py
    ksql_string = f"CREATE STREAM {stream_name + 'streamdummy'} AS SELECT 1 AS DUMMY, * FROM {stream_name};"
    client.ksql(ksql_string, stream_properties=streamProperties)
    print("created stream dummy")


def main():

    topic_name = get_topic_name()
    stream_name = topic_name

    prepare_ksql(stream_name, topic_name)
    
    # starts receiving the messages from the temperature topic
    for msg in consumer:
        
        print("received message")
        if not msg.value: 
            print("no message value")
            pass

        json_msg = json.loads(msg.value)

        if not json_msg:
            print("poorly formated message")
            pass
            
        if "date" in json_msg and json_msg["date"] == last_day_action_taken:
            continue

        if "temperature" in json_msg and "measured_time" in json_msg:
            current_temperature = json_msg["temperature"]
            
            if current_temperature >= target_temperature:
                json_msg["skip-day"] = 1
                send_heater_command(False, json_msg)
                continue
            
            simulated_time_current_temperature = get_closest_simulated_temperature(stream_name, current_temperature)

            if target_temperature_did_change:
                simulated_time_target_temperature = get_closest_simulated_temperature(stream_name, target_temperature)
                target_temperature_did_change = False

            simulated_time_to_target = simulated_time_target_temperature - simulated_time_current_temperature
        
            current_time = datetime.strptime(json_msg["measured_time"], "%H:%M")
            target_time = datetime.strptime(target_time_string, "%H:%M")
            
            time_left = (target_time - current_time).total_seconds()

            send_heater_command(
                time_left < 0 or simulated_time_to_target < 0 or simulated_time_to_target >= time_left,
                json_msg
            )
        else:
            print("could not parse input")

main()
        
        
