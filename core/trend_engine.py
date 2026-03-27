import numpy as np


def detect_trend(df):
    if len(df) < 2:
        return "stable", 0.0

    y = df["data_rate"].to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)

    denom = float(np.sum(x_centered ** 2))
    slope = 0.0 if denom == 0 else float(np.sum(x_centered * y_centered) / denom)

    if slope > 0.05:
        return "increasing", slope
    if slope < -0.05:
        return "decreasing", slope
    return "stable", slope
