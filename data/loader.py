import os

import pandas as pd


def load_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path)
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    raise ValueError(f"Unsupported file format: {ext}")
