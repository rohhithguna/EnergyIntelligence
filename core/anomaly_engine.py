from sklearn.ensemble import IsolationForest


def detect_anomalies(df, contamination=0.05):
    out = df.copy(deep=True)
    model = IsolationForest(contamination=contamination, random_state=42)
    out["anomaly"] = model.fit_predict(out[["data_rate"]])
    anomalies = out[out["anomaly"] == -1]
    return out, anomalies
