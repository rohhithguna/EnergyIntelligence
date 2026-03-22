import json

import numpy as np
import pandas as pd

from analysis.insight_generator import generate_insights
from analysis.quality_engine import compute_quality_score
from analysis.recommendation_engine import generate_recommendations
from core.anomaly_engine import detect_anomalies
from core.pattern_spike_engine import run_core_engine
from core.risk_engine import compute_risk
from core.trend_engine import detect_trend
from data.loader import load_data
from data.preprocessor import preprocess_data
from data.validator import validate_file


def _event_records(df, indices):
    events = []
    for idx in indices:
        if idx < 0 or idx >= len(df):
            continue
        row = df.iloc[idx]
        events.append({
            "index": int(idx),
            "time": str(row["time"]),
            "data_rate": float(row["data_rate"]),
        })
    return events


def validate_data(file_path):
    return validate_file(file_path)


def _hour_bucket(ts):
    try:
        return pd.to_datetime(ts).strftime("%I:00 %p")
    except Exception:
        return "unknown"


def _top_window(events):
    if not events:
        return "No notable event window detected."
    buckets = {}
    for event in events:
        bucket = _hour_bucket(event.get("time"))
        buckets[bucket] = buckets.get(bucket, 0) + 1
    hour, count = sorted(buckets.items(), key=lambda x: (-x[1], x[0]))[0]
    return f"Most events occur around {hour} with {count} occurrences."


def _drop_clusters(drops):
    if not drops:
        return []
    idx = sorted(int(d["index"]) for d in drops)
    clusters = []
    start = idx[0]
    prev = idx[0]
    for item in idx[1:]:
        if item == prev + 1:
            prev = item
            continue
        clusters.append({"start_index": start, "end_index": prev, "count": (prev - start + 1)})
        start = item
        prev = item
    clusters.append({"start_index": start, "end_index": prev, "count": (prev - start + 1)})
    return clusters


def _distribution(df):
    arr = pd.to_numeric(df["data_rate"], errors="coerce").fillna(0).to_numpy(dtype=float)
    return {
        "mean": round(float(np.mean(arr)) if len(arr) else 0.0, 4),
        "median": round(float(np.median(arr)) if len(arr) else 0.0, 4),
        "variance": round(float(np.var(arr)) if len(arr) else 0.0, 4),
    }


def _confidence_score(quality_score, records, variance):
    quality_part = max(0.0, min(100.0, float(quality_score))) * 0.6
    records_part = min(100.0, (float(records) / 1000.0) * 100.0) * 0.25
    noise_penalty = min(100.0, float(variance) / 10.0)
    noise_part = max(0.0, 100.0 - noise_penalty) * 0.15
    score = int(max(0, min(100, round(quality_part + records_part + noise_part))))

    if score >= 80:
        level = "high"
        reason = "based on consistent data and low noise"
    elif score >= 55:
        level = "medium"
        reason = "based on moderate quality and acceptable noise"
    else:
        level = "low"
        reason = "based on limited records or noisy data"

    return {
        "score": score,
        "level": level,
        "text": f"Confidence: {level.capitalize()} ({reason})",
    }


def _severity(item, kind, mean, std):
    value = float(item.get("data_rate", 0.0))
    if kind == "drop":
        deviation = (mean - value) / std if std > 0 else 0.0
    else:
        deviation = (value - mean) / std if std > 0 else 0.0

    if deviation >= 2.5:
        return "severe"
    if deviation >= 1.2:
        return "moderate"
    return "minor"


def _apply_event_severity(spikes, drops, anomalies, mean, std):
    for item in spikes:
        item["type"] = "spike"
        item["severity"] = _severity(item, "spike", mean, std)
    for item in drops:
        item["type"] = "drop"
        item["severity"] = _severity(item, "drop", mean, std)
    for item in anomalies:
        item["type"] = "anomaly"
        item["severity"] = _severity(item, "spike", mean, std)


def _root_cause_hints(spikes, drops, anomalies):
    hints = []
    if spikes:
        hints.append("Frequent spikes suggest system overload during peak intervals.")
    if drops:
        hints.append("Drop clusters suggest possible service interruption windows.")
    if anomalies:
        hints.append("Anomalies suggest irregular system behavior that needs log inspection.")
    if not hints:
        hints.append("No major root-cause signals detected in current data.")
    return hints


def _trend_interpretation(trend):
    if trend == "increasing":
        return "Trend is increasing, indicating risk is growing over time."
    if trend == "decreasing":
        return "Trend is decreasing, indicating improving system behavior."
    return "Trend is stable, indicating no long-term increase in system load."


def _time_based_analysis(spikes, drops):
    spike_window = _top_window(spikes)
    drop_window = _top_window(drops)
    return {
        "peak_time_interval": spike_window,
        "frequent_spike_period": spike_window,
        "drop_clusters": _drop_clusters(drops),
        "drop_cluster_summary": drop_window,
    }


def run_pipeline(file_path):
    """
    Execute full analytics pipeline with comprehensive error handling.
    Returns structured output with error information if pipeline fails.
    """
    try:
        validation = validate_data(file_path)
        if not validation["valid"]:
            raise ValueError(validation["reason"])

        df = load_data(file_path)
        df = preprocess_data(df)

        df, spikes, drops = run_core_engine(df)
        df, anomalies_df = detect_anomalies(df)

        trend, trend_slope = detect_trend(df)
        risk = compute_risk(len(spikes), len(drops), len(anomalies_df))
        quality = compute_quality_score(df, anomalies_count=len(anomalies_df))

        spikes_events = _event_records(df, spikes)
        drops_events = _event_records(df, drops)
        anomalies_events = anomalies_df[["time", "data_rate"]].assign(
            time=lambda x: x["time"].astype(str),
            data_rate=lambda x: x["data_rate"].astype(float),
        ).to_dict(orient="records")

        dist = _distribution(df)
        std = float(np.sqrt(max(dist["variance"], 0.0)))
        _apply_event_severity(spikes_events, drops_events, anomalies_events, dist["mean"], std)

        time_analysis = _time_based_analysis(spikes_events, drops_events)
        confidence = _confidence_score(quality["score"], len(df), dist["variance"])
        root_cause_hints = _root_cause_hints(spikes_events, drops_events, anomalies_events)
        trend_text = _trend_interpretation(str(trend).lower())

        insights = generate_insights(spikes_events, drops_events, anomalies_events, str(trend).lower(), dist)
        recommendations = generate_recommendations(
            len(spikes), len(drops), len(anomalies_df), risk["level"]
        )

        risk_level = str(risk["level"]).lower()

        result = {
            "spikes": spikes_events,
            "drops": drops_events,
            "anomalies": anomalies_events,
            "trend": str(trend).lower(),
            "trend_slope": round(float(trend_slope), 6),
            "trend_interpretation": trend_text,
            "risk": risk_level,
            "risk_score": int(risk["score"]),
            "risk_justification": (
                f"Risk is {risk_level} due to {len(spikes_events)} spikes, {len(drops_events)} drops, and {len(anomalies_events)} anomalies."
            ),
            "quality": int(quality["score"]),
            "quality_details": quality,
            "confidence": confidence,
            "distribution": dist,
            "root_cause_hints": root_cause_hints,
            "time_analysis": time_analysis,
            "system_stability": "unstable" if risk_level == "high" else "stable",
            "insights": insights,
            "recommendations": recommendations,
            "counts": {
                "spikes": len(spikes),
                "drops": len(drops),
                "anomalies": len(anomalies_df),
            },
            "series": {
                "time": df["time"].astype(str).tolist(),
                "data_rate": df["data_rate"].astype(float).tolist(),
            },
        }
        return result
    
    except Exception as e:
        # Return structured error response
        return {
            "error": str(e),
            "status": "error",
            "spikes": [],
            "drops": [],
            "anomalies": [],
            "insights": [f"Error during analysis: {str(e)}"],
            "recommendations": ["Please check your data format and try again"],
            "counts": {"spikes": 0, "drops": 0, "anomalies": 0},
        }


if __name__ == "__main__":
    output = run_pipeline("dataset/sample_data.csv")
    print(json.dumps(output, indent=2))
