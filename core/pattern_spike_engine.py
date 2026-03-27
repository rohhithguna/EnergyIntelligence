import pandas as pd


def detect_spikes_drops(df):
    out = df.copy(deep=True)
    out["data_rate"] = pd.to_numeric(out["data_rate"], errors="coerce").fillna(0.0)
    out["moving_avg"] = out["data_rate"].rolling(window=5, min_periods=1).mean()
    out["moving_std"] = out["data_rate"].rolling(window=5, min_periods=1).std().fillna(0.0)

    upper = out["moving_avg"] + (out["moving_std"] * 1.2)
    lower = out["moving_avg"] - (out["moving_std"] * 1.2)

    spikes = out.index[out["data_rate"] > upper].tolist()
    drops = out.index[out["data_rate"] < lower].tolist()
    return out, spikes, drops


def run_core_engine(df):
    out, spikes, drops = detect_spikes_drops(df)
    return out, spikes, drops
