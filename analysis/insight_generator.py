def _fmt(value):
    try:
        return f"{float(value):.2f}"
    except Exception:
        return "0.00"


def generate_insights(spikes, drops, anomalies, trend="stable", distribution=None):
    insights = []

    # Backward compatibility for older callers that pass non-event arguments.
    spikes = spikes if isinstance(spikes, list) else []
    drops = drops if isinstance(drops, list) else []
    anomalies = anomalies if isinstance(anomalies, list) else []
    distribution = distribution if isinstance(distribution, dict) else {}

    if spikes:
        max_spike = max((s.get("data_rate", 0) for s in spikes), default=0)
        insights.append(
            f"{len(spikes)} spikes detected with maximum value {_fmt(max_spike)}, indicating high load variation."
        )

    if drops:
        min_drop = min((d.get("data_rate", 0) for d in drops), default=0)
        insights.append(
            f"{len(drops)} drops detected with minimum value {_fmt(min_drop)}, indicating possible interruption periods."
        )

    if anomalies:
        max_anomaly = max((a.get("data_rate", 0) for a in anomalies), default=0)
        insights.append(
            f"{len(anomalies)} anomalies detected with peak anomaly value {_fmt(max_anomaly)}, indicating irregular behavior."
        )

    mean_value = distribution.get("mean", 0)
    variance = distribution.get("variance", 0)
    insights.append(
        f"Average data rate is {_fmt(mean_value)} with variance {_fmt(variance)}."
    )

    if trend == "increasing":
        insights.append("Trend is increasing, which suggests system risk is growing over time.")
    elif trend == "decreasing":
        insights.append("Trend is decreasing, which suggests gradual improvement in load behavior.")
    else:
        insights.append("Trend is stable, indicating consistent behavior without long-term drift.")

    return insights
