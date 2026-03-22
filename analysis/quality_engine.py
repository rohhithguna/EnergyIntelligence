import numpy as np


def compute_quality_score(df, anomalies_count=0):
    total = max(1, len(df))

    missing_pct = float(df["data_rate"].isna().mean() * 100)
    variance = float(np.var(df["data_rate"].fillna(0).to_numpy(dtype=float)))
    anomaly_ratio = float((anomalies_count / total) * 100)

    missing_penalty = min(40, missing_pct * 1.5)
    anomaly_penalty = min(40, anomaly_ratio * 2.0)
    variance_bonus = min(15, np.log1p(max(variance, 0.0)) * 2.0)

    score = int(max(0, min(100, 100 - missing_penalty - anomaly_penalty + variance_bonus)))
    return {
        "score": score,
        "missing_pct": round(missing_pct, 2),
        "variance": round(variance, 4),
        "anomaly_ratio": round(anomaly_ratio, 2),
    }
