# analysis/insight_generator.py

def generate_insights(spikes, drops, anomalies, correlation_matrix):
    """
    Generate insights based on detected patterns
    :param spikes: list or dataframe of spikes
    :param drops: list or dataframe of drops
    :param anomalies: dataframe of anomalies
    :param correlation_matrix: correlation matrix
    :return: list of insights
    """

    insights = []

    # Spike insights
    if len(spikes) > 0:
        insights.append("High spikes detected → possible system overload")

    # Drop insights
    if len(drops) > 0:
        insights.append("Sudden drops detected → possible failures or interruptions")

    # Anomaly insights
    if len(anomalies) > 0:
        insights.append(f"{len(anomalies)} anomalies detected → irregular system behavior")

    # Correlation insights (if time column exists)
    if 'time' in correlation_matrix.columns and 'data_rate' in correlation_matrix.columns:
        corr_value = correlation_matrix.loc['time', 'data_rate']

        if corr_value > 0.5:
            insights.append("Data flow increases over time (positive correlation)")
        elif corr_value < -0.5:
            insights.append("Data flow decreases over time (negative correlation)")
        else:
            insights.append("No strong correlation between time and data flow")

    # If no issues
    if not insights:
        insights.append("System appears stable with no major anomalies")

    return insights
