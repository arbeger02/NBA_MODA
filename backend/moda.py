from .data_fetcher import fetch_player_data
from .utils import normalize_data
import pandas as pd
import numpy as np
import config

# --- Default Swing Weights ---
DEFAULT_WEIGHTS = {
    'Height': 0,
    'Wingspan': 0,
    'Weight': 0,
    'Max_Vertical_Leap': 0,
    'Offensive_Load': 0.2,
    'Usage%': 0.2,
    'Box_Creation': 0.15,
    'pAST%': 0.15,
    'ORB%': 0.1,
    'DRB%': 0.1,
    'DBPM': 0.05,
    'DWS': 0.05,
    'Shooting_Proficiency': 0.05,
    'Spacing': 0.05,
    'Clutch': 0.05
}

# --- Default Polynomial Degrees for Return-to-Scale ---
DEFAULT_WEIGHTS = {
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

    # Get the list of column names from DEFAULT_WEIGHTS
    columns_to_keep = list(DEFAULT_WEIGHTS.keys())

    # Add 'name' to the list of columns to keep if you have a name column in df
    if 'name' in df.columns:
        columns_to_keep.append('name')

    # Filter the DataFrame to keep only the desired columns
    try:
        df = df[columns_to_keep]
    except KeyError as e:
        print(f"Warning: One or more columns from DEFAULT_WEIGHTS not found in DataFrame: {e}")
        # Handle the missing columns (e.g., add them with default values or skip them)
        # In this case, we will skip any missing columns
        existing_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[existing_columns]

    return df

# --- Helper Calculation Functions ---
def calculate_box_creation(stats):
    """Calculates Box Creation."""
    shooting_proficiency = calculate_shooting_proficiency(stats)
    return stats['AST'] * 0.1843 + (stats['PTS'] + stats['TOV']) * 0.0969 - 2.3021 * shooting_proficiency + 0.0582 * (stats['AST'] * (stats['PTS'] + stats['TOV']) * shooting_proficiency) - 1.1942


def calculate_offensive_load(stats):
    """Calculates Offensive Load."""
    box_creation = calculate_box_creation(stats)
    return ((stats['AST'] - (0.38 * box_creation)) * 0.75) + stats['FGA'] + stats['FTA'] * 0.44 + box_creation + stats['TOV']

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
    league_efg = config.get_league_efg()  # Get eFG from config.py

    if league_efg is None:
        print("Warning: League eFG% not available. Using 0 for spacing calculation.")
        league_efg = 0

    spacing = (stats['3PA'] * (stats['3P%'] * 1.5)) - league_efg
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