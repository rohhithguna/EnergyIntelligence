from EnergyIntelligence.data.loader import load_data
from EnergyIntelligence.data.preprocessor import preprocess_data

from EnergyIntelligence.core.pattern_spike_engine import run_core_engine
from EnergyIntelligence.core.anomaly_engine import detect_anomalies

from EnergyIntelligence.analysis.correlation import compute_correlation
from EnergyIntelligence.analysis.insight_generator import generate_insights


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


print("\n---- FINAL INSIGHTS ----")
for i in insights:
    print(i)
