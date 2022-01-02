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


def retrieve_active_rosters():

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

def retrieve_active_rosters_vorp(current_year):
    
    # Retrieving active rosters 
    team_dict = retrieve_active_rosters()

    # Retrieving current year VORPs
    tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(current_year)}_advanced.html')
    table = tables[0]
    table = table[['Player', 'Tm', 'VORP']]
    table.columns = ['Player', 'Team', 'VORP']
    table = table[table.Team != 'Tm']
    table.Team.unique()
    table['VORP'] = table.VORP.apply(pd.to_numeric)
    player_vorp = table.groupby('Player')['VORP'].sum()
    player_vorp = pd.DataFrame(player_vorp)
    player_vorp.reset_index(drop = False, inplace = True)
    player_vorp.columns = ['Player', 'VORP']
    player_vorp

    # Aggregating team VORPs
    team_vorps = {}
    for team, roster in team_dict.items():
        team_war = 0
        for player in roster:
            vorp = player_vorp[player_vorp.Player == player]
            vorp = sum(vorp.VORP)
            team_war += vorp
        team_vorps[team] = team_war

    return team_vorps