import numpy as np
from sklearn.linear_model import LinearRegression


def detect_trend(df):
    if len(df) < 2:
        return "stable", 0.0

    x = np.arange(len(df)).reshape(-1, 1)
    y = df["data_rate"].to_numpy(dtype=float)

    model = LinearRegression()
    model.fit(x, y)
    slope = float(model.coef_[0])

    if slope > 0.05:
        return "increasing", slope
    if slope < -0.05:
        return "decreasing", slope
    return "stable", slope
