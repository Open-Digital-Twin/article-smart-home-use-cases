"""
Operation: This script combines all files on RealTimeUpdated and ConstantTimeUpdated
to generate comparisson graphs. The comparisson criteria may be the duration of heater 
operation (function average_time_graph) or the final temperature reached on 18 o'clock (average_temperature_graph).

Input: the graph type: time or temperature.

"""

import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import sys
import matplotlib.dates as mdates

rows_number = 2
columns_number = 2
months = ["JAN", "FEV", "MAR", "APR"]
month_names = ["January", "February", "March", "April"]
target_temperature = 20
bar_width = 0.33
room_names = ['smallroom', 'bigroom', 'smallroomwindow']
time_interval_format = "%Hh"

def get_graph_type():
    if len(sys.argv) < 2:
        print("graph type missinig")
        return None
    return sys.argv[1]

def get_day(x):
    date_comp = x.split('/')
    return date_comp[0]

def as_float(x):
    if x == 'None':
        return None
    return float(x)

def format_time(x):
    if x == 'None':
        return None
    return datetime.strptime(x, "%H:%M")

def format_timeinterval(x):
    return datetime.strptime(f"{x.components.hours}:{x.components.minutes}", time_interval_format)

colors = ['r', 'g', 'b', 'c']

def time_heater_on_graph():
    for index in range(1, len(sys.argv) - 1):

        filename = sys.argv[index]
        df = pd.read_csv(filename,
                        header=0,
                        low_memory=False)

        df['date'] = df['date'].apply(get_day)
        x_points = df['date']
        df["TimeHeaterOn"] = df["TimeHeaterOn"].apply(format_time)
        y_points = df['TimeHeaterOn']
        print(df["TimeHeaterOn"])

        plt.ylabel("TIME HEATER ON")
        ax = plt.subplot(1, 1, 1)
        ax.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.plot_date(x_points, y_points,  f"{colors[index - 1]}.")

    plt.suptitle(f"Time Heater was on in {sys.argv[len(sys.argv) - 1]}")
    plt.show()

def end_temperature_graph():
    for index in range(1, len(sys.argv) - 1):

        file = sys.argv[index]
        df = pd.read_csv(file,
                        header=0,
                        low_memory=False)

        df['date'] = df['date'].apply(get_day)
        x_points = df['date']
        df["SimulatedTemperature"] = df["SimulatedTemperature"].apply(as_float)
        y_points = df['SimulatedTemperature']

        plt.ylabel("FINAL TEMP")
        plt.plot(x_points, y_points, f"{colors[index - 1]}.")

    plt.hlines(20, 0, 31, linestyle="dashed", colors='black')
    plt.suptitle(f"End Temperature on {sys.argv[len(sys.argv) - 1]}")
    plt.show()

# returns: the average difference between target temperature and simulated temperature
# considers one month one room
def get_average_difference_temp_target(month_df):
    
    month_df["SimulatedTemperature"] = month_df["SimulatedTemperature"].apply(as_float)
    month_df["difference"] = abs(month_df["SimulatedTemperature"] - target_temperature)
    return month_df["difference"].mean()

def get_average_heater_on_time(df):

    df["TimeHeaterOn"] = df["TimeHeaterOn"].replace(regex=[":0"], value=[":00"])
    df = df[df["TimeHeaterOn"] != "None"]
    df["TimeHeaterOn"] = pd.to_datetime(df["TimeHeaterOn"])
    df["hour"] = df["TimeHeaterOn"].dt.hour
    df["minutes"] = df["TimeHeaterOn"].dt.minute
    df["timeinsecs"] = df["minutes"] * 60 + df["hour"] * 3600
    return int(df["timeinsecs"].mean())

def build_data_for_graph(function):
    
    months_data = {k:{} for k in months}

    total_average_real_time = 0
    total_average_limited_time = 0

    for graph_number in range(0, len(months)):

        real_time_values = []
        constant_time_values = []
        month_id = months[graph_number]
        
        for room_name in room_names:
            constant_time_filename = f"ConstantTimeUpdated/{room_name}{month_id}.csv"
            df_constant = pd.read_csv(constant_time_filename, header=0, low_memory=False)
            avg_constant = function(df_constant)
            print("average of constant ", month_id, " ", avg_constant, "room = ", room_name)
            constant_time_values.append(avg_constant)
            total_average_limited_time += avg_constant

            real_time_filename = f"RealTimeUpdated/{room_name}{month_id}Updated.csv"
            df_realtime = pd.read_csv(real_time_filename, header=0, low_memory=False)    
            avg_realtime = function(df_realtime)
            print("average of realtime ", month_id, " ", avg_realtime, "room = ", room_name)
            real_time_values.append(avg_realtime)
            total_average_real_time += avg_realtime

        months_data[month_id]["constant"] = constant_time_values
        months_data[month_id]["realtime"] = real_time_values

    print("total real 0", total_average_real_time)
    total_average_real_time = total_average_real_time / (len(months) + len(room_names))
    print("total real 1", total_average_real_time)
    print("total limited 0", total_average_limited_time)
    total_average_limited_time = total_average_limited_time / (len(months) + len(room_names))
    print("total limited 1", total_average_limited_time)
    
    return months_data


def average_temperature_graph():

    plt.rcParams.update({'font.size': 12})
    
    months_data = build_data_for_graph(get_average_difference_temp_target)
    print(months_data)

    for i in range(len(months)):
        
        ax = plt.subplot(rows_number, columns_number, i + 1)

        month_id = months[i]
        month_name = month_names[i]
        print(month_id, month_name)
        month_data = months_data[month_id]

        bars_set_central_x = [0,1,2]
        plt.bar(bars_set_central_x, month_data["constant"], color ='#F5C2C1', width = bar_width, label ='Fixed Time', edgecolor='black', linewidth = 0.5)
        plt.bar([r + bar_width for r in bars_set_central_x], month_data["realtime"], color ='#CEE741', width = bar_width, label ='Our system', edgecolor='black', linewidth = 0.5)

        plt.xticks([r + bar_width/2 for r in bars_set_central_x], room_names)
        
        plt.title(month_name)

    handles, labels = ax.get_legend_handles_labels()
    plt.figlegend(handles, labels, loc='upper right')
    plt.suptitle("Difference between calculated and desired temperature at 18h.")
    plt.show()
    plt.gcf().subplots_adjust(hspace=1.2)
    

def average_time_graph():
    
    plt.rcParams.update({'font.size': 12})
    months_data = build_data_for_graph(get_average_heater_on_time)
    print(months_data)

    for i in range(len(months)):
        
        ax = plt.subplot(rows_number, columns_number, i + 1)
        #ax.yaxis.set_major_formatter(mdates.DateFormatter(time_interval_format))
       
        month_id = months[i]
        month_name = month_names[i]
        print(month_id, month_name)
        month_data = months_data[month_id]

        means_constant = [x/3600 for x in month_data["constant"]]
        #means_constant = pd.to_timedelta(month_data["constant"], unit='s') # month_data["constant"]
        #means_constant = [format_timeinterval(x) for x in means_constant]
        print(means_constant)

        means_realtime = [x/3600 for x in month_data["realtime"]]
        #means_realtime = pd.to_timedelta(month_data["realtime"], unit='s') # month_data["realtime"]
        
        #means_realtime = [format_timeinterval(x) for x in means_realtime]
        
        bars_set_central_x = [0,1,2]
        plt.bar(bars_set_central_x, means_constant, color ='#F5C2C1', width = bar_width, label ='Fixed Time', edgecolor='black', linewidth = 0.5)
        plt.bar([r + bar_width for r in bars_set_central_x], means_realtime, color ='#CEE741', width = bar_width, label ='Our system', edgecolor='black', linewidth = 0.5)
        
        #plt.plot_date(bars_set_central_x, means_realtime,  'g.')
        plt.xticks([r + bar_width/2 for r in bars_set_central_x], room_names)
        
        plt.title(month_name)

    handles, labels = ax.get_legend_handles_labels()
    plt.figlegend(handles, labels, loc='upper right')
    plt.suptitle("Average duration in hours of heater operation")
    plt.show()


graph_type = get_graph_type()
if graph_type == "time":
    average_time_graph()
elif graph_type == "temperature":
    average_temperature_graph()
else:
    print("invalid graph type. Current available: time or temperature")