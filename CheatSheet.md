


### Confluent CLI

#### Start confluent:

export CONFLUENT_HOME=confluent-7.0.1
export PATH=$PATH:$CONFLUENT_HOME/bin
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)
confluent local services start

#### Start/Stop specific confluent app:

confluent local services connect stop
confluent local services connect start

#### Check status of specific app:

confluent local services connect status

#### Check logs of specific app:

confluent local services connect log

### Connect

#### Install Confluent Hub Connector:

confluent-hub install confluentinc/kafka-connect-mqtt:1.2.3

#### POST Connectors:
curl -s -X POST -H 'Content-Type: application/json' --data @connectorSink.json http://localhost:8083/connectors
curl -s -X POST -H 'Content-Type: application/json' --data @connectorSource.json http://localhost:8083/connectors
curl -s -X POST -H 'Content-Type: application/json' --data @connectorSourceUser.json http://localhost:8083/connectors

#### DELETE Connector:
curl -s -X DELETE localhost:8083/connectors/mqtt-sink

#### Get STATUS of Connector:
curl -s "http://localhost:8083/connectors/mqtt-sink/status"

### Kafka

#### Create Topic:
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic oi

#### Producer:
kafka-console-producer --broker-list localhost:9092 --topic equipments

#### Consumer
kafka-console-consumer --bootstrap-server localhost:9092 --topic equipments --property print.key=true --from-beginning

### KSQL

#### Change Offset in KSQL:
SET 'auto.offset.reset' = 'earliest';

### Python Kafka Libs
pip install kafka-python ksql

### Gazebo

#### Plugin Environment Variable
export GAZEBO_PLUGIN_PATH=${GAZEBO_PLUGIN_PATH}:~/Documents/build

sudo apt-get update && sudo apt-get install build-essential

para o plugin de sensor, <plugin> deve estar dentro de <sensor>




