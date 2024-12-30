import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def normalize_data(df):
    """
    Normalizes specified columns of the DataFrame to a 0-1 range.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with normalized columns.
    """
    scaler = MinMaxScaler()
    
    # Columns to normalize - Add or remove columns as needed for your analysis
    cols_to_normalize = [
        'Usage %', 'Offensive Load', 'Box Creation', 'Pomeroy Assist Ratio',
        'ORB%', 'DRB%', 'Defensive Crafted Plus Minus',
        'Shooting Quality', 'Clutch'
    ]

    # Create copies of the columns to be normalized
    for col in cols_to_normalize:
        df[col + '_normalized'] = df[col]

    # Apply normalization
    df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])

    # Rename the normalized columns for clarity
    df = df.rename(columns={
        'Usage %': 'Usage',
        'Offensive Load_normalized': 'Offensive Load',
        'Box Creation_normalized': 'Box Creation',
        'Pomeroy Assist Ratio_normalized': 'Pomeroy Assist Ratio',
        'ORB%_normalized': 'ORB%',
        'DRB%_normalized': 'DRB%',
        'Defensive Crafted Plus Minus_normalized': 'Defensive Crafted Plus Minus',
        'Shooting Quality_normalized': 'Shooting Quality',
        'Clutch_normalized': 'Clutch'
    })
    
    df['Creation/Passing'] = (df['Box Creation'] + df['Pomeroy Assist Ratio']) / 2
    df['Rebounding'] = (df['ORB%'] + df['DRB%']) / 2
    df['Defense'] = df['Defensive Crafted Plus Minus']
    df['Shooting'] = df['Shooting Quality']
    
    df.fillna(0, inplace=True)

    return df