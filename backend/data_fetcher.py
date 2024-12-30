from nba_api.stats.static import players
from nba_api.stats.endpoints import playerdashboardbyyearoveryear, commonplayerinfo, leaguedashplayerstats, playerdashboardbyclutch, leaguedashplayerptshot
from nba_api.stats.library.parameters import SeasonTypeAllStar
import time
import pandas as pd

def fetch_player_data():
    """
    Fetches player data from the NBA API.

    Returns:
        dict: A dictionary where keys are player names and values are dictionaries of stats.
    """
    player_dict = players.get_active_players()
    all_player_stats = {}

    # Get current season
    current_season = leaguedashplayerstats.LeagueDashPlayerStats(season_type_all_star=SeasonTypeAllStar.default).get_data_frames()[0]['SEASON_ID'][-4:]

    for player in player_dict:
        try:
            # Basic info
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=player['id']).get_data_frames()[0]
            name = player_info['DISPLAY_FIRST_LAST'][0]
            time.sleep(0.6)  # Avoid rate limiting
            # General stats
            general_stats_dash = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id=player['id'], per_mode_detailed='PerGame').get_data_frames()[0]
            general_stats_dash = general_stats_dash[general_stats_dash['GROUP_VALUE'] == current_season]

            # Clutch stats (using last 5 minutes, score within 5 as an example)
            clutch_stats_dash = playerdashboardbyclutch.PlayerDashboardByClutch(player_id=player['id'], per_mode_detailed='PerGame', measure_type_detailed_defense='Advanced').get_data_frames()[0]
            clutch_stats_dash = clutch_stats_dash[clutch_stats_dash['GROUP_VALUE'] == current_season]

            # Add more detailed clutch stats if available
            clutch_efg = clutch_stats_dash['EFG_PCT'].iloc[0] if not clutch_stats_dash.empty else 0
            clutch_plus_minus = clutch_stats_dash['PLUS_MINUS'].iloc[0] if not clutch_stats_dash.empty else 0

            # Shooting stats
            shooting_stats_dash = leaguedashplayerptshot.LeagueDashPlayerPtShot(player_id=player['id'], per_mode_detailed='PerGame', season=current_season, season_type_all_star=SeasonTypeAllStar.default).get_data_frames()[0]
            shooting_stats_dash = shooting_stats_dash[shooting_stats_dash['PLAYER_ID'] == player['id']]
            

            # Combine stats
            player_stats = {
                'Height': player_info['HEIGHT'][0],
                'Weight': player_info['WEIGHT'][0],
                'PTS': general_stats_dash['PTS'].iloc[0] if not general_stats_dash.empty else 0,
                'AST': general_stats_dash['AST'].iloc[0] if not general_stats_dash.empty else 0,
                'TOV': general_stats_dash['TOV'].iloc[0] if not general_stats_dash.empty else 0,
                '3PA': general_stats_dash['FG3A'].iloc[0] if not general_stats_dash.empty else 0,
                '3P%': general_stats_dash['FG3_PCT'].iloc[0] if not general_stats_dash.empty else 0,
                'MP': general_stats_dash['MIN'].iloc[0] if not general_stats_dash.empty else 0,
                'TmMP': general_stats_dash['GP'].iloc[0] * 48 if not general_stats_dash.empty else 0, # Assuming 48 minutes per game
                'TmFG': general_stats_dash['TEAM_FGM'].iloc[0] if not general_stats_dash.empty else 0, # Assuming you have team FG made somewhere
                'FG': general_stats_dash['FGM'].iloc[0] if not general_stats_dash.empty else 0,
                'FGA': general_stats_dash['FGA'].iloc[0] if not general_stats_dash.empty else 0,
                'FTA': general_stats_dash['FTA'].iloc[0] if not general_stats_dash.empty else 0,
                'eFG%': general_stats_dash['EFG_PCT'].iloc[0] if not general_stats_dash.empty else 0,
                'FT%': general_stats_dash['FT_PCT'].iloc[0] if not general_stats_dash.empty else 0,
                '+/-': general_stats_dash['PLUS_MINUS'].iloc[0] if not general_stats_dash.empty else 0,
                'Clutch eFG%': clutch_efg,
                'Clutch +/-': clutch_plus_minus,
                'Spacing': shooting_stats_dash['EFG_PCT'].iloc[0] if not shooting_stats_dash.empty else 0,  # Example, adjust as needed
                'Max Vertical Leap': 0, # Placeholder, you'll need another data source for this
                'Wingspan': 0,  # Placeholder, you'll need another data source for this
                'Usage %': general_stats_dash['USG_PCT'].iloc[0] if not general_stats_dash.empty else 0,
                'ORB%': general_stats_dash['OREB_PCT'].iloc[0] if not general_stats_dash.empty else 0,
                'DRB%': general_stats_dash['DREB_PCT'].iloc[0] if not general_stats_dash.empty else 0,
                'DDARKO': 0,  # Placeholder
                'DLEBRON': 0,  # Placeholder
                'DDRIP': 0,  # Placeholder
                'DBPM': 0,  # Placeholder
                'DLA3RAPM': 0, # Placeholder
            }
            

            all_player_stats[name] = player_stats
            print(f"Fetched stats for {name}")
        except Exception as e:
            print(f"Error fetching data for {player['full_name']}: {e}")

    return all_player_stats