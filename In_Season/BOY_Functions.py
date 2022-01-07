########## Imports and variables ##########

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

########## Functions ########## 

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

def retrieve_opening_day_roster(current_year):
    tables = pd.read_html('https://www.lineups.com/nba/depth-charts')
    teams = ['Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
            'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
            'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
            'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
            'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans',
            'New York Knicks', 'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers',
            'Phoenix Suns', 'Portland Trailblazers', 'Sacramento Kings', 'San Antonio Spurs',
            'Toronto Raptors', 'Utah Jazz', 'Washington Wizards']
    def name_adjustment(x):
        try:
            names = x.split(' ')
            if len(names) == 4:
                name = names[0] + ' ' + names[1]
            if len(names) == 6:
                name = names[0] + ' ' + names[1] + ' ' + names[2]
        except:
            name = x
        return name

    # Getting active rosters into dictionary of lists for each team
    team_dict = {}
    for team, table in zip(teams,tables):
        table.columns = table.columns.droplevel(0)
        for i in [1,2,3]:
            table[str(i)] = table[str(i)].apply(name_adjustment)
        table = table[['1', '2', '3']]
        players = list()
        for i in range(table.shape[0]): 
            for j in range(table.shape[1]):
                player = table.iloc[i, j]
                players = players + [player]
        team_dict[team] = players

    return team_dict

def retrieve_opening_day_roster_late_start():

    # Teams list to iterate through links
    teams = ['Atlanta-Hawks', 'Boston-Celtics', 'Brooklyn-Nets', 'Charlotte-Hornets', 'Chicago-Bulls', 
    'Cleveland-Cavaliers', 'Dallas-Mavericks', 'Denver-Nuggets', 'Detroit-Pistons', 'Golden-State-Warriors',
    'Houston-Rockets', 'Indiana-Pacers', 'Los-Angeles-Clippers', 'Los-Angeles-Lakers', 'Memphis-Grizzlies',
    'Miami-Heat', 'Milwaukee-Bucks', 'Minnesota-Timberwolves', 'New-Orleans-Pelicans', 'New-York-Knicks',
    'Oklahoma-City-Thunder', 'Orlando-Magic', 'Philadelphia-Sixers', 'Phoenix-Suns', 'Portland-Trail-Blazers',
    'Sacramento-Kings', 'San-Antonio-Spurs', 'Toronto-Raptors', 'Utah-Jazz', 'Washington-Wizards']

    # Iterating through each team to get dictionary of rosters
    team_dict = {}
    for i,team in enumerate(teams):
        link = f'https://basketball.realgm.com/nba/teams/{team}/{str(i+1)}/Rosters/Opening_Day'
        tables = pd.read_html(link)
        table = tables[8]
        table = table[['Player', 'YOS']]
        team = team.split('-')
        if len(team) == 2:
            team = team[0] + ' ' + team[1]
        if len(team) == 3:
            team = team[0] + ' ' + team[1] + ' ' + team[2]
        team_dict[team] = table
    
    # Saving opening day rosters
    file_name = 'In_Season/Data/opening_day_rosters.pickle'
    with open(file_name, 'wb') as f:
        pickle.dump(team_dict, f)

    return team_dict

def retrieve_opening_day_vorp_predictors(current_year):
    
    # Getting predictive advanced stats from the prior year and adjusting columns
    tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(current_year-1)}_advanced.html')
    table = tables[0]
    table = table[['Player', 'Age', 'Tm', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 
                'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48',
                'OBPM', 'DBPM', 'BPM', 'VORP']]
    table.columns = ['Player', 'Age', 'Team', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 
                'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48',
                'OBPM', 'DBPM', 'BPM', 'VORP_Prior_Year']
    table = table[table.Team != 'Tm']
    columns = ['Age', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 
                'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48',
                'OBPM', 'DBPM', 'BPM', 'VORP_Prior_Year']
    for column in columns:
        table[column] = table[column].apply(pd.to_numeric)
    
    # Grouping players, converting to DF, naming columns
    player_predictive = table.groupby('Player').agg({'Age' : 'mean', 'G' : 'sum', 'MP' : 'sum', 'PER' : 'mean', 
                                                    'TS%' : 'mean', '3PAr' : 'mean', 'FTr' : 'mean', 
                                                    'ORB%' : 'mean', 'DRB%' : 'mean', 'TRB%' : 'mean', 
                                                    'AST%' : 'mean', 'STL%' : 'mean', 'BLK%' : 'mean', 
                                                    'TOV%' : 'mean', 'USG%' : 'mean', 'OWS' : 'sum', 
                                                    'DWS' : 'sum', 'WS' : 'sum', 'WS/48' : 'mean', 
                                                    'OBPM' : 'sum', 'DBPM' : 'sum', 'BPM' : 'sum',
                                                    'VORP_Prior_Year' : 'sum'})
    player_predictive = pd.DataFrame(player_predictive)
    player_predictive.reset_index(drop = False, inplace = True)
    player_predictive.columns = ['Player', 'Age', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 
                'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48',
                'OBPM', 'DBPM', 'BPM', 'VORP_Prior_Year']
    
    
    # Adjusting for less games
    if current_year == 2022:
        player_predictive['VORP_Prior_Year'] = player_predictive.VORP_Prior_Year * (82/72)
        player_predictive['G'] = player_predictive.G * (82/72)
        player_predictive['MP'] = player_predictive.MP * (82/72)
        player_predictive['OWS'] = player_predictive.OWS * (82/72)
        player_predictive['DWS'] = player_predictive.DWS * (82/72)
        player_predictive['WS'] = player_predictive.WS * (82/72)
        player_predictive['OBPM'] = player_predictive.OBPM * (82/72)
        player_predictive['DBPM'] = player_predictive.DBPM * (82/72)
        player_predictive['BPM'] = player_predictive.BPM * (82/72)

    # Saving data
    file_name = 'In_Season/Data/vorp_predictive_data.csv'
    player_predictive.to_csv(file_name)
    
    return player_predictive

retrieve_opening_day_vorp_predictors(current_year)