from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, leaguedashplayerstats, leaguedashplayerclutch, leaguedashplayerbiostats, draftcombinestats, leaguedashteamstats
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import config

def get_advanced_defensive_stats(player_name, season):
    """
    Web scrapes Basketball Reference for a given player and season to retrieve DWS and DBPM.
    
    Parameters:
        player_name (str): The name of the player (e.g., "LeBron James").
        season (str): The season year in the format "YYYY-YY" (e.g., "2023-24").
    
    Returns:
        dict: A dictionary containing the player's DWS and DBPM for the specified season.
    """
    # Split the string into the start year and the last two digits of the end year
    start_year, end_short = season.split('-')
    
    # Extract the first two digits of the start year
    century = start_year[:2]
    
    # Combine the century with the last two digits to form the full end year
    season = int(century + end_short)

    # Split the player name into first and last name
    first_name, last_name = player_name.lower().split()
    
    # Construct the player's URL
    player_url = f"https://www.basketball-reference.com/players/{last_name[0]}/{last_name[:5]}{first_name[:2]}01.html"
    
    # Send a GET request to the player's page
    response = requests.get(player_url)
    
    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data for {player_name}. Status code: {response.status_code}")
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Locate the Advanced table
    advanced_table = soup.find("table", {"id": "advanced"})
    
    if not advanced_table:
        raise Exception(f"Advanced stats table not found for {player_name}.")
    
    # Extract the header row to find the indices of DWS and DBPM
    header_row = advanced_table.find("thead").find("tr")
    headers = [th.text for th in header_row.find_all("th")]
    
    # Find the indices of DWS and DBPM
    try:
        dws_index = headers.index("DWS")
        dbpm_index = headers.index("DBPM")
    except ValueError:
        raise Exception("DWS or DBPM column not found in the Advanced table.")
    
    # Locate the row for the specified season
    season_row = advanced_table.find("tbody").find("tr", {"id": f"advanced.{season}"})
    
    if not season_row:
        raise Exception(f"No data found for {player_name} in the {season} season.")
    
    # Extract the player's DWS and DBPM from the row
    # Note: The data rows have an additional "th" tag for the season, so we need to offset the indices by 1
    dws = season_row.find_all("td")[dws_index - 1].text
    dbpm = season_row.find_all("td")[dbpm_index - 1].text
    
    # Return the results as a dictionary
    return {
        "Player": player_name,
        "Season": season,
        "DWS": dws,
        "DBPM": dbpm
    }

def fetch_player_data():
    """
    Fetches player data from the NBA API for the 2023-24 season.
    Filters for players who averaged at least 20 minutes per game.

    Returns:
        dict: A dictionary where keys are player names and values are dictionaries of stats.
    """
    player_dict = players.find_players_by_full_name("Lebron James")
    all_player_stats = {}

    # Hardcode the current season
    current_season = '2023-24'

    general_stats = leaguedashplayerstats.LeagueDashPlayerStats(season=current_season, rank='N')
    general_stats_df = general_stats.get_data_frames()[0]

    general_stats_per100 = leaguedashplayerstats.LeagueDashPlayerStats(season=current_season, rank='N', per_mode_detailed='Per100Possessions')
    general_stats__per100_df = general_stats.get_data_frames()[0]

    advanced_stats = leaguedashplayerbiostats.LeagueDashPlayerBioStats(season=current_season)
    advanced_stats_df = advanced_stats.get_data_frames()[0]

    clutch_stats = leaguedashplayerclutch.LeagueDashPlayerClutch(season=current_season, rank='N')
    clutch_stats_df = clutch_stats.get_data_frames()[0]

    combine_stats = draftcombinestats.DraftCombineStats(season_all_time='All Time')
    combine_stats_df = combine_stats.get_data_frames()[0]

    for player in player_dict:
        try:
            # Basic info
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=player['id']).get_data_frames()[0]
            name = player_info['DISPLAY_FIRST_LAST'][0]
            time.sleep(0.6)  # Avoid rate limiting

            # General stats
            general_stats_df_player = general_stats_df[general_stats_df['PLAYER_ID'] == player['id']]

            # General stats per 100 possessions
            general_stats__per100_df_player = general_stats__per100_df[general_stats__per100_df['PLAYER_ID'] == player['id']]

            # Advanced stats
            advanced_stats_df_player = advanced_stats_df[advanced_stats_df['PLAYER_ID'] == player['id']]

            # Clutch stats
            clutch_stats_df_player = clutch_stats_df[clutch_stats_df['PLAYER_ID'] == player['id']]

            # Combine stats
            combine_stats_df_player = combine_stats_df[combine_stats_df['PLAYER_ID'] == player['id']]

            # Defense stats
            defense_stats = get_advanced_defensive_stats(name, current_season)

            # Combine stats
            player_stats = {
                'Height': advanced_stats_df_player['PLAYER_HEIGHT_INCHES'].iloc[0],
                'Weight': advanced_stats_df_player['PLAYER_WEIGHT'].iloc[0],
                'PTS': general_stats_df_player['PTS'].iloc[0] if not general_stats_df_player.empty else 0,
                'AST': general_stats_df_player['AST'].iloc[0] if not general_stats_df_player.empty else 0,
                'TOV': general_stats_df_player['TOV'].iloc[0] if not general_stats_df_player.empty else 0,
                '3PA': general_stats_df_player['FG3A'].iloc[0] if not general_stats_df_player.empty else 0,
                '3PAper100': general_stats__per100_df_player['FG3A'].iloc[0] if not general_stats__per100_df_player.empty else 0,
                '3P%': general_stats_df_player['FG3_PCT'].iloc[0] if not general_stats_df_player.empty else 0,
                'MP': general_stats_df_player['MIN'].iloc[0] if not general_stats_df_player.empty else 0,
                'TmMP': general_stats_df_player['GP'].iloc[0] * 48 if not general_stats_df_player.empty else 0, # Assuming 48 minutes per game
                'FG': general_stats_df_player['FGM'].iloc[0] if not general_stats_df_player.empty else 0,
                'FGA': general_stats_df_player['FGA'].iloc[0] if not general_stats_df_player.empty else 0,
                'FTA': general_stats_df_player['FTA'].iloc[0] if not general_stats_df_player.empty else 0,
                'TS%': advanced_stats_df_player['TS_PCT'].iloc[0] if not advanced_stats_df_player.empty else 0,
                'FT%': general_stats_df_player['FT_PCT'].iloc[0] if not general_stats_df_player.empty else 0,
                '+/-': general_stats_df_player['PLUS_MINUS'].iloc[0] if not general_stats_df_player.empty else 0,
                'Clutch_PTS': clutch_stats_df_player['PTS'].iloc[0] if not clutch_stats_df_player.empty else 0,
                'Clutch_FGA': clutch_stats_df_player['FGA'].iloc[0] if not clutch_stats_df_player.empty else 0,
                'Clutch_FTA': clutch_stats_df_player['FTA'].iloc[0] if not clutch_stats_df_player.empty else 0,
                'Clutch_+/-': clutch_stats_df_player['PLUS_MINUS'].iloc[0] if not clutch_stats_df_player.empty else 0,
                'Max_Vertical_Leap': combine_stats_df_player['MAX_VERTICAL_LEAP'].iloc[0] if not combine_stats_df_player.empty else 0,
                'Wingspan': combine_stats_df_player['WINGSPAN'].iloc[0] if not combine_stats_df_player.empty else 0,
                'Usage%': advanced_stats_df_player['USG_PCT'].iloc[0] if not advanced_stats_df_player.empty else 0,
                'ORB%': advanced_stats_df_player['OREB_PCT'].iloc[0] if not advanced_stats_df_player.empty else 0,
                'DRB%': advanced_stats_df_player['DREB_PCT'].iloc[0] if not advanced_stats_df_player.empty else 0,
                'pAST%': advanced_stats_df_player['AST_PCT'].iloc[0] if not advanced_stats_df_player.empty else 0,
                'DBPM': defense_stats['DBPM'], 
                'DWS': defense_stats['DWS']
            }

            all_player_stats[name] = player_stats

        except Exception as e:
            print(f"Error fetching data for {player['full_name']}: {e}")

    return all_player_stats

def get_nba_efg(season):
    """
    Fetches the league-wide Effective Field Goal Percentage (eFG%) for a given season.

    Args:
        season (str): The NBA season (e.g., '2023-24').

    Returns:
        float: The league-wide eFG% for the season, or None if an error occurs.
    """
    try:
        # Fetch team stats for the given season
        team_stats = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Advanced'  # Get advanced stats
        ).get_data_frames()[0]

        # Calculate the league-wide eFG%
        league_efg = team_stats['EFG_PCT'].mean()

        return league_efg

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage: Get eFG% for the 2023-24 season
current_season = '2023-24'
efg = get_nba_efg(current_season)

if efg:
    # Save to config file
    config.set_league_efg(efg)