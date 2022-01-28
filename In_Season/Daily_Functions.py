##########IMPORTS AND PARAMETERS##########

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
import unidecode

current_year = 2022

##########FUNCTIONS##########

# Retreiving necessary daily information

def retreive_active_rosters():

    # Instantiating necessary items
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

def retreive_games_played(current_year):

    # Map to change team names
    games_played_map = {
        'Milwaukee' : 'Milwaukee Bucks',
        'Boston' : 'Boston Celtics',
        'Memphis' : 'Memphis Grizzlies',
        'LA Clippers' : 'Los Angeles Clippers',
        'Sacramento' : 'Sacramento Kings',
        'Indiana' : 'Indiana Pacers',
        'Golden State' : 'Golden State Warriors',
        'LA Lakers' : 'Los Angeles Lakers',
        'San Antonio' : 'San Antonio Spurs',
        'Utah' : 'Utah Jazz',
        'Houston' : 'Houston Rockets',
        'Dallas' : 'Dallas Mavericks',
        'Charlotte' : 'Charlotte Hornets',
        'Cleveland' : 'Cleveland Cavaliers',
        'Orlando' : 'Orlando Magic',
        'Washington' : 'Washington Wizards',
        'New York' : 'New York Knicks',
        'Brooklyn' : 'Brooklyn Nets',
        'Philadelphia' : 'Philadelphia 76ers',
        'Minnesota' : 'Minnesota Timberwolves',
        'Miami' : 'Miami Heat',
        'New Orleans' : 'New Orleans Pelicans',
        'Detroit' : 'Detroit Pistons',
        'Okla City' : 'Oklahoma City Thunder',
        'Portland' : 'Portland Trailblazers',
        'Chicago' : 'Chicago Bulls',
        'Denver' : 'Denver Nuggets',
        'Phoenix' : 'Phoenix Suns',
        'Atlanta' : 'Atlanta Hawks',
        'Toronto' : 'Toronto Raptors'
    }

    # Reading in table and adjusting columns
    tables = pd.read_html('https://www.teamrankings.com/nba/stat/games-played')
    games_played_table = tables[0]
    games_played_table = games_played_table[['Team', str(current_year - 1)]]
    games_played_table.columns = ['Team', 'Games_Played']
    games_played_table['Team'] = games_played_table.Team.apply(lambda x: games_played_map[x])

    return games_played_table

def retreive_active_rosters_vorp(current_year):
    
    # Retrieving active rosters 
    team_dict = retreive_active_rosters()

    # Retrieving current year VORPs
    tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(current_year)}_advanced.html')
    table = tables[0]
    table = table[['Player', 'Tm', 'VORP']]
    table.columns = ['Player', 'Team', 'VORP']
    table = table[table.Team != 'Tm']
    table = table[table.Team != 'TOT']
    table['VORP'] = table.VORP.apply(pd.to_numeric)
    player_vorp = table.groupby('Player')['VORP'].sum()
    player_vorp = pd.DataFrame(player_vorp)
    player_vorp.reset_index(drop = False, inplace = True)
    player_vorp.columns = ['Player', 'VORP']

    # Aggregating team VORPs
    team_vorps = pd.DataFrame(columns = ['Team', 'VORP'])
    for team, roster in team_dict.items():
        team_war = 0
        for player in roster:
            vorp = player_vorp[player_vorp.Player == player]
            vorp = sum(vorp.VORP)
            team_war += vorp
        if current_year == 2022:
            team_war = team_war * (82/72)
        vorp_series = pd.Series([team, team_war], index = team_vorps.columns)
        team_vorps = team_vorps.append(vorp_series, ignore_index = True)

    return team_vorps

# Functions to calculate day's win %

def retreive_adjusted_point_differetial():

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
    rating_tables = pd.read_html('https://www.basketball-reference.com/leagues/NBA_2022_ratings.html')
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

    return merged

def calculate_current_day_team_vorp(current_year):

    # Calling functions to get necessary info
    active_rosters = retrieve_active_rosters()
    games_played_table = retreive_games_played(current_year)

    # Getting overall fraction of season from average of games played table
    frac_season = np.mean(games_played_table.Games_Played)/82

    # Retreiving BOY projected VORPS
    boy_vorps = pd.read_csv('In_Season/Data/opening_day_vorps_player.csv', index_col = 0)
    # Changing Vorp_Projection column to be a float
    boy_vorps['VORP_projection'] = boy_vorps.VORP_projection.apply(lambda x: float(x.strip('[]')) if type(x)==str else x)

    # Retrieving current year VORPs
    tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(current_year)}_advanced.html')
    table = tables[0]
    table = table[['Player', 'Tm', 'G', 'VORP']]
    table.columns = ['Player', 'Team', 'Games', 'VORP']
    table = table[table.Team != 'Tm']
    table = table[table.Team != 'TOT']
    table['VORP'] = table.VORP.apply(pd.to_numeric)
    player_vorp = table.groupby(['Player', 'Games'])['VORP'].sum()
    player_vorp = pd.DataFrame(player_vorp)
    player_vorp.reset_index(drop = False, inplace = True)
    player_vorp.columns = ['Player', 'Games', 'VORP']

    # Adjusting naming conventions of current year VORP table to be consistent w/ BOY vorps
    table['Player'] = table.Player.str.lower()
    table['Player'] = table.Player.apply(unidecode.unidecode)
    table['Player'] = table.Player.str.replace("'", '')
    table['Player'] = table.Player.str.replace(".", '')
    table['Player'] = table.Player.apply(lambda x: x.split(' ')[0] + ' ' + x.split(' ')[1])
    table['Player'] = table.Player.str.strip('*,')
    table['Player'] = table.Player.apply(name_exceptions)

    # Merging BOY VORPS w/ current VORPs
    vorp_df = pd.merge(boy_vorps, table, on = 'Player', how = 'inner')
    vorp_df['Games'] = vorp_df.Games.apply(float)
    vorp_df.drop_duplicates(subset = ['Player'], inplace = True)

    # Getting each player's current year annualized VORP, adjusting for games played
    vorp_df['VORP_82'] = 0
    if frac_season < 0.25:
        vorp_df['VORP_82'] = vorp_df.VORP_projection
    if frac_season > 0.25:
        for index, row in vorp_df.iterrows():
            if ((frac_season <= 0.5) & (row.Games < 12)):
                vorp_df.loc[index, 'VORP_82'] = row.VORP_projection
            elif ((frac_season > 0.5) & (frac_season <= 0.75) & (row.Games < 25)):
                vorp_df.loc[index, 'VORP_82'] = row.VORP_projection
            elif ((frac_season > 0.75) & (row.Games < 40)):
                vorp_df.loc[index, 'VORP_82'] = row.VORP_projection
            else:
                games_frac = float(row.Games)/82.0
                vorp_df.loc[index, 'VORP_82'] = (row.VORP_projection * (1.0 - games_frac)) + (row.VORP * games_frac)
    
    # Iterating through active rosters to get active roster annnualized VORP
    team_vorp_df = pd.DataFrame(columns = ['Team', 'VORP_Today'])
    missed_players = list()
    for team, roster in active_rosters.items():
        team_vorp = 0
        for player in roster:
            if str(player) == 'nan':
                continue
            
            # Aligning naming conventions with vorp_df
            player = player.lower()
            player = unidecode.unidecode(player)
            player = player.replace("'", '')
            player = player.replace(".", '')
            player = player.split(' ')[0] + ' ' + player.split(' ')[1]
            player.strip('*,')
            player = name_exceptions(player)
            
            # Adding player's VORP to team VORP total
            player_vorp = vorp_df[vorp_df.Player == player]
            if len(player_vorp == 1):
                vorp = sum(player_vorp.VORP_82)
                team_vorp += vorp
            else:
                missed_players.append(player)
        
        # Adding team's VORP to overall VORP df
        series = pd.Series([team, team_vorp], index = team_vorp_df.columns)
        team_vorp_df = team_vorp_df.append(series, ignore_index = True)

    return team_vorp_df, missed_players
