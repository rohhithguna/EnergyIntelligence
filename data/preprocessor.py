import pandas as pd

def preprocess_data(df):
    # remove empty rows
    df = df.dropna(how='all')

    # convert time column
    df['time'] = pd.to_datetime(df['time'], errors='coerce')

    # remove invalid time rows
    df = df.dropna(subset=['time'])

    # handle missing values
    df['data_rate'] = df['data_rate'].fillna(method='ffill')
    df['data_rate'] = df['data_rate'].fillna(method='bfill')

    # remove duplicates
    df = df.drop_duplicates()

    # remove invalid values
    df = df[df['data_rate'] >= 0]

    # sort data
    df = df.sort_values(by='time')

    return df
