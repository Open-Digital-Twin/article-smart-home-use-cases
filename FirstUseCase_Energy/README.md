# Energy Visualization Use Case

## Overview

This use case is divided in three components: the data collection, data processing, and the visualization. Each of them must be executed in a separate terminal. The first simulates the receival from data from sensors. It reads from a file some power measurements and publishes this information on a MQTT topic. The second hears from a Kafka topic and converts this measurements to colors, publishing the results on Kafka topics respective to each of the appliances. The third lauches the Gazebo 3D world, with the appliances' control scripts (plugins) that change their colors based on what they receive from MQTT topics. 

The data processing works with Kafka and the first and third components publish on and subscibe to MQTT topics, respectively. Therefore, we need Kaka Connect to make this transposition. More details below. 

## Requirements

1. Install Gazebo 

This is the software responsible for the 3D visualization. Tutuorial on [Gazebo Website](https://classic.gazebosim.org/tutorials?tut=install_ubuntu)

2. Install Confluent

This is package includes all Apache Kafka components necessary to run application (and even some more).  Tutorial on [Confluent Website](https://docs.confluent.io/confluent-cli/current/install.html)

## How to Run (Unix)

### 1st terminal - Gazebo visualization

1. Create a `build` folder under `plugins` and navigate to it

`$ cd plugins && mkdir build`

`$ cd plugins/build/`

2. Compile the plugins 

`$ cmake ../`
`$ make`

3. Set GAZEBO_PLUGIN_PATH environment variable to the current directory (`build`)

`$ export GAZEBO_PLUGIN_PATH=${GAZEBO_PLUGIN_PATH}:$(pwd)`

4. Go back to `Energy` directory  and elect contents of folder `models` and move to `home/model_editor_models` 

5. Select contents of folder `building` and move to `home/building_editor_models` (both model_ and building_ editor_models were created by Gazebo installation)

6. Run the application

`$ gazebo newWorld`

### 2nd terminal - Real time generation

1. Go to the `RealTimeGen` folder and download, in this directory, the data set (HomeC.csv) file containing the power readings from https://www.kaggle.com/datasets/taranvee/smart-home-dataset-with-weather-information

2. Run the script

`$ python3 csv_reader.py`

### 3rd terminal - Data Processing

1. Start confluent 

`confluent local services start`

Obs.: Do not forget to reset confluents environemtal variables in case they are not permanent

`cd /path/to/confluent/folder`

`export CONFLUENT_HOME=confluent-7.0.1`

`export PATH=$PATH:$CONFLUENT_HOME/bin`

Obs.: You may need to set the Java 8 it you have more than one version installed:

Mac: `export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)`

2. Go back to this repository's `connectors` folder under `Kafka` and post the Kafka Connectors 

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSink.json http://localhost:8083/connectors`

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSource.json http://localhost:8083/connectors`

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSourceUser.json http://localhost:8083/connectors`

3. Go back to `Kafka` folder and run the processing script

`python3 kafkaprocessing.py`
