from kafka import KafkaProducer
from ksql import KSQLAPI
import sys
import os
import pandas as pd

def get_file_name():
    if len(sys.argv) < 2:
        print("filename missinig")
        return None
    return sys.argv[1]

def generate_events_on_topic(topic_name, df, client, producer):

    stream_name = topic_name + 'stream' 

    ksql_string = f"CREATE STREAM {stream_name} (temperature double, measured_time double) WITH (KAFKA_TOPIC='{topic_name}', PARTITIONS=1, REPLICAS=1, VALUE_FORMAT='JSON');"
    client.ksql(ksql_string)

    for index, row in df.iterrows():
        timestamp = row[0]
        temperature = row[1]
       
        msg = "{"+ f'"measured_time": {timestamp}, "temperature": {temperature}' + "}"
        producer.send(topic_name, msg.encode())
        producer.flush() #blocks until message is sent
        print("msg sent: ", msg)
    
    streamProperties = {"ksql.streams.auto.offset.reset": "earliest"}
    ksql_string = f"CREATE STREAM {stream_name + 'dummy'} AS SELECT 1 AS DUMMY, * FROM {stream_name};"
    client.ksql(ksql_string, stream_properties=streamProperties)

def main():
    filename = get_file_name()
    print(filename)

    client = KSQLAPI('http://localhost:8088')
    df = pd.read_csv(filename,low_memory=False, usecols=[0,2,3,4])
    producer = KafkaProducer(bootstrap_servers='localhost:9092')

    room_names = {'smallroomwindow':'T2', 'bigroom': 'T3', 'smallroom': 'T4'}

    for room_name in room_names.keys():
        print("publishing room name = ", room_name, "thermometer name = ", room_names[room_name])
        sub_df = df[["time", room_names[room_name]]]
        generate_events_on_topic(room_name, sub_df, client, producer)

main()


