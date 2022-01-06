import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from sklearn.linear_model import LinearRegression
import pickle
import datetime as dt

current_year = dt.date.today().year


def retrieve_prior_year_vorps(current_year):

    # Retrieving active rosters 
    # team_dict = retrieve_active_rosters()

    # Retrieving prior year VORPs

    tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(current_year-1)}_advanced.html')
    table = tables[0]
    table = table[['Player', 'Tm', 'VORP']]
    table.columns = ['Player', 'Team', 'VORP']
    table = table[table.Team != 'Tm']
    table.Team.unique()
    table['VORP'] = table.VORP.apply(pd.to_numeric)
    player_vorp = table.groupby('Team')['VORP'].sum()
    player_vorp = pd.DataFrame(player_vorp)
    player_vorp.reset_index(drop = False, inplace = True)
    player_vorp.columns = ['Team', 'VORP']
    team_vorps = player_vorp
    team_vorps['VORP'] = team_vorps.VORP * (82/72)

    # # Aggregating team VORPs
    # team_vorps = pd.DataFrame(columns = ['Team', 'Prior_Year_Vorp'])
    # for team, roster in team_dict.items():
    #     team_war = 0
    #     for player in roster:
    #         vorp = player_vorp[player_vorp.Player == player]
    #         vorp = sum(vorp.VORP)
    #         team_war += vorp
    #     if current_year == 2022:
    #         team_war = team_war * (82/72)
    #     vorp_series = pd.Series([team, team_war], index = team_vorps.columns)
    #     team_vorps = team_vorps.append(vorp_series, ignore_index = True)
    
    #Save to data file
    file_path = 'In_Season/Data/prior_year_vorps.csv'
    team_vorps.to_csv(file_path)

    return team_vorps

def retrieve_prior_year_point_differential(current_year):
    
    # Possesions table team map for merging
    team_map = {
        'LA Lakers' : 'Los Angeles Lakers',
        'Charlotte' : 'Charlotte Hornets',
        'Sacramento' : 'Sacramento Kings',
        'San Antonio' : 'San Antonio Spurs',
        'Houston' : 'Houston Rockets',
        'Minnesota' : 'Minnesota Timberwolves',
        'Phoenix' : 'Phoenix Suns',
        'Brooklyn' : 'Brooklyn Nets',
        'Detroit' : 'Detroit Pistons',
        'Memphis' : 'Memphis Grizzlies',
        'Milwaukee' : 'Milwaukee Bucks',
        'Boston' : 'Boston Celtics',
        'Utah' : 'Utah Jazz',
        'Golden State' : 'Golden State Warriors',
        'LA Clippers' : 'Los Angeles Clippers',
        'Orlando' : 'Orlando Magic',
        'Chicago' : 'Chicago Bulls',
        'Portland' : 'Portland Trail Blazers',
        'Okla City': 'Oklahoma City Thunder',
        'New Orleans' : 'New Orleans Pelicans',
        'Indiana' : 'Indiana Pacers',
        'Washington' : 'Washington Wizards',
        'Cleveland' : 'Cleveland Cavaliers',
        'Atlanta' : 'Atlanta Hawks',
        'Toronto' : 'Toronto Raptors',
        'Denver' : 'Denver Nuggets',
        'New York' : 'New York Knicks',
        'Philadelphia' : 'Philadelphia 76ers',
        'Miami' : 'Miami Heat',
        'Dallas' : 'Dallas Mavericks'
    }

    # Getting net adjusted rating table
    rating_tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(current_year-1)}_ratings.html')
    rating_table = rating_tables[0]
    rating_table.columns = rating_table.columns.droplevel(0)
    rating_table['Games'] = rating_table.W + rating_table.L

    # Getting possesions table
    possesions_table = pd.read_html('https://www.teamrankings.com/nba/stat/possessions-per-game')
    possesions_table = possesions_table[0]
    possesions_table['Team'] = possesions_table.Team.apply(lambda x: team_map[x])
    possesions_table = possesions_table[['Team', '2021']]
    possesions_table.columns = ['Team', 'Possesions/Game']

    # Merging tables
    merged = pd.merge(rating_table, possesions_table, on = 'Team', how = 'inner')
    merged['Possesions'] = merged.Games*merged['Possesions/Game']
    merged['Adj_Point_Differential'] = merged.Possesions/100 * merged.NRtg
    merged['Adj_Point_Differential_82'] = merged.Adj_Point_Differential*(82/merged.Games)

    # Importing win pct model
    file_name = 'Model_Build/Data/win_pct_regression.pickle'
    with open(file_name, 'rb') as f:
        model = pickle.load(f)

    # Adding adjusted win percent column
    x = merged[['Adj_Point_Differential_82']]
    merged['Adjusted_Win_Pct'] = model.predict(x)

    # Saving to data folder
    file_path = 'In_Season/Data/prior_year_adjusted_win_pct'
    merged.to_csv(file_path)

    return merged

print(retrieve_prior_year_point_differential(2022))