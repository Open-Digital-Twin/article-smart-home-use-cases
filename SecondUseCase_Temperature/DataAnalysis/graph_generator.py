from wsgiref.handlers import format_date_time
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import sys
import matplotlib.dates as mdates


def get_file_name():
    if len(sys.argv) < 2:
        print("filename missinig")
        return None
    return sys.argv[1]

df = pd.read_csv(get_file_name(),
                 header=0,
                 low_memory=False)

def get_day(x):
    date_comp = x.split('/')
    return date_comp[0]

def format_time(x):
    return datetime.strptime(x, "%H:%M")

df['date'] = df['date'].apply(get_day)

rows_number = 3
columns_number = 1
graph_number = 1

#plot date vs action time                
df['actiontime'] = df['actiontime'].apply(format_time)
y_points = df['actiontime']
x_points = df['date']

ax = plt.subplot(rows_number, columns_number, graph_number)
plt.ylabel("ACTION TIME")
ax.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.plot_date(x_points, y_points, 'o')

graph_number += 1

#plot date vs temperature
x_points = df['date']
y_points = df['temperature']

plt.subplot(rows_number, columns_number, graph_number)
plt.ylabel("INITIAL TEMP")
plt.plot(x_points, y_points, 'o')

graph_number += 1

#plot date vs temperature on target time
x_points = df['date']
y_points = df['SimulatedTemperature']

plt.subplot(rows_number, columns_number, graph_number)
plt.ylabel("FINAL TEMP")
plt.plot(x_points, y_points, 'o')

plt.suptitle("Days of January")
plt.show()