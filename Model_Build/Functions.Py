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

def retrieve_historical_vorp(year):


    team_map = {
        'TOR' : 'Toronto Raptors',
        'MEM' : 'Memphis Grizzlies',
        'MIA' : 'Miami Heat',
        'BRK' : 'Brooklyn Nets',
        'NOP' : 'New Orleans Pelicans',
        'MIL' : 'Milwaukee Bucks',
        'CLE' : 'Cleveland Cavaliers',
        'LAL' : 'Los Angeles Lakers',
        'ORL' : 'Orlando Magic',
        'HOU' : 'Houston Rockets',
        'WAS' : 'Washington Wizards',
        'PHO' : 'Phoenix Suns',
        'UTA' : 'Utah Jazz',
        'SAC' : 'Sacramento Kings',
        'CHO' : 'Charlotte Hornets',
        'CHI' : 'Chicago Bulls',
        'ATL' : 'Atlanta Hawks',
        'NYK' : 'New York Knicks',
        'DEN' : 'Denver Nuggets',
        'PHI' : 'Philadelphia 76ers',
        'SAS' : 'Sacramento Kings',
        'LAC' : 'Los Angeles Clippers',
        'OKC' : 'Oklahoma City Thunder',
        'MIN' : 'Minnesota Timberwolves',
        'DET' : 'Detroit Pistons',
        'IND' : 'Indiana Pacers',
        'GSW' : 'Golden State Warriors',
        'POR' : 'Portland Trailblazers',
        'DAL' : 'Dallas Mavericks',
        'TOT' : 'Toronto Raptors',
        'BOS' : 'Boston Celtics'
    }

    tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(year)}_advanced.html')
    table = tables[0]
    table = table[['Player', 'Tm', 'VORP']]
    table.columns = ['Player', 'Team', 'VORP']
    table = table[table.Team != 'Tm']
    table.Team.unique()
    table['Team'] = table.Team.apply(lambda x: team_map[x])
    table['VORP'] = table.VORP.apply(pd.to_numeric)
    team_vorp = table.groupby('Team')['VORP'].sum()
    
    return team_vorp