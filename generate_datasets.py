import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

base_time = datetime(2024, 1, 1, 0, 0, 0)
rows = 500

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

def generate_generic():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    data_rate = np.random.normal(100, 20, rows)
    data_rate = add_anomalies(data_rate)
    return pd.DataFrame({
        'time': timestamps,
        'data_rate': np.maximum(data_rate, 0)
    })

def generate_network_traffic():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    base_bytes = np.random.normal(50000, 10000, rows)
    bytes_transferred = add_anomalies(base_bytes)
    
    source_ips = [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(rows)]
    dest_ips = [f"10.0.0.{np.random.randint(1, 255)}" for _ in range(rows)]
    protocols = np.random.choice(['TCP', 'UDP', 'ICMP'], rows)
    ports = np.random.choice([80, 443, 8080, 3306, 5432], rows)
    
    return pd.DataFrame({
        'time': timestamps,
        'source_ip': source_ips,
        'destination_ip': dest_ips,
        'bytes_transferred': np.maximum(bytes_transferred, 100),
        'protocol': protocols,
        'port': ports
    })

def generate_server_logs():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    log_levels = np.random.choice(['INFO', 'WARN', 'ERROR', 'DEBUG'], rows, p=[0.6, 0.2, 0.15, 0.05])
    services = np.random.choice(['auth_service', 'api_gateway', 'database', 'cache', 'worker'], rows)
    messages = [f"Log message {i}" for i in range(rows)]
    sources = [f"server_{np.random.randint(1, 10)}" for _ in range(rows)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'log_level': log_levels,
        'message': messages,
        'service': services,
        'source': sources
    })

def generate_finance_transactions():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    base_amount = np.random.normal(500, 150, rows)
    amount = add_anomalies(base_amount)
    
    transaction_types = np.random.choice(['deposit', 'withdrawal', 'transfer', 'purchase'], rows, p=[0.3, 0.3, 0.25, 0.15])
    account_ids = [f"ACC_{np.random.randint(100000, 999999)}" for _ in range(rows)]
    currencies = np.random.choice(['USD', 'EUR', 'GBP', 'JPY'], rows, p=[0.6, 0.2, 0.15, 0.05])
    
    return pd.DataFrame({
        'time': timestamps,
        'amount': np.maximum(amount, 10),
        'transaction_type': transaction_types,
        'account_id': account_ids,
        'currency': currencies
    })

def generate_user_activity():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    user_ids = [f"USER_{np.random.randint(1000, 9999)}" for _ in range(rows)]
    actions = np.random.choice(['login', 'logout', 'upload', 'download', 'view', 'edit'], rows, p=[0.2, 0.2, 0.15, 0.15, 0.2, 0.1])
    devices = np.random.choice(['mobile', 'desktop', 'tablet'], rows, p=[0.5, 0.35, 0.15])
    locations = np.random.choice(['US', 'EU', 'ASIA', 'AU'], rows, p=[0.4, 0.3, 0.2, 0.1])
    
    base_duration = np.random.normal(300, 60, rows)
    duration = add_anomalies(base_duration)
    
    return pd.DataFrame({
        'time': timestamps,
        'user_id': user_ids,
        'action': actions,
        'device': devices,
        'location': locations,
        'data_rate': np.maximum(duration, 10)
    })

def generate_iot_sensor():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    sensor_ids = [f"SENSOR_{np.random.randint(1, 50)}" for _ in range(rows)]
    
    base_value = np.random.normal(22, 2, rows)
    value = add_anomalies(base_value)
    
    locations = np.random.choice(['warehouse_a', 'warehouse_b', 'office', 'lab'], rows)
    units = np.random.choice(['celsius', 'celsius', 'celsius', 'psi'], rows)
    
    return pd.DataFrame({
        'time': timestamps,
        'sensor_id': sensor_ids,
        'value': value,
        'location': locations,
        'unit': units
    })

def generate_web_traffic():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    urls = [f"/page_{np.random.randint(1, 20)}" for _ in range(rows)]
    
    base_response = np.random.normal(200, 50, rows)
    response_time = add_anomalies(base_response)
    
    status_codes = np.random.choice([200, 201, 301, 400, 404, 500, 503], rows, p=[0.7, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
    methods = np.random.choice(['GET', 'POST', 'PUT', 'DELETE'], rows, p=[0.7, 0.2, 0.05, 0.05])
    
    return pd.DataFrame({
        'time': timestamps,
        'url': urls,
        'response_time': np.maximum(response_time, 10),
        'status_code': status_codes,
        'method': methods
    })

def generate_api_logs():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    endpoints = [f"/api/v1/resource_{np.random.randint(1, 25)}" for _ in range(rows)]
    
    base_latency = np.random.normal(150, 40, rows)
    response_time = add_anomalies(base_latency)
    
    statuses = np.random.choice([200, 201, 400, 401, 404, 500], rows, p=[0.7, 0.05, 0.08, 0.05, 0.07, 0.05])
    methods = np.random.choice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], rows, p=[0.5, 0.25, 0.1, 0.1, 0.05])
    
    return pd.DataFrame({
        'time': timestamps,
        'endpoint': endpoints,
        'response_time': np.maximum(response_time, 5),
        'status': statuses,
        'method': methods
    })

def generate_system_metrics():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    
    base_cpu = np.random.normal(40, 15, rows)
    cpu_usage = add_anomalies(base_cpu)
    cpu_usage = np.clip(cpu_usage, 0, 100)
    
    base_memory = np.random.normal(60, 10, rows)
    memory_usage = add_anomalies(base_memory)
    memory_usage = np.clip(memory_usage, 0, 100)
    
    disk_usage = np.random.normal(70, 8, rows)
    disk_usage = np.clip(disk_usage, 0, 100)
    
    network = np.random.normal(500, 100, rows)
    network = np.maximum(network, 0)
    
    return pd.DataFrame({
        'time': timestamps,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
        'network': network
    })

def generate_application_logs():
    timestamps = [base_time + timedelta(minutes=i) for i in range(rows)]
    events = np.random.choice(['startup', 'shutdown', 'error', 'warning', 'request', 'response'], rows, p=[0.05, 0.05, 0.1, 0.15, 0.35, 0.30])
    statuses = np.random.choice(['success', 'failed', 'pending', 'timeout'], rows, p=[0.7, 0.15, 0.1, 0.05])
    modules = [f"module_{np.random.randint(1, 15)}" for _ in range(rows)]
    severities = np.random.choice(['low', 'medium', 'high', 'critical'], rows, p=[0.5, 0.3, 0.15, 0.05])
    
    base_value = np.random.normal(50, 15, rows)
    data_rate = add_anomalies(base_value)
    
    return pd.DataFrame({
        'time': timestamps,
        'event': events,
        'status': statuses,
        'module': modules,
        'severity': severities,
        'data_rate': np.maximum(data_rate, 0)
    })

datasets = {
    'generic': generate_generic(),
    'network_traffic': generate_network_traffic(),
    'server_logs': generate_server_logs(),
    'finance_transactions': generate_finance_transactions(),
    'user_activity': generate_user_activity(),
    'iot_sensor': generate_iot_sensor(),
    'web_traffic': generate_web_traffic(),
    'api_logs': generate_api_logs(),
    'system_metrics': generate_system_metrics(),
    'application_logs': generate_application_logs()
}

output_dir = '/Users/rohhithg/Desktop/MYSELF/MyProject/DataFlow_project/dataset'
os.makedirs(output_dir, exist_ok=True)

for domain, df in datasets.items():
    filepath = os.path.join(output_dir, f'{domain}.csv')
    df.to_csv(filepath, index=False)
    print(f'✓ {domain}.csv ({len(df)} rows)')

print(f'\nAll datasets generated in {output_dir}')
