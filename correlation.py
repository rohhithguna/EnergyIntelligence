# analysis/correlation.py

def compute_correlation(df):
    """
    Compute correlation matrix
    :param df: DataFrame
    :return: correlation matrix
    """

    correlation_matrix = df.corr(numeric_only=True)

    return correlation_matrix