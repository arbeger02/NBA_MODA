from .data_fetcher import fetch_player_data
from .utils import polynomial_return_to_scale
from .config import get_league_efg
import pandas as pd
import numpy as np

# --- Default Swing Weights ---
DEFAULT_WEIGHTS = {
    'Height': 0,
    'Wingspan': 0,
    'Weight': 0,
    'Max_Vertical_Leap': 0,
    'Offensive_Load': 20,
    'Usage%': 20,
    'Box_Creation': 15,
    'pAST%': 15,
    'ORB%': 10,
    'DRB%': 10,
    'DBPM': 20,
    'DWS': 20,
    'Shooting_Proficiency': 15,
    'Spacing': 15,
    'Clutch': 5
}

# --- Default Polynomial Degrees for Return-to-Scale ---
POLYNOMIAL_DEGREES = {
    'Height': 2,
    'Wingspan': 2,
    'Weight': 2,
    'Max_Vertical_Leap': 2,
    'Offensive_Load': 2,
    'Usage%': 2,
    'Box_Creation': 2,
    'pAST%': 2,
    'ORB%': 2,
    'DRB%': 2,
    'DBPM': 2,
    'DWS': 2,
    'Shooting_Proficiency': 2,
    'Spacing': 2,
    'Clutch': 2
}

def calculate_mvp_rankings(weights=None):
    """
    Calculates MVP rankings using the MODA model.

    Args:
        weights (dict): Optional dictionary of weights for each objective.

    Returns:
        list: List of dictionaries, each containing player name and MVP score.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # 1. Fetch Data
    player_stats = fetch_player_data()

    # 2. Calculate Advanced Stats and Value Scores
    df = calculate_advanced_stats(player_stats)

    # --- Create 'Ideal' row ---
    if 'name' in df.columns:
        ideal_row = pd.DataFrame([['Ideal'] + [df[col].max() for col in df.columns if col != 'name']], columns=df.columns)
        df = pd.concat([df, ideal_row], ignore_index=True)

    # --- Filter columns ---
    df_filtered = df.copy()
    columns_to_keep = list(DEFAULT_WEIGHTS.keys())
    try:
        df_filtered = df_filtered[columns_to_keep]
    except KeyError as e:
        print(f"Warning: One or more columns from DEFAULT_WEIGHTS not found in DataFrame: {e}")
        existing_columns = [col for col in columns_to_keep if col in df_filtered.columns]
        df_filtered = df_filtered[existing_columns]

    # --- Apply Return-to-Scale ---
    scaled_values = {}
    for name in df_filtered.columns:
        if name in POLYNOMIAL_DEGREES:
            # Ensure numeric values, converting non-numeric values to NaN
            numeric_values = pd.to_numeric(df_filtered[name], errors='coerce').fillna(0)

            scaled_values[name] = polynomial_return_to_scale(
                numeric_values.tolist(),
                degree=POLYNOMIAL_DEGREES.get(name, 1),
                normal_scaling=(numeric_values.mean() >= 0)
            )

    # Create a new DataFrame with scaled values
    df_scaled = pd.DataFrame(scaled_values)

    # Concatenate player names (if available) with the scaled data
    if 'name' in df.columns:
        df_scaled = pd.concat([df['name'].reset_index(drop=True), df_scaled], axis=1)

    # --- Calculate Overall MVP Score ---
    df_scaled['MVP Score'] = 0
    for name, weight in weights.items():
        if name in df_scaled.columns:
            df_scaled['MVP Score'] += weight * df_scaled[name]

    # Rank Players (excluding 'Ideal')
    mvp_rankings = df_scaled[df_scaled['name'] != 'Ideal'][['name', 'MVP Score']].sort_values(by='MVP Score', ascending=False).to_dict('records')

    return mvp_rankings

# --- Helper Calculation Functions ---
def calculate_box_creation(stats):
    """Calculates Box Creation."""
    shooting_proficiency = calculate_shooting_proficiency(stats)
    return (stats['AST']/stats['GP']) * 0.1843 + ((stats['PTS']/stats['GP']) + (stats['TOV']/stats['GP'])) * 0.0969 - 2.3021 * shooting_proficiency + 0.0582 * ((stats['AST']/stats['GP']) * ((stats['PTS']/stats['GP']) + (stats['TOV']/stats['GP'])) * shooting_proficiency) - 1.1942

def calculate_offensive_load(stats):
    """Calculates Offensive Load."""
    box_creation = calculate_box_creation(stats)
    return (((stats['AST']/stats['GP']) - (0.38 * box_creation)) * 0.75) + (stats['FGA']/stats['GP']) + (stats['FTA']/stats['GP']) * 0.44 + box_creation + (stats['TOV']/stats['GP'])

def calculate_shooting_proficiency(stats):
    """
    Calculates 3-Point Proficiency using data from the stats dictionary.

    Formula:
    (2 / (1 + EXP(-3PA))) * 3P%
    """
    return (2 / (1 + np.exp(-stats['3PAper100']))) * stats['3P%']

def calculate_spacing(stats):
    """
    Calculates Spacing.

    Spacing = (3PA * (3P% * 1.5)) - League Average eFG%
    """
    league_efg = get_league_efg()  # Get eFG from config.py

    if league_efg is None:
        print("Warning: League eFG% not available. Using 0 for spacing calculation.")
        league_efg = 0

    spacing = (stats['3PAper100'] * (stats['3P%'] * 1.5)) - league_efg
    return spacing

def calculate_clutch_ts_percentage(stats):
    """
    Calculates Clutch True Shooting Percentage (TS%) using data from the stats dictionary.

    Formula:
    TS% = 0.5 * (Total Points) / [(Total Field Goal Attempts) + 0.44 * (Total Free Throw Attempts)]
    """
    clutch_pts = stats['Clutch_PTS']
    clutch_fga = stats['Clutch_FGA']
    clutch_fta = stats['Clutch_FTA']

    # Handle cases where FGA or FTA are zero to avoid division by zero
    if clutch_fga + 0.44 * clutch_fta == 0:
        return 0

    ts_percentage = 0.5 * clutch_pts / (clutch_fga + 0.44 * clutch_fta)
    return ts_percentage
    
def calculate_clutch(stats):
    """
    Calculates a 'Clutch' stat.

    Compares a player's effective TS% in clutch situations
    to their overall performance and returns a single standardized value.
    """
    TS = stats['TS%']
    Clutch_TS = calculate_clutch_ts_percentage(stats)

    clutch_stat = Clutch_TS - TS

    return clutch_stat

def calculate_advanced_stats(player_stats):
    player_data = []

    for player, stats in player_stats.items():
        player_record = {}
        player_record['name'] = player
        player_record.update(stats)
        
        try:
            player_record['Offensive_Load'] = calculate_offensive_load(stats)
            player_record['Box_Creation'] = calculate_box_creation(stats)
            player_record['Shooting_Proficiency'] = calculate_shooting_proficiency(stats)
            player_record['Spacing'] = calculate_spacing(stats)
            player_record['Clutch'] = calculate_clutch(stats)
        except Exception as e:
            print(f"Error calculating advanced stats for {player}: {e}")
            continue
        
        player_data.append(player_record)

    df = pd.DataFrame(player_data)

    return df