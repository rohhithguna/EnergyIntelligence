import pandas as pd
import numpy as np

filepath = '/Users/rohhithg/Desktop/MYSELF/MyProject/DataFlow_project/dataset/server_logs.csv'
df = pd.read_csv(filepath)

np.random.seed(42)
base_response = np.random.normal(150, 40, len(df))

def add_anomalies(values, spike_prob=0.05, drop_prob=0.03, anomaly_prob=0.02):
    result = values.copy()
    for i in range(len(result)):
        r = np.random.random()
        if r < spike_prob:
            result[i] *= np.random.uniform(2.5, 5.0)
        elif r < spike_prob + drop_prob:
            result[i] *= np.random.uniform(0.1, 0.4)
        elif r < spike_prob + drop_prob + anomaly_prob:
            result[i] = np.random.uniform(np.max(values) * 2, np.max(values) * 3)
    return result

response_time = add_anomalies(base_response)
df['response_time'] = np.maximum(response_time, 50)

df.to_csv(filepath, index=False)
print(f"✓ server_logs.csv updated with response_time numeric column")
