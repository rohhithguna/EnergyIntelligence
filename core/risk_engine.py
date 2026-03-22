def compute_risk(spikes_count, drops_count, anomalies_count):
    score = (spikes_count * 2) + (drops_count * 3) + (anomalies_count * 4)

    if score < 15:
        level = "LOW"
    elif score < 40:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {"score": int(score), "level": level}
