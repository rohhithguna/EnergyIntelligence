from data.loader import load_data
from data.preprocessor import preprocess_data

from core.pattern_spike_engine import run_core_engine
from core.anomaly_engine import detect_anomalies

from analysis.correlation import compute_correlation
from analysis.insight_generator import generate_insights

import matplotlib.pyplot as plt


def main():
    # Step 1: Load data
    df = load_data("sample_data.csv")

    # Step 2: Preprocess data
    df = preprocess_data(df)

    # Step 3: Detect patterns + spikes + drops
    df, spikes, drops = run_core_engine(df)

    # Step 4: Detect anomalies
    df, anomalies = detect_anomalies(df)

    # Step 5: Correlation analysis
    correlation_matrix = compute_correlation(df)

    # Step 6: Generate insights
    insights = generate_insights(spikes, drops, anomalies, correlation_matrix)

    # ================= OUTPUT =================

    print("\n========== FINAL INSIGHTS ==========")
    for i in insights:
        print("•", i)

    print("\n========== SPIKES (index positions) ==========")
    print(spikes)

    print("\n========== DROPS (index positions) ==========")
    print(drops)

    print("\n========== ANOMALIES (sample) ==========")
    if len(anomalies) > 0:
        print(anomalies[['time', 'data_rate']].head(10))
    else:
        print("No anomalies detected")

    print("\n========== CORRELATION MATRIX ==========")
    print(correlation_matrix)

    # ================= VISUALIZATION =================

    plt.figure()
    plt.plot(df['time'], df['data_rate'], label="Data Rate")

    # mark spikes
    plt.scatter(df.loc[spikes, 'time'], df.loc[spikes, 'data_rate'], label="Spikes")

    # mark drops
    plt.scatter(df.loc[drops, 'time'], df.loc[drops, 'data_rate'], label="Drops")

    # mark anomalies
    if len(anomalies) > 0:
        plt.scatter(anomalies['time'], anomalies['data_rate'], label="Anomalies")

    plt.title("Data Flow Monitoring System")
    plt.xlabel("Time")
    plt.ylabel("Data Rate")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
