import pandas as pd


def preprocess_data(df):
    out = df.copy(deep=True)
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]

    if "data_rate" not in out.columns and "usage" in out.columns:
        out = out.rename(columns={"usage": "data_rate"})

    time_col = None
    for c in ["time", "timestamp", "datetime", "event_time", "date"]:
        if c in out.columns:
            time_col = c
            break

    if time_col is None:
        raise ValueError("No valid time column found")

    out = out.rename(columns={time_col: "time"})
    out["time"] = pd.to_datetime(out["time"], errors="coerce")
    out["data_rate"] = pd.to_numeric(out["data_rate"], errors="coerce")

    out = out.dropna(subset=["time"])
    out = out.sort_values("time")
    out["data_rate"] = out["data_rate"].ffill().bfill()
    out = out.dropna(subset=["data_rate"])
    out = out.drop_duplicates(subset=["time"])
    out = out.reset_index(drop=True)
    return out
