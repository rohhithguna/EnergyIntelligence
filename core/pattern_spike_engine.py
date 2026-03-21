import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def _get_target_col(df: pd.DataFrame) -> str:
    """Return the supported target column name."""
    if "data_rate" in df.columns:
        return "data_rate"
    if "usage" in df.columns:
        return "usage"
    raise ValueError("Input DataFrame must contain 'data_rate' or 'usage' column.")


def detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Cluster flow values into low/medium/high pattern labels."""
    out = df.copy(deep=True)
    col = _get_target_col(out)
    out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    n = len(out)
    if n == 0:
        out["cluster"] = pd.Series(index=out.index, dtype="object")
        return out

    vals = out[[col]].to_numpy()
    unique_count = int(pd.Series(vals.ravel()).nunique(dropna=True))
    k = max(1, min(3, n, unique_count))

    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(vals)

    centers = model.cluster_centers_.ravel()
    order = np.argsort(centers)
    names = ["low flow", "medium flow", "high flow"][:k]
    label_map = {int(cluster_id): names[pos] for pos, cluster_id in enumerate(order)}

    out["cluster"] = pd.Series(labels, index=out.index).map(label_map)
    return out


def detect_spikes_and_drops(df: pd.DataFrame):
    """Add moving average and return spike/drop index lists."""
    col = _get_target_col(df)

    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["moving_avg"] = df[col].rolling(window=3, min_periods=1).mean()

    v = df[col].to_numpy(dtype=float)
    m = df["moving_avg"].to_numpy(dtype=float)
    valid = m > 0

    spike_mask = valid & (v > (m * 1.5))
    drop_mask = valid & (v < (m * 0.5))

    spikes = df.index[spike_mask].tolist()
    drops = df.index[drop_mask].tolist()

    return spikes, drops


def run_core_engine(df: pd.DataFrame):
    """Run core pattern and disruption detection pipeline."""
    out = detect_patterns(df)
    spikes, drops = detect_spikes_and_drops(out)
    return out, spikes, drops
