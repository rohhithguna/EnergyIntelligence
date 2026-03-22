import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def detect_patterns(df):
    out = df.copy(deep=True)
    values = pd.to_numeric(out["data_rate"], errors="coerce").fillna(0).to_numpy().reshape(-1, 1)

    k = 3 if len(out) >= 3 else max(1, len(out))
    if k == 1:
        out["pattern"] = "medium"
        return out

    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(values)

    centers = model.cluster_centers_.flatten()
    order = np.argsort(centers)
    names = ["low", "medium", "high"][:k]
    mapping = {int(cluster): names[pos] for pos, cluster in enumerate(order)}
    out["pattern"] = pd.Series(labels, index=out.index).map(mapping)
    return out


def detect_spikes_drops(df):
    out = df.copy(deep=True)
    out["moving_avg"] = out["data_rate"].rolling(window=3, min_periods=1).mean()
    spikes = out.index[out["data_rate"] > (out["moving_avg"] * 1.5)].tolist()
    drops = out.index[out["data_rate"] < (out["moving_avg"] * 0.5)].tolist()
    return out, spikes, drops


def run_core_engine(df):
    out = detect_patterns(df)
    out, spikes, drops = detect_spikes_drops(out)
    return out, spikes, drops
