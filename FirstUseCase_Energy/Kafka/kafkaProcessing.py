from calendar import c
import json
from enum import IntEnum

from matplotlib.pyplot import table
from kafka import KafkaProducer
from kafka import KafkaConsumer
from ksql import KSQLAPI
import threading
import constants
import time
import datetime


client = KSQLAPI('http://localhost:8088')

producer = KafkaProducer(bootstrap_servers='localhost:9092')
#consumer = KafkaConsumer("equipments")

def initial_setup():
    global client
    #client.ksql("SET 'ksql.query.pull.table.scan.enabled'='true';")
    client.ksql("DROP table if exists EQUIPMENT_TABLE;")
    client.ksql("DROP stream if exists CONVERTED_STREAM;")
    client.ksql("DROP stream if exists EQUIPMENT_STREAM")
    client.create_stream(table_name='EQUIPMENT_STREAM',
                         columns_type=['equipment varchar',
                                       'power double', 'measured_time BIGINT'],
                         topic='equipment',
                         value_format='json')
                         
    ksql_string = "CREATE STREAM CONVERTED_STREAM AS SELECT equipment, power, CAST(TIMESTAMPTOSTRING(measured_time * 1000, 'yyyy-MM-dd') AS DATE) AS MY_DATE FROM EQUIPMENT_STREAM;"
    streamProperties = {"ksql.streams.auto.offset.reset": "earliest"}
    client.ksql(ksql_string, stream_properties=streamProperties)


class Color(IntEnum):
    RED = 1
    GREEN = 2
    BLUE = 3

color = Color.RED
is_realtime = True

def publish(msg, topic):
    global producer
    print(f"Sending msg = {msg} to topic = {topic}")
    producer.send(topic, msg.encode())


def get_variant_color(power):
    if power < 0.1:
        return 255
    if power < 0.2:
        return 192
    if power < 0.3:
        return 128
    if power < 0.4:
        return 64
    return 0

def mock():
    global color
    if color == Color.RED:
        publish('255-255-255-1', "Ex0")
        publish('255-192-192-1', "Ex1")
        publish('255-128-128-1', "Ex2")
        publish('255-64-64-1', "Ex3")
        publish('255-0-0-1', "Ex4")
    elif color == Color.GREEN:
        publish('255-255-255-1', "Ex0")
        publish('192-255-192-1', "Ex1")
        publish('128-255-128-1', "Ex2")
        publish('64-255-64-1', "Ex3")
        publish('0-255-0-1', "Ex4")
    else:
        publish('255-255-255-1', "Ex0")
        publish('192-192-255-1', "Ex1")
        publish('128-128-255-1', "Ex2")
        publish('64-64-255-1', "Ex3")
        publish('0-0-255-1', "Ex4")


def get_discrete_rgba(color_lock, power):
    color_lock.acquire()
    color_to_return = ""
    global color
    print("getting color for power = ", power, " current color = ", color)
    variant = get_variant_color(power)
    alpha = 1.0
    if color == Color.RED:
        color_to_return = f'255-{variant}-{variant}-{alpha}'
    elif color == Color.GREEN:
        color_to_return = f'{variant}-255-{variant}-{alpha}'
    else:
        color_to_return = f'{variant}-{variant}-255-{alpha}'
    color_lock.release()
    return color_to_return


def treat_user_message(json_msg):
    global color

    print("\n\nchanging color to\n\n", json_msg["color"])
    color = json_msg["color"]

def custom_period_average(color_lock, to_date, from_date):
    global client

    print("custom_period_average")
    
    ksql_string = f"SELECT equipment, AVG(POWER) AS AVG_POWER FROM CONVERTED_STREAM WHERE MY_DATE > '{from_date}' AND MY_DATE < '{to_date}' GROUP BY EQUIPMENT EMIT CHANGES;"
    streamProperties = {"ksql.streams.auto.offset.reset": "earliest"}
    query = client.query(ksql_string, stream_properties=streamProperties)

    queryId = get_query_id(next(query))
    print("query id = ", queryId)

    for i in range(0, 4):
        try:
            print("waiting for next item")
            item = next(query)
            print_item(item, "limited period analysis")
            columns = get_columns_from_message(item)
            msg_to_publish = get_discrete_rgba(
                color_lock, columns[constants.POWER_COL])
            publish(msg_to_publish, columns[constants.EQUIPMENT_COL])

        except:
            print("unable to read data")

    print("returning from custom_period_average function. Deleting everything created.")
    client.close_query(queryId)

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

def print_item(item, from_function):
    print("\nReceived item from function = ", from_function)
    columns = get_columns_from_message(item)
    print("EQUIPMENT = ", columns[constants.EQUIPMENT_COL])
    print("AVERAGE POWER = ", columns[constants.POWER_COL])

def real_time_thread(color_lock, is_realtime_lock, real_time_thread_blocking):
    global client
    while True:

        real_time_thread_blocking.acquire()
        print("Realtime thread unlocked")
        real_time_thread_blocking.release()

        print("Making new realtime query")

        ksql_string = "SELECT * FROM EQUIPMENT_STREAM EMIT CHANGES;"
        streamProperties = {"ksql.streams.auto.offset.reset": "latest"}
        query = client.query(ksql_string, stream_properties=streamProperties)

        query_id = get_query_id(next(query))
        print("query id = ", query_id)

        for item in query:
            print_item(item, "real time thread")

            is_realtime_lock.acquire()
            global is_realtime
            if not is_realtime:
                print("Realtime flag is off")
                is_realtime_lock.release()
                break
            is_realtime_lock.release()

            try:
                columns = get_columns_from_message(item)
                msg_to_publish = get_discrete_rgba(
                    color_lock, columns[constants.POWER_COL])
                publish(msg_to_publish, columns[constants.EQUIPMENT_COL])

            except:
                print("invalid message format")

        print("realtime thread was locked. Terminating query")
        client.close_query(query_id)


def change_color(color_lock, new_color):
    color_lock.acquire()
    print("Changing color to = ", new_color)
    global color
    color = new_color
    color_lock.release()


def user_message_thread(color_lock, is_realtime_lock, real_time_thread_blocking_lock):
    consumer = KafkaConsumer("users")
    global is_realtime

    for msg in consumer:
        print("received user message")
        # and msg.key and msg.key.decode():
        if msg.value and json.loads(msg.value):
            json_msg = json.loads(msg.value)
            if "color" in json_msg:
                change_color(color_lock, json_msg["color"])
            if "command" in json_msg:
                if json_msg["command"] == "realtime":
                    print("reactivating realtime thread")
                    real_time_thread_blocking_lock.release()

                    is_realtime_lock.acquire()
                    is_realtime = True
                    is_realtime_lock.release()

                elif json_msg["command"] == "limited":
                    print("blocking realtime thread")
                    real_time_thread_blocking_lock.acquire()

                    is_realtime_lock.acquire()
                    is_realtime = False
                    is_realtime_lock.release()

                    if "to_date" in json_msg and "from_date" in json_msg:
                        from_date = json_msg["from_date"]
                        to_date = json_msg["to_date"]
                        custom_period_average(color_lock=color_lock,
                                              to_date=to_date,
                                              from_date=from_date)


initial_setup()
color_lock = threading.Lock()
is_realtime_lock = threading.Lock()
real_time_thread_blocking_lock = threading.Lock()

# creating threads
t1 = threading.Thread(target=user_message_thread, args=(
    color_lock, is_realtime_lock, real_time_thread_blocking_lock))
t2 = threading.Thread(target=real_time_thread, args=(
    color_lock, is_realtime_lock, real_time_thread_blocking_lock))

# start threads
t1.start()
t2.start()

# wait until threads finish their job
t1.join()
t2.join()


# for msg in consumer:
#     print("key", msg.key, "value", msg.value)
#     json.loads(msg.value)
#     if msg.value and json.loads(msg.value) and msg.key and msg.key.decode():
#         print(json.loads(msg.value))
#         print("received", json.loads(msg.value), "topic", msg.topic)
#         json_msg = json.loads(msg.value)
#         print(json_msg)
#         if msg.key.decode().startswith('user'):
#             treat_user_message(json_msg)
#             mock()
#         else:
#             msg_to_publish = get_discrete_rgba(json_msg["power"])
#             print(msg_to_publish.encode())
#             publish(msg_to_publish, json_msg["equipment"])
