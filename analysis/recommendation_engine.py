def generate_recommendations(spikes_count, drops_count, anomalies_count, risk_level):
    recs = []

    if spikes_count >= 3:
        recs.append("Reduce system load or increase capacity during peak intervals.")
    if drops_count >= 2:
        recs.append("Check service health and investigate interruption causes.")
    if anomalies_count >= 2:
        recs.append("Inspect logs and telemetry for irregular events.")

    if risk_level == "HIGH":
        recs.append("Trigger incident response and continuous monitoring.")
    elif risk_level == "MEDIUM":
        recs.append("Schedule preventive checks and threshold tuning.")
    else:
        recs.append("Maintain baseline monitoring and periodic review.")

    return recs
