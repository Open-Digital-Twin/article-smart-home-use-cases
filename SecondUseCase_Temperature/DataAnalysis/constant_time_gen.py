import pandas as pd
import sys
import os
import glob

months = ['JAN', 'FEV', 'MAR', 'APR']

def get_mean_in_secs(df):

    df["actiontime"] = df["actiontime"].replace(regex=[":0"], value=[":00"])
    df = df[df["actiontime"] != "None"]
    print(df)
    df["actiontime"] = pd.to_datetime(df["actiontime"])
    df["hour"] = df["actiontime"].dt.hour
    df["minutes"] = df["actiontime"].dt.minute
    df["timeinsecs"] = df["minutes"] * 60 + df["hour"] * 3600
    return int(df["timeinsecs"].mean())

def get_mean_of_means_timedelta(means):

    mean = sum(means) / len(means)
    mean_time = pd.to_timedelta(mean, unit='s')
    mean_time = mean_time.round('15min')
    return mean_time


def get_temperature(df):
    mean_time_formated = f"{mean_time.components.hours}:{mean_time.components.minutes}"
    return mean_time_formated

def get_files_of_month(month_number):
    global months
    month = months[month_number - 1]
    files = glob.glob(f'../RealTimeDataGen/HeaterRoutineFiles/*{month}.csv')
    return files

def get_number_days_month(month_df):
    return int(len(month_df) / 24)

def write_on_file(file_to_append, month, day, actiontime, temperature):

    actiontime_formated = f"{actiontime.components.hours}:{actiontime.components.minutes}"

    dat_result = f"{day}/{month}" + ","
    dat_result += actiontime_formated + ","
    dat_result += str(round(temperature, 2))

    print("dat result", dat_result)
    file_to_append.write(dat_result + '\n')

def generate_lines(f,days_on_month, target_month, target_time, month_df):
    
    for day in range(1, days_on_month + 1):

        print('--------------------------')
        print("DAY", day)
        print('--------------------------')
        day_df = month_df[month_df["day"] == day]
        temperature = 0

        if target_time.components.minutes == 0:
            day_df = day_df[day_df["hour"] == target_time.components.hours]
            temperature = day_df.iloc[0]["temperature"]
        else:
            day_df = day_df[day_df["hour"].isin(
                [target_time.components.hours, target_time.components.hours + 1])]
            print(day_df)
            temp_diff = day_df.iloc[1]['temperature'] - \
                day_df.iloc[0]['temperature']
            increment = temp_diff / 4
            temperature = day_df.iloc[0]["temperature"] + \
                (increment * (target_time.components.minutes / 15))

        write_on_file(f, target_month, day, target_time, temperature)

def prepare_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

    f = open(filename, "a+")
    f.write("date,actiontime,temperature\n")
    return f

full_df = pd.read_csv('../RealTimeDataGen/stutt.csv',
                 usecols=[1, 2, 3, 6],
                 names=['month', 'day', 'hour', 'temperature'],
                 header=7,
                 low_memory=False)

for target_month in [1,2,3,4]:
    print("month", target_month)
    files_of_month = get_files_of_month(target_month)
    print(files_of_month)
    mean_times = []
    for file_name in files_of_month:
        dfTimeSource = pd.read_csv(file_name, low_memory=False)
        mean_time = get_mean_in_secs(dfTimeSource)
        mean_times.append(mean_time)

    target_time = get_mean_of_means_timedelta(mean_times)
    print("timeee", target_time)
    month_df = full_df[full_df['month'] == target_month]
    days_on_month = get_number_days_month(month_df)
    result_filename = f"ConstantTime/{months[target_month - 1]}.csv"
    print("generating file", result_filename)
    result_file = prepare_file(result_filename)
    generate_lines(result_file,days_on_month, target_month, target_time, month_df)




