# Use Case 2 - Indoor Temperature Prediction

This use case aims to determine the best time to turn on a heater so that a room's indoor temperature is 20ºC at 18 o'clock. 
Below we describe the steps we took to evaluate the system. 
Our evaluation measures the operation of our system in three different rooms and during the four first months of the year.

## 1. Simulation

In this step, we simulated the heating of three different rooms in the software Energy 2D. To do so, we:

1. Downloaded and installed the software from
[Enery 2D Website](https://energy.concord.org/energy2d/download.html)

2. Designed the three rooms we wanted, saving as threeRooms.e2d. 
3. We run the simualtion for the equivalent of 13 hours and stopped it. In practice it takes some real-world minutes, as the simulation runs faster

4. Exported the data (open graph -> view data -> Copy data) and, in a text editor, made a find and replace and transformed the data to a CSV. 
Also, as this process doesn't copy the header indicating the columns' names, we manually added it.
5. We saved the file as [dataset.csv](SimulatedStream/dataset.csv) under `SimulatedStream` folder

6. Started confluent 

`ConfluentFolder user$ confluent local services start`

Obs.: Do not forget to reset confluents environemtal variables in case they are not permanent

`cd /path/to/ConfluentFolder`

`export CONFLUENT_HOME=confluent-7.0.1`

`export PATH=$PATH:$CONFLUENT_HOME/bin`

Obs.: You may need to set the Java 8 it you have more than one version installed:

Mac: `export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)`

7. Post the five connectors (four source and one sink)

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSinkHeaterActions.json http://localhost:8083/connectors`

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSourceRealTimeTemperature.json http://localhost:8083/connectors`

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSourceSimulationBR.json http://localhost:8083/connectors`

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSourceSimulationSR.json http://localhost:8083/connectors`

`curl -s -X POST -H 'Content-Type: application/json' --data @connectorSourceSimulationSRW.json http://localhost:8083/connectors`

8. We run the [Python Script](SimulatedStream/generate_temperature_streams.py) under the same folder passing the dataset as parameter:

`SimulatedStream user$ python3 generate_temperature_streams.py dataset.csv`

This creates three streams on Kafka, one for each room, that represent their heating simulation.

## 2. Data generation and processing

This step runs a script that emulates temperature readings from a physical room. 
Also, runs another script that receives these values and determines if the heater placed on the same room should be turned on. The following steps we executed for runing one itearation of the system. One iteration corresponds to one room and one month, so we executed the following steps 12 times. All the results of our excecutions, called heater routine files, are placed under `HeaterRoutineFiles` folder. In the following example we consider the iteration for the small room in January.

1. Run the Data Processing script for a room 

`cd DataAnalysis`
`python3 temperature_processing.py smallroom`

2. In another terminal, run the script that genreates temperature measurements

`cd RealTimeDataGen`
`python3 temperature_realtime_gen.py 1 smallroom`

3. Wait until the second terminates and then manually terminates the first.
At the end, you will have a smallroomJAN.csv in the RealTimeDataGen directory.

4. Predict which temperature the system reached at 18 o'clock at every day of January. To do so, run:

`cd DataAnalysis`

`python3 results_processing.py r ../RealTimeDataGen/smallroomJAN.csv`

## 3. Generate Files for the comparisson system

For evaluating our system we compared with one that turns the heater on every day at a fixed time. Each of the four months that we evaluated has a fixed time, which was determined by our system's action-time average for the same month considering all rooms. To be more clear, the fixed time of the month of January is the average of the 93 daily action-time values presented in smallroomJAN.csv, bigroomJAN.csv and smallroomwindowJAN.csv. So, for executing the following steps, you must have executed all the 12 iterations of our system.


1. Generate the heater routine file for all four months

`python3 constant_time_ge.py`

At the end you will have four files under the `ConstantTime` folder.

2. Predict which temperature the system reached at 18 o'clock for every room. To do so, run:

`python3 results_processing.py c smallroom`

After that, you will have a four new files under `ConstantTimeUpdated`, one representing the small room's heatin on the four months. Run again for the other rooms by changing the seond argument to bigroom and smallroomwindow. At the end you will have 12 files.


## 4. Generate the graphs

For comparing the system, we chose two criterias: the time heater's daily operation time (from the moment it was turned on until 18 o'clock) and the final temperature the system reached at 18 o'clock. For generating a graphes that compare the monthly average per room we run:

`python3 graph_mixer.py time`

`python3 graph_mixer.py temperature`



