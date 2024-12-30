from data_fetcher import fetch_player_data
from utils import normalize_data
import pandas as pd
import numpy as np

# --- Default Swing Weights ---
DEFAULT_WEIGHTS = {
    'Stature': 0,       # Initially set to 0
    'Athleticism': 0,   # Initially set to 0
    'Usage': 15,
    'Creation/Passing': 25,
    'Rebounding': 10,
    'Defense': 25,
    'Shooting': 15,
    'Clutch': 10
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
    player_data = []
    for player, stats in player_stats.items():
        player_record = {}
        player_record['name'] = player
        player_record.update(stats)
        
        try:
            player_record['Offensive Load'] = calculate_offensive_load(stats)
            player_record['Box Creation'] = calculate_box_creation(stats)
            player_record['Pomeroy Assist Ratio'] = calculate_pomeroy_assist_ratio(stats)
            player_record['Defensive Crafted Plus Minus'] = calculate_defensive_crafted_pm(stats)
            player_record['Shooting Quality'] = calculate_shooting_quality(stats)
            player_record['Clutch'] = calculate_clutch(stats)
        except Exception as e:
            print(f"Error calculating advanced stats for {player}: {e}")
            continue
        
        player_data.append(player_record)

    df = pd.DataFrame(player_data)
    
    normalized_df = normalize_data(df)

    # 3. Calculate Overall MVP Score
    normalized_df['MVP Score'] = (
        weights['Usage'] * normalized_df['Usage'] +
        weights['Creation/Passing'] * normalized_df['Creation/Passing'] +
        weights['Rebounding'] * normalized_df['Rebounding'] +
        weights['Defense'] * normalized_df['Defense'] +
        weights['Shooting'] * normalized_df['Shooting'] +
        weights['Clutch'] * normalized_df['Clutch']
    ) / sum(weights.values()) if sum(weights.values()) > 0 else 0

    # 4. Rank Players
    mvp_rankings = normalized_df[['name', 'MVP Score']].sort_values(by='MVP Score', ascending=False).to_dict('records')

    return mvp_rankings

# --- Helper Calculation Functions ---
def calculate_box_creation(stats):
    """Calculates Box Creation."""
    three_point_proficiency = (2 / (1 + np.exp(-stats['3PA']))) * stats['3P%']
    return stats['AST'] * 0.1843 + (stats['PTS'] + stats['TOV']) * 0.0969 - 2.3021 * three_point_proficiency + 0.0582 * (stats['AST'] * (stats['PTS'] + stats['TOV']) * three_point_proficiency) - 1.1942


def calculate_offensive_load(stats):
    """Calculates Offensive Load."""
    box_creation = calculate_box_creation(stats)
    return ((stats['AST'] - (0.38 * box_creation)) * 0.75) + stats['FGA'] + stats['FTA'] * 0.44 + box_creation + stats['TOV']


def calculate_pomeroy_assist_ratio(stats):
    """Calculates Pomeroy Assist Ratio."""
    return stats['AST'] / (((stats['MP'] / (stats['TmMP'] / 5)) * stats['TmFG']) - stats['FG'])

def calculate_defensive_crafted_pm(stats):
    """Calculates Defensive Crafted Plus/Minus."""
    try:
        ddarko = stats['DDARKO']
    except Exception as e:
        print("Issue with DDARKO value")
        ddarko = 0
    try:
        dlebron = stats['DLEBRON']
    except Exception as e:
        print("Issue with DLEBRON value")
        dlebron = 0
    try:
        ddrip = stats['DDRIP']
    except Exception as e:
        print("Issue with DDRIP value")
        ddrip = 0
    try:
        dbpm = stats['DBPM']
    except Exception as e:
        print("Issue with DBPM value")
        dbpm = 0
    try:
        dla3rapm = stats['DLA3RAPM']
    except Exception as e:
        print("Issue with DLA3RAPM value")
        dla3rapm = 0
    return ((ddarko * 2) + dlebron + ddrip + (dbpm / 2) + (dla3rapm * 2)) / 6.5

def calculate_shooting_quality(stats):
    """Calculates Shooting Quality."""
    try:
        spacing = stats['Spacing']
    except Exception as e:
        print("Issue with Spacing value")
        spacing = 0
    try:
        ft_percent = stats['FT%']
    except Exception as e:
        print("Issue with FT% value")
        ft_percent = 0
    try:
        three_p_percent = stats['3P%']
    except Exception as e:
        print("Issue with 3P% value")
        three_p_percent = 0
    return ((spacing * 2) + ((ft_percent + three_p_percent) * 5)) / 7

def calculate_clutch(stats):
    """
    Calculates a standardized 'Clutch' stat.

    Compares a player's effective FG% and plus/minus in clutch situations
    to their overall performance and returns a single standardized value.
    """
    # Example placeholder logic (you'll need to refine this based on your data)
    # This is a very simplistic example and should be improved with better logic.
    clutch_fg_improvement = stats.get('Clutch eFG%', 0) - stats.get('eFG%', 0)
    clutch_pm_improvement = stats.get('Clutch +/-', 0) - stats.get('+/-', 0)

    # Normalize the improvements (this is a placeholder, adjust as needed)
    # You might want to use standard deviation or other normalization techniques.
    normalized_fg_improvement = clutch_fg_improvement / 0.1  # Example scaling
    normalized_pm_improvement = clutch_pm_improvement / 5    # Example scaling

    # Combine the normalized values into a single 'Clutch' stat
    clutch_stat = (normalized_fg_improvement + normalized_pm_improvement) / 2

    return clutch_stat