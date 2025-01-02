
# config.py
LEAGUE_EFG = None  # Initialize with a default value

def set_league_efg(efg):
    global LEAGUE_EFG
    LEAGUE_EFG = efg

def get_league_efg():
    return LEAGUE_EFG