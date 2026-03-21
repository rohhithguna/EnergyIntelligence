# core/anomaly_engine.py

import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(df, contamination=0.05):
    """
    Detect anomalies using Isolation Forest
    :param df: DataFrame with 'data_rate'
    :param contamination: expected anomaly ratio
    :return: updated df + anomalies dataframe
    """

    model = IsolationForest(contamination=contamination, random_state=42)

    # Fit model
    df['anomaly'] = model.fit_predict(df[['data_rate']])

    # Extract anomalies
    anomalies = df[df['anomaly'] == -1]

    return df, anomalies
