import pandas as pd


DOMAIN_CONFIG = {
    'network': {
        'column_aliases': ['bandwidth', 'throughput', 'packets', 'data_rate', 'usage'],
        'explanation': 'Network domain: monitoring bandwidth usage, throughput, and packet flow.'
    },
    'server': {
        'column_aliases': ['cpu', 'memory', 'requests', 'load', 'data_rate', 'usage'],
        'explanation': 'Server domain: monitoring CPU usage, memory consumption, and request load.'
    },
    'generic': {
        'column_aliases': ['data_rate', 'usage', 'value', 'metric'],
        'explanation': 'Generic domain: monitoring generic data flow without domain-specific context.'
    }
}

# Map frontend domain names to column mapping for pipeline
FRONTEND_DOMAIN_MAPPING = {
    'network_traffic': {
        'numeric_column': 'bytes_transferred',
        'map_to': 'data_rate',
        'alternative_columns': ['throughput', 'bandwidth', 'packets']
    },
    'server_logs': {
        'numeric_column': 'response_time',
        'map_to': 'data_rate',
        'alternative_columns': ['latency', 'duration', 'time_ms']
    },
    'system_metrics': {
        'numeric_column': 'cpu_usage',
        'map_to': 'data_rate',
        'alternative_columns': ['memory_usage', 'disk_usage', 'network_io']
    },
    'finance_transactions': {
        'numeric_column': 'amount',
        'map_to': 'data_rate',
        'alternative_columns': ['value', 'price', 'cost']
    },
    'user_activity': {
        'numeric_column': 'duration',
        'map_to': 'data_rate',
        'alternative_columns': ['time_spent', 'engagement']
    },
    'iot_sensor': {
        'numeric_column': 'value',
        'map_to': 'data_rate',
        'alternative_columns': ['measurement', 'reading']
    },
    'web_traffic': {
        'numeric_column': 'visitor_count',
        'map_to': 'data_rate',
        'alternative_columns': ['page_views', 'requests', 'clicks']
    },
    'api_logs': {
        'numeric_column': 'latency',
        'map_to': 'data_rate',
        'alternative_columns': ['response_time', 'duration']
    },
    'application_logs': {
        'numeric_column': None,
        'map_to': 'data_rate',
        'alternative_columns': []
    },
    'generic': {
        'numeric_column': None,
        'map_to': None,
        'alternative_columns': []
    }
}


def apply_column_mapping(df, domain):
    """
    Apply column mapping for a specific domain.
    Maps domain-specific numeric columns to 'data_rate' for pipeline processing.
    
    Args:
        df (pd.DataFrame): Input dataframe
        domain (str): Frontend domain name
    
    Returns:
        tuple: (df, numeric_column_found)
            - df: modified dataframe with 'data_rate' column
            - numeric_column_found: the name of the column that was mapped
    """
    if domain not in FRONTEND_DOMAIN_MAPPING:
        return df, None
    
    if domain == 'generic':
        return df, None
    
    mapping = FRONTEND_DOMAIN_MAPPING[domain]
    numeric_col = mapping.get('numeric_column')
    alternatives = mapping.get('alternative_columns', [])
    
    if not numeric_col:
        return df, None
    
    # Try primary numeric column first
    if numeric_col in df.columns:
        df_copy = df.copy()
        df_copy['data_rate'] = pd.to_numeric(df_copy[numeric_col], errors='coerce').fillna(0)
        return df_copy, numeric_col
    
    # Try alternative columns
    for alt_col in alternatives:
        if alt_col in df.columns:
            df_copy = df.copy()
            df_copy['data_rate'] = pd.to_numeric(df_copy[alt_col], errors='coerce').fillna(0)
            return df_copy, alt_col
    
    # No numeric column found, return unchanged
    return df, None


def map_domain_to_dataframe(domain, dataframe):
    """
    Maps user-selected domain to dataset interpretation.
    
    Standardizes the dataframe by renaming the relevant metric column to 'data_rate'.
    
    Args:
        domain (str): One of 'network', 'server', or 'generic'
        dataframe (pd.DataFrame): Input dataframe with metric columns
    
    Returns:
        dict: {
            'valid': bool,
            'reason': str (error message if invalid),
            'dataframe': pd.DataFrame (standardized, with column renamed to 'data_rate'),
            'explanation': str (domain interpretation)
        }
    """
    result = {
        'valid': False,
        'reason': '',
        'dataframe': None,
        'explanation': ''
    }

    # Validate domain
    domain_lower = domain.lower() if isinstance(domain, str) else ''
    if domain_lower not in DOMAIN_CONFIG:
        valid_domains = ', '.join(DOMAIN_CONFIG.keys())
        result['reason'] = f"Unknown domain: {domain}. Supported domains: {valid_domains}"
        return result

    # Validate dataframe
    if not isinstance(dataframe, pd.DataFrame):
        result['reason'] = "Input must be a pandas DataFrame"
        return result

    if dataframe.empty:
        result['reason'] = "DataFrame is empty"
        return result

    # Get domain config
    config = DOMAIN_CONFIG[domain_lower]
    column_aliases = config['column_aliases']
    explanation = config['explanation']

    # Find matching column in dataframe
    matched_column = None
    df_columns_lower = {col.lower(): col for col in dataframe.columns}

    for alias in column_aliases:
        if alias.lower() in df_columns_lower:
            matched_column = df_columns_lower[alias.lower()]
            break

    if matched_column is None:
        available = ', '.join(dataframe.columns)
        result['reason'] = f"No matching metric column found for {domain_lower} domain. Available columns: {available}"
        return result

    # Create a copy and rename the column to 'data_rate'
    result_df = dataframe.copy()

    if matched_column != 'data_rate':
        result_df = result_df.rename(columns={matched_column: 'data_rate'})

    # Success
    result['valid'] = True
    result['reason'] = ''
    result['dataframe'] = result_df
    result['explanation'] = explanation

    return result

