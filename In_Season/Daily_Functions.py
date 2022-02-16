##########IMPORTS AND PARAMETERS##########

# Imports 
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
import time
import datetime as dt
import re
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Setting current year parameter
today = dt.date.today()
today_month = today.month
if (today_month > 7):
    current_year = today.year + 1
else:
    current_year = today.year

kelly = 10.0

##########FUNCTIONS##########

# Retreiving necessary daily information

def retreive_active_rosters():

    # Functions for name standardizing
    def name_standardization_df(df):
        df['Player'] = df.Player.apply(unidecode.unidecode)
        df['Player'] = df.Player.str.replace('.', '')
        df['Player'] = df.Player.str.replace("'", '')
        df['Player'] = df.Player.str.lower()
        df['Player'] = df.Player.str.strip('*')
        return df
    def name_standardization_player(player):
        player = unidecode.unidecode(player)
        player = player.replace('.', '')
        player = player.replace("'", '')
        player = player.lower()
        player = player.strip('*')
        return player

    # Retreiving retreive_injuries
    injuries = retreive_injuries()
    injuries = name_standardization_df(injuries)

    # Instantiating necessary items
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get('https://www.lineups.com/nba/depth-charts')
    driver.refresh()
    time.sleep(5)
    html = driver.page_source
    tables = pd.read_html(html)
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
            if len(names) == 5:
                name = names[0] + ' ' + names[1]
            if len(names) == 7:
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
                if type(player) == float:
                    continue
                player_standard = name_standardization_player(player)
                if (player_standard in injuries.Player.unique()):
                    pass
                else:
                    players = players + [player]
        team_dict[team] = players

    return team_dict

def retreive_injuries():
    # Getting tables
    tables = pd.read_html('https://www.espn.com/nba/injuries')

    # Iterating through injury tables to create injury list
    injuries = pd.DataFrame(columns = ['NAME', 'STATUS'])
    for table in tables:
        table = table[['NAME', 'STATUS']]
        injuries = injuries.append(table)
    injuries.reset_index(drop = True, inplace = True)

    # Filtering out players who may not be out
    injuries = injuries[injuries.STATUS == 'Out']

    # Adjusting columns
    injuries = injuries[['NAME']]
    injuries.columns = ['Player']

    return injuries

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

def retreive_todays_games():

    # Creating teamp map to change scraped team names to align with VORPS
    team_map_schedule = {
        'L.A. Lakers' : 'Los Angeles Lakers',
        'L.A. Clippers' : 'Los Angeles Clippers',
        'Portland' : 'Portland Trailblazers',
        'Cleveland' : 'Cleveland Cavaliers',
        'Denver' : 'Denver Nuggets',
        'Dallas' : 'Dallas Mavericks',
        'Utah' : 'Utah Jazz',
        'San Antonio' : 'San Antonio Spurs',
        'Atlanta' : 'Atlanta Hawks',
        'Charlotte' : 'Charlotte Hornets',
        'Chicago' : 'Chicago Bulls',
        'Detroit' : 'Detroit Pistons',
        'Milwaukee' : 'Milwaukee Bucks',
        'Orlando' : 'Orlando Magic',
        'Minnesota' : 'Minnesota Timberwolves',
        'Phoenix' : 'Phoenix Suns',
        'Boston' : 'Boston Celtics',
        'Indiana' : 'Indiana Pacers',
        'Sacramento' : 'Sacramento Kings',
        'Toronto' : 'Toronto Raptors',
        'Washington' : 'Washington Wizards',
        'Brooklyn' : 'Brooklyn Nets',
        'New Orleans' : 'New Orleans Pelicans',
        'Dallas' : 'Dallas Mavericks',
        'Philadelphia' : 'Philadelphia 76ers',
        'Miami' : 'Miami Heat',
        'Memphis' : 'Memphis Grizzlies',
        'Golden St.' : 'Golden State Warriors',
        'New York' : 'New York Knicks',
        'Houston' : 'Houston Rockets',
        'Oklahoma City' : 'Oklahoma City Thunder'
    }

    # Instantiating selenium driver
    link = 'https://www.cbssports.com/nba/schedule/'
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(link)

    # Getting table for today's games and formatting
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@id='TableBase']/div/div/table")))
    html = driver.page_source
    tables = pd.read_html(html)
    try:
        today_schedule = tables[1]
    except:
        today_schedule = tables[0]
    today_schedule = today_schedule[['Away', 'Home']]
    today_schedule['Away'] = today_schedule.Away.apply(lambda x: team_map_schedule[x])
    today_schedule['Home'] = today_schedule.Home.apply(lambda x: team_map_schedule[x])

    # Getting table for yesterday's games and formatting
    day_buttons = driver.find_elements_by_class_name("ToggleContainer-text")
    yesterday = day_buttons[0]
    yesterday.click()
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='TableBase']/div/div/table")))
    html_yesterday = driver.page_source
    tables_yesterday = pd.read_html(html_yesterday)
    try:
        yesterday_schedule = tables_yesterday[1]
    except:
        yesterday_schedule = tables_yesterday[0]
    yesterday_schedule = yesterday_schedule[['Away', 'Home']]
    yesterday_schedule['Away'] = yesterday_schedule.Away.apply(lambda x: team_map_schedule[x])
    yesterday_schedule['Home'] = yesterday_schedule.Home.apply(lambda x: team_map_schedule[x])

    # Getting table for tomorrow's games and formatting
    day_buttons = driver.find_elements_by_class_name("ToggleContainer-text")
    today = day_buttons[2]
    today.click()
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='TableBase']/div/div/table")))
    day_buttons = driver.find_elements_by_class_name("ToggleContainer-text")
    tomorrow = day_buttons[2]
    tomorrow.click()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@id='TableBase']/div/div/table")))
    html_tomorrow = driver.page_source
    tables_tomorrow = pd.read_html(html_tomorrow)
    try:
        tomorrow_schedule = tables_tomorrow[1]
    except:
        tomorrow_schedule = tables_tomorrow[0]
    tomorrow_schedule = tomorrow_schedule[['Away', 'Home']]
    tomorrow_schedule['Away'] = tomorrow_schedule.Away.apply(lambda x: team_map_schedule[x])
    tomorrow_schedule['Home'] = tomorrow_schedule.Home.apply(lambda x: team_map_schedule[x])


    # Creating B2B columns for today's today's schedule 
    today_schedule['is_B2B_First_Away'] = today_schedule.Away.apply(lambda x: 1 if x in 
                                                                list(tomorrow_schedule.Away.unique()) + list(tomorrow_schedule.Home.unique())
                                                               else 0)
    today_schedule['is_B2B_First_Home'] = today_schedule.Home.apply(lambda x: 1 if x in 
                                                                    list(tomorrow_schedule.Away.unique()) + list(tomorrow_schedule.Home.unique())
                                                                else 0)
    today_schedule['is_B2B_Second_Away'] = today_schedule.Away.apply(lambda x: 1 if x in 
                                                                    list(yesterday_schedule.Away.unique()) + list(yesterday_schedule.Home.unique())
                                                                else 0)
    today_schedule['is_B2B_Second_Home'] = today_schedule.Home.apply(lambda x: 1 if x in 
                                                                    list(yesterday_schedule.Away.unique()) + list(yesterday_schedule.Home.unique())
                                                                else 0)

    return today_schedule

def retreive_odds():

    # Creating function to convert odds to probability
    def calculate_odds(odds):
        if odds<0:
            return (abs(odds)/(abs(odds)+100))*100
        if odds>0:
            return (100/(odds+100))*100

    # Creating team map to align w/ final output
    team_map = {
        'Wizards' : 'Washington Wizards',
        'Celtics' : 'Boston Celtics',
        'Pelicans' : 'New Orleans Pelicans',
        'Knicks' : 'New York Knicks',
        'Pistons' : 'Detroit Pistons',
        'Magic' : 'Orlando Magic',
        '76ers' : 'Philadelphia 76ers',
        'Hawks' : 'Atlanta Hawks',
        'Pacers' : 'Indiana Pacers',
        'Raptors' : 'Toronto Raptors',
        'Grizzlies' : 'Memphis Grizzlies',
        'Heat' : 'Miami Heat',
        'Bulls' : 'Chicago Bulls',
        'Jazz' : 'Utah Jazz',
        'Bucks' : 'Milwaukee Bucks',
        'Spurs' : 'San Antonio Spurs',
        'Warriors' : 'Golden State Warriors',
        'Thunder' : 'Oklahoma City Thunder',
        'Timberwolves' : 'Minnesota Timberwolves',
        'Nuggets' : 'Denver Nuggets',
        'Suns' : 'Phoenix Suns',
        'Cavaliers' : 'Cleveland Cavaliers',
        'Mavericks' : 'Dallas Mavericks',
        'Kings' : 'Sacramento Kings',
        'Hornets' : 'Charlotte Hornets',
        'Trail Blazers' : 'Portland Trailblazers',
        'Nets' : 'Brooklyn Nets',
        'Lakers' : 'Los Angeles Lakers',
        'Clippers' : 'Los Angeles Clippers',
        'Rockets' : 'Houston Rockets'
    }

    # Instantiating WebDriver
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get('https://www.actionnetwork.com/nba/odds')

    # Navigating to ML
    ml_button = driver.find_element_by_xpath("//*[@id='__next']/div/main/div/div[2]/div/div[1]/div[2]/select")
    select = Select(ml_button)
    select.select_by_visible_text('Moneyline')

    # Getting table from HTML
    html = driver.page_source
    tables = pd.read_html(html)
    odds = tables[0]
    odds.dropna(inplace = True)
    odds.reset_index(drop = True, inplace = True)

    odds_df = pd.DataFrame(columns = ['Home_Team', 'Away_Team', 'Home_Odds', 'Away_Odds'])
    for index, row in odds.iterrows():
        
        # Retreiving teams
        teams = {}
        for key in team_map.keys():
            if row.Scheduled.find(key) != -1:
                teams[row.Scheduled.find(key)] = key
        keys = []
        for key in teams.keys():
            keys.append(key)
        if keys[0] > keys[1]:
            home_team = teams[keys[0]]
            away_team = teams[keys[1]]
        else:
            home_team = teams[keys[1]]
            away_team = teams[keys[0]]
        
        # Retreiving odds
        ml_string = row['Unnamed: 5']
        if len(ml_string) == 12:
            ml_string = ml_string.replace('ML', '')
            ml_away = ml_string[:4]
            ml_home = ml_string[-4:]
        if len(ml_string) == 13:
            ml_string = ml_string.replace('ML', '')
            if (ml_string[4] == '+') | (ml_string[4]=='-'):
                ml_away = ml_string[:4]
                ml_home = ml_string[-5:]
            else:
                ml_away = ml_string[:5]
                ml_home = ml_string[-4:]
        if len(ml_string) == 14:
            ml_string = ml_string.replace('ML', '')
            if (ml_string[5] == '+') | (ml_string[5]=='-'):
                ml_away = ml_string[:5]
                ml_home = ml_string[-5:]
            else:
                ml_away = ml_string[:5]
                ml_home = ml_string[-5:]
        try:
            ml_away = float(ml_away)
        except:
            continue
        try:
            ml_home = float(ml_home)
        except:
            continue
        series = pd.Series([home_team, away_team, ml_home, ml_away], index = odds_df.columns)
        odds_df = odds_df.append(series, ignore_index = True)
    odds_df['Home_Prob'] = odds_df.Home_Odds.apply(calculate_odds)
    odds_df['Away_Prob'] = odds_df.Away_Odds.apply(calculate_odds)
    odds_df['Home_Team'] = odds_df.Home_Team.apply(lambda x: team_map[x])
    odds_df['Away_Team'] = odds_df.Away_Team.apply(lambda x: team_map[x])

    # Adding a message if games are passed over for same reason
    if len(odds_df) != len(odds):
        print("At least one game not included in odds df")
    
    return odds_df
    
# Functions to calculate day's win %

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
    active_rosters = retreive_active_rosters()
    games_played_table = retreive_games_played(current_year)

    # Getting overall fraction of season from average of games played table
    frac_season = np.mean(games_played_table.Games_Played)/82.0

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
    table = table.groupby(['Player']).agg({'Games' : 'sum', 'VORP' : 'sum'})
    table = pd.DataFrame(table)
    table.reset_index(drop = False, inplace = True)
    table.columns = ['Player', 'Games', 'VORP']

    # Adjusting naming conventions of current year VORP table to be consistent w/ BOY vorps
    def name_exceptions(x):
        if x == 'cam thomas':
            return 'cameron thomas'
        if x == 'herbert jones':
            return 'herb jones'
        if x == 'charlie brown':
            return 'charles brown'
        if x == 'ish wainright':
            return 'ishmail wainright'
        if x == 'enes freedom':
            return 'enes kanter'
        return x
    
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

    return team_vorp_df, missed_players, frac_season

def calculate_current_day_win_pct(team_vorp_df, frac_season):

    # Retreiving necessary inputs
    boy_win_pct_df = pd.read_csv('In_Season/Data/BOY_projected_win_pct.csv', index_col = 0)
    boy_win_pct_df = boy_win_pct_df[['Team', 'Projected_Point_Differential', 'VORP_Projection']]

    point_diff_df = retreive_adjusted_point_differetial()
    point_diff_df = point_diff_df[['Team', 'Adj_Point_Differential_82', 'Games']]
    for index, row in point_diff_df.iterrows():
        if row.Team == 'Portland Trail Blazers':
            point_diff_df.loc[index, 'Team'] = 'Portland Trailblazers'
    
    # Retreiving VORP/point model
    file_name = 'Model_Build/Data/vorp_regression.pickle'
    with open(file_name, 'rb') as f:
        model = pickle.load(f)
    
    # Retreiving point/win_pct model
    file_name = 'Model_Build/Data/win_pct_regression.pickle'
    with open(file_name, 'rb') as f:
        win_pct_model = pickle.load(f)

    # Merging tables
    merged_1 = pd.merge(point_diff_df, team_vorp_df, on = 'Team')
    merged_2 = pd.merge(merged_1, boy_win_pct_df, on = 'Team')

    # Calculating team's point differential considering inputs
    merged_2['Point_Differential'] = 0
    if frac_season < 0.25:
        merged_2['Point_Differential'] = merged_2.Projected_Point_Differential
    else:
        merged_2['Point_Differential'] = merged_2.Projected_Point_Differential * (1 - merged_2.Games/82.0)\
            + merged_2.Adj_Point_Differential_82 * merged_2.Games/82.0

    # Making adjustment for VORP
    merged_2['VORP_Adjustment'] = 0
    for index, row in merged_2.iterrows():
        vorp_difference = row.VORP_Today - row.VORP_Projection
        merged_2.loc[index, 'VORP_Adjustment'] = model.coef_ * vorp_difference
    
    merged_2['Point_Differential_Final'] = merged_2.Point_Differential + merged_2.VORP_Adjustment

    # Adding projected win % column
    merged_2['Projected_Win_Pct'] = 0
    for index, row in merged_2.iterrows():
        x = merged_2[merged_2.Team == row.Team]
        x = x[['Point_Differential_Final']]
        merged_2.loc[index, 'Projected_Win_Pct'] = win_pct_model.predict(x)

    return merged_2

# Functions to calculate today's bets and results

def calculate_todays_bets(projected_win_pct_table, kelly, capital, save = False):

    # Retreiving today's games
    todays_games = retreive_todays_games()
    todays_odds = retreive_odds()
    
    # Iterating through today's games and putting in calculated probability
    todays_games['Away_Prob_Naive'] = 0
    todays_games['Home_Prob_Naive'] = 0
    for index, row in todays_games.iterrows():
        todays_games.loc[index, 'Away_Prob_Naive'] = projected_win_pct_table[projected_win_pct_table.Team == row.Away]['Projected_Win_Pct'].iloc[0]                                         
        todays_games.loc[index, 'Home_Prob_Naive'] = projected_win_pct_table[projected_win_pct_table.Team == row.Home]['Projected_Win_Pct'].iloc[0]
    
    # Iterating through today's games to adjust projected winning percentage based on game factors
    todays_games['Home_Prob_Adjusted'] = 0
    todays_games['Away_Prob_Adjusted'] = 0
    for index, row in todays_games.iterrows():

        # Getting projected win % by comparing naive projected
        home_prob_compared = row.Home_Prob_Naive * (1 - row.Away_Prob_Naive) 
        away_prob_compared = row.Away_Prob_Naive * (1 - row.Home_Prob_Naive)

        # Creating a scaler for adjustment
        scaler = 1.0/(home_prob_compared + away_prob_compared)

        # Adjusting for home court advantage/B2B
        if (row.is_B2B_Second_Home == 0) & (row.is_B2B_Second_Away == 1):
            home_prob_adjusted = home_prob_compared * 1.26 * scaler
        elif (row.is_B2B_Second_Home == 1) & (row.is_B2B_Second_Away == 0):
            home_prob_adjusted = home_prob_compared * 1.10 * scaler
        elif (row.is_B2B_Second_Home == 1) & (row.is_B2B_Second_Away == 1):
            home_prob_adjusted = home_prob_compared * 1.16 * scaler
        elif (row.is_B2B_Second_Home == 0) & (row.is_B2B_Second_Away == 0):
            home_prob_adjusted = home_prob_compared * 1.16 * scaler
        else:
            print("There's been a grave mistake")

        # Adjusting home projection to scale to 100%
        # home_prob_compared_2 = home_prob_compared / (home_prob_compared + away_prob_compared)
        away_prob_adjusted = 1.0 - home_prob_adjusted                                                                                                     

        # Adjusting for home court advantage/B2B
        # if (row.is_B2B_Second_Home == 0) & (row.is_B2B_Second_Away == 1):
        #     home_prob_adjusted = home_prob_compared_2 * 1.26
        #     away_prob_adjusted = 1.0 - home_prob_adjusted
        # elif (row.is_B2B_Second_Home == 1) & (row.is_B2B_Second_Away == 0):
        #     home_prob_adjusted = home_prob_compared_2 * 1.10
        #     away_prob_adjusted = (1.0 - home_prob_adjusted)
        # elif (row.is_B2B_Second_Home == 1) & (row.is_B2B_Second_Away == 1):
        #     home_prob_adjusted = home_prob_compared_2 * 1.16
        #     away_prob_adjusted = 1.0 - home_prob_adjusted
        # elif (row.is_B2B_Second_Home == 0) & (row.is_B2B_Second_Away == 0):
        #     home_prob_adjusted = home_prob_compared_2 * 1.16
        #     away_prob_adjusted = (1.0 - home_prob_adjusted)
        # else:
        #     print("There's been a grave mistake")
        
        # Inputting adjusted win percentage
        todays_games.loc[index, 'Home_Prob_Adjusted'] = home_prob_adjusted
        todays_games.loc[index, 'Away_Prob_Adjusted'] = away_prob_adjusted

    # Add underlying probability of odds to df
    todays_games['Home_Odds'] = 0
    todays_games['Away_Odds'] = 0
    todays_games['Home_Prob_Odds'] = 0
    todays_games['Away_Prob_Odds'] = 0
    for index, row in todays_games.iterrows():
        home_team = row.Home
        away_team = row.Away
        todays_games.loc[index, 'Home_Prob_Odds'] = todays_odds[todays_odds.Home_Team == home_team]['Home_Prob'].iloc[0]/100.0
        todays_games.loc[index, 'Away_Prob_Odds'] = todays_odds[todays_odds.Away_Team == away_team]['Away_Prob'].iloc[0]/100.0
        todays_games.loc[index, 'Home_Odds'] = todays_odds[todays_odds.Home_Team == home_team]['Home_Odds'].iloc[0]
        todays_games.loc[index, 'Away_Odds'] = todays_odds[todays_odds.Home_Team == home_team]['Away_Odds'].iloc[0]

    # Creating columns to feed into kelly formula
    todays_games['Home_Prob_Diff'] = todays_games.Home_Prob_Adjusted - todays_games.Home_Prob_Odds
    todays_games['Away_Prob_Diff'] = todays_games.Away_Prob_Adjusted - todays_games.Away_Prob_Odds

    # Creating column of Kelly recommendation
    todays_games['Home_Bet_Size'] = 0
    todays_games['Away_Bet_Size'] = 0
    for index, row in todays_games.iterrows():

        # Home Kelly Recommendation
        if row.Home_Prob_Diff < 0:
            todays_games.loc[index, 'Home_Bet_Size'] = 0
        elif row.Home_Prob_Adjusted > 0.95:
            todays_games.loc[index, 'Home_Bet_Size'] = 0
        else:
            p = row.Home_Prob_Adjusted
            q = 1.0 - p
            ml = row.Home_Odds
            if ml>=0:
                b = (ml/100)
            if ml<0:
                b = (100/abs(ml))
            kc = ((p*b) - q) / b
            bet = kc/kelly
            todays_games.loc[index, 'Home_Bet_Size'] = bet
        
        # Away Kelly Recommendation
        if row.Away_Prob_Diff < 0:
            todays_games.loc[index, 'Away_Bet_Size'] = 0
        else:
            p = row.Away_Prob_Adjusted
            q = 1.0 - p
            ml = row.Away_Odds
            if ml>=0:
                b = (ml/100)
            if ml<0:
                b = (100/abs(ml))
            kc = ((p*b) - q) / b
            bet = kc/kelly
            todays_games.loc[index, 'Away_Bet_Size'] = bet
    
    # Creating bet columns
    todays_games['Home_Bet'] = todays_games.Home_Bet_Size * capital
    todays_games['Away_Bet'] = todays_games.Away_Bet_Size * capital

    # Creating Payoff column
    todays_games['Potential_Payoff'] = 0
    for index, row in todays_games.iterrows():
        if row.Home_Bet > 0:
            if row.Home_Odds < 0:
                todays_games.loc[index, 'Potential_Payoff'] = (row.Home_Bet/abs(row.Home_Odds))*100
            if row.Home_Odds > 0:
                todays_games.loc[index, 'Potential_Payoff'] = row.Home_Bet * (row.Home_Odds/100)
        if row.Away_Bet > 0:
            if row.Away_Odds < 0:
                todays_games.loc[index, 'Potential_Payoff'] = (row.Away_Bet/abs(row.Away_Odds))*100
            if row.Away_Odds > 0:
                todays_games.loc[index, 'Potential_Payoff'] = row.Away_Bet * (row.Away_Odds/100)
    
    # Adding date column
    todays_games['Date'] = dt.date.today()

    # Saving today's bets
    if save:
        todays_games.to_csv('In_Season/Data/todays_bets.csv')

    return todays_games, todays_odds

def calculate_yesterdays_bet_results(capital, first_run = False):

    # Initializing necessary objects
    yesterday_bets = pd.read_csv('In_Season/Data/todays_bets.csv', index_col = 0)
    team_map_results = {
        'LAL' : 'Los Angeles Lakers',
        'LAC' : 'Los Angeles Clippers',
        'POR' : 'Portland Trailblazers',
        'CLE' : 'Cleveland Cavaliers',
        'DEN' : 'Denver Nuggets',
        'DAL' : 'Dallas Mavericks',
        'UTA' : 'Utah Jazz',
        'SA' : 'San Antonio Spurs',
        'ATL' : 'Atlanta Hawks',
        'CHA' : 'Charlotte Hornets',
        'CHI' : 'Chicago Bulls',
        'DET' : 'Detroit Pistons',
        'MIL' : 'Milwaukee Bucks',
        'ORL' : 'Orlando Magic',
        'MIN' : 'Minnesota Timberwolves',
        'PHO' : 'Phoenix Suns',
        'BOS' : 'Boston Celtics',
        'IND' : 'Indiana Pacers',
        'SAC' : 'Sacramento Kings',
        'TOR' : 'Toronto Raptors',
        'WAS' : 'Washington Wizards',
        'BKN' : 'Brooklyn Nets',
        'NO' : 'New Orleans Pelicans',
        'DAL' : 'Dallas Mavericks',
        'PHI' : 'Philadelphia 76ers',
        'MIA' : 'Miami Heat',
        'MEM' : 'Memphis Grizzlies',
        'GS' : 'Golden State Warriors',
        'NY' : 'New York Knicks',
        'HOU' : 'Houston Rockets',
        'OKC' : 'Oklahoma City Thunder'
    }

    # Instantiating selenium driver
    link = 'https://www.cbssports.com/nba/schedule/'
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(link)

    # Getting table for yesterday's games and formatting
    day_buttons = driver.find_elements_by_class_name("ToggleContainer-text")
    yesterday = day_buttons[0]
    yesterday.click()
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='TableBase']/div/div/table")))
    html_yesterday = driver.page_source
    tables_yesterday = pd.read_html(html_yesterday)
    try:
        yesterday_schedule = tables_yesterday[1]
    except:
        yesterday_schedule = tables_yesterday[0]
    yesterday_schedule = yesterday_schedule[['Away', 'Home', 'Result']]

    # Populating yesterday's schedule w/ winner
    yesterday_schedule['Winner'] = ''
    for index, row in yesterday_schedule.iterrows():
        winner = row.Result[:3]
        yesterday_schedule.loc[index, 'Winner'] = winner
    yesterday_schedule['Winner'] = yesterday_schedule.Winner.str.strip(' ')
    yesterday_schedule['Winner'] = yesterday_schedule.Winner.apply(lambda x: team_map_results[x])

    # Determining if bet hit and calculating running total of capital
    winners = list(yesterday_schedule.Winner.unique())
    yesterday_bets['Won_Bet'] = -1 
    yesterday_bets['Capital'] = capital
    for index, row in yesterday_bets.iterrows():
        if index == 0:
            if row.Home_Bet > 0:
                if row.Home in winners:
                    yesterday_bets.loc[index, 'Won_Bet'] = 1
                    yesterday_bets.loc[index, 'Capital'] = capital + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet'] = 0
                    yesterday_bets.loc[index, 'Capital'] = capital - row.Home_Bet
            if row.Away_Bet > 0:
                if row.Away in winners:
                    yesterday_bets.loc[index, 'Won_Bet'] = 1
                    yesterday_bets.loc[index, 'Capital'] = capital + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet'] = 0
                    yesterday_bets.loc[index, 'Capital'] = capital - row.Away_Bet
        else:
            if row.Potential_Payoff == 0:
                yesterday_bets.loc[index, 'Capital'] = yesterday_bets.loc[(index - 1), 'Capital']
            if row.Home_Bet > 0:
                if row.Home in winners:
                    yesterday_bets.loc[index, 'Won_Bet'] = 1
                    yesterday_bets.loc[index, 'Capital'] = yesterday_bets.loc[(index - 1), 'Capital'] + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet'] = 0
                    yesterday_bets.loc[index, 'Capital'] = yesterday_bets.loc[(index - 1), 'Capital'] - row.Home_Bet
            if row.Away_Bet > 0:
                if row.Away in winners:
                    yesterday_bets.loc[index, 'Won_Bet'] = 1
                    yesterday_bets.loc[index, 'Capital'] = yesterday_bets.loc[(index - 1), 'Capital'] + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet'] = 0
                    yesterday_bets.loc[index, 'Capital'] = yesterday_bets.loc[(index - 1), 'Capital'] - row.Away_Bet
    
    # Saving results
    if first_run:
        yesterday_bets.to_csv('In_Season/Data/results_tracker.csv')
    else:
        results = pd.read_csv('In_Season/Data/results_tracker.csv', index_col = 0)
        results = results.append(yesterday_bets)
        results.reset_index(drop = True, inplace = True)
        results.to_csv('In_Season/Data/results_tracker.csv')

    return yesterday_bets, winners

# Functions to calculate external bets and results for

def calculate_todays_bets_external(odds, kelly, capital_538, capital_combined, save = False):

    # Map for 538 scraping
    fivethirtyeight_team_map =  {
        'Pistons' : 'Detroit Pistons',
        'Thunder' : 'Oklahoma City Thunder',
        'Kings' : 'Sacramento Kings',
        'Trail Blazers' : 'Portland Trailblazers',
        'Spurs' : 'San Antonio Spurs',
        'Raptors' : 'Toronto Raptors',
        'Rockets' : 'Houston Rockets',
        'Magic' : 'Orlando Magic',
        'Warriors' : 'Golden State Warriors',
        'Celtics' : 'Boston Celtics',
        'Cavaliers' : 'Cleveland Cavaliers',
        'Mavericks' : 'Dallas Mavericks',
        'Hornets' : 'Charlotte Hornets',
        'Pacers' : 'Indiana Pacers',
        'Grizzlies' : 'Memphis Grizzlies',
        'Wizards' : 'Washington Wizards',
        'Knicks' : 'New York Knicks',
        'Nets' : 'Brooklyn Nets',
        'Bucks' : 'Milwaukee Bucks',
        'Bulls' : 'Chicago Bulls',
        'Pelicans' : 'New Orleans Pelicans',
        'Jazz' : 'Utah Jazz',
        'Nuggets' : 'Denver Nuggets',
        'Clippers' : 'Los Angeles Clippers',
        'Lakers' : 'Los Angeles Lakers',
        '76ers' : 'Philadelphia 76ers',
        'Hawks' : 'Atlanta Hawks',
        'Heat' : 'Miami Heat',
        'Timberwolves' : 'Minnesota Timberwolves',
        'Suns' : 'Phoenix Suns'
    }

    # Scraping data from 538
    tables = pd.read_html(f'https://projects.fivethirtyeight.com/{current_year}-nba-predictions/games/')
    fivethirtyeight_data = pd.DataFrame(columns = ['Date', 'Away_Team', 'Away_Prob', 'Home_Team', 'Home_Prob'])
    for i, table in enumerate(tables):
        if i == 0:
            continue
        if i > 30:
            break
        if i % 2 == 0:
            matchup_data = table.iloc[:, [2,4]]
            matchup_data.drop(2, axis = 0, inplace = True)
            matchup_data.columns = ['Teams', 'Probability']
            away_team = matchup_data.loc[0, 'Teams']
            away_prob = matchup_data.loc[0, 'Probability']
            home_team = matchup_data.loc[1, 'Teams']
            home_prob = matchup_data.loc[1, 'Probability']
            date = dt.date.today()
            data_series = pd.Series([date, away_team, away_prob, home_team, home_prob], index = fivethirtyeight_data.columns)
            fivethirtyeight_data = fivethirtyeight_data.append(data_series, ignore_index = True)

    # Changing team names using team map
    fivethirtyeight_data['Home_Team'] = fivethirtyeight_data.Home_Team.apply(lambda x: fivethirtyeight_team_map[x])
    fivethirtyeight_data['Away_Team'] = fivethirtyeight_data.Away_Team.apply(lambda x: fivethirtyeight_team_map[x])



    # Merging dfs and adjusting column names
    merged = pd.merge(fivethirtyeight_data, odds, on = ['Home_Team', 'Away_Team'])
    merged.columns = ['Date', 'Away_Team', 'Away_Prob', 'Home_Team', 'Home_Prob', 'Home_Odds', 'Away_Odds', 
                    'Home_Prob_Implied', 'Away_Prob_Implied']

    # Formatting columns
    merged['Away_Prob'] = merged.Away_Prob.str.strip('%')
    merged['Away_Prob'] = merged.Away_Prob.astype(float)
    merged['Away_Prob'] = merged.Away_Prob/100
    merged['Home_Prob'] = merged.Home_Prob.str.strip('%')
    merged['Home_Prob'] = merged.Home_Prob.astype(float)
    merged['Home_Prob'] = merged.Home_Prob/100
    merged['Home_Prob_Implied'] = merged.Home_Prob_Implied/100
    merged['Away_Prob_Implied'] = merged.Away_Prob_Implied/100

    # Creating columns for bet size and potential payoff
    merged['Home_Prob_Diff'] = merged.Home_Prob - merged.Home_Prob_Implied
    merged['Away_Prob_Diff'] = merged.Away_Prob - merged.Away_Prob_Implied
    merged['Home_Bet_Size'] = 0
    merged['Away_Bet_Size'] = 0

    # Calculating 538 bets and payoffs
    for index, row in merged.iterrows():

        # Home Kelly Recommendation
        if row.Home_Prob_Diff < 0:
            merged.loc[index, 'Home_Bet_Size'] = 0
        else:
            p = row.Home_Prob
            q = 1.0 - p
            ml = row.Home_Odds
            if ml>=0:
                b = (ml/100)
            if ml<0:
                b = (100/abs(ml))
            kc = ((p*b) - q) / b
            bet = kc/kelly
            merged.loc[index, 'Home_Bet_Size'] = bet

        # Away Kelly Recommendation
        if row.Away_Prob_Diff < 0:
            merged.loc[index, 'Away_Bet_Size'] = 0
        else:
            p = row.Away_Prob
            q = 1.0 - p
            ml = row.Away_Odds
            if ml>=0:
                b = (ml/100)
            if ml<0:
                b = (100/abs(ml))
            kc = ((p*b) - q) / b
            bet = kc/kelly
            merged.loc[index, 'Away_Bet_Size'] = bet

    # Creating bet columns
    merged['Home_Bet'] = merged.Home_Bet_Size * capital_538
    merged['Away_Bet'] = merged.Away_Bet_Size * capital_538

    # Creating Payoff column
    merged['Potential_Payoff'] = 0
    for index, row in merged.iterrows():
        if row.Home_Bet > 0:
            if row.Home_Odds < 0:
                merged.loc[index, 'Potential_Payoff'] = (row.Home_Bet/abs(row.Home_Odds))*100
            if row.Home_Odds > 0:
                merged.loc[index, 'Potential_Payoff'] = row.Home_Bet * (row.Home_Odds/100)
        if row.Away_Bet > 0:
            if row.Away_Odds < 0:
                merged.loc[index, 'Potential_Payoff'] = (row.Away_Bet/abs(row.Away_Odds))*100
            if row.Away_Odds > 0:
                merged.loc[index, 'Potential_Payoff'] = row.Away_Bet * (row.Away_Odds/100)






    # Calling in todays bets and diluting to necessary columns
    bets = pd.read_csv('In_Season/Data/todays_bets.csv', index_col = 0)
    bets = bets[['Away', 'Home', 'Home_Prob_Adjusted', 'Away_Prob_Adjusted']]
    bets.columns = ['Away_Team', 'Home_Team', 'Home_Prob_Adjusted', 'Away_Prob_Adjusted']

    # Merging and creating combined probs
    combined = pd.merge(merged, bets, on = ['Home_Team', 'Away_Team'])
    combined['Home_Prob_Combined'] = (combined.Home_Prob + combined.Home_Prob_Adjusted)/2
    combined['Away_Prob_Combined'] = (combined.Away_Prob + combined.Away_Prob_Adjusted)/2

    # Creating columns for bet recommendation
    combined['Home_Prob_Diff_Combined'] = combined.Home_Prob_Combined - combined.Home_Prob_Implied
    combined['Away_Prob_Diff_Combined'] = combined.Away_Prob_Combined - combined.Away_Prob_Implied
    combined['Home_Bet_Size_Combined'] = 0
    combined['Away_Bet_Size_Combined'] = 0

    # Calculating combined bets and payoffs
    for index, row in combined.iterrows():

        # Home Kelly Recommendation
        if row.Home_Prob_Diff_Combined < 0:
            combined.loc[index, 'Home_Bet_Size_Combined'] = 0
        else:
            p = row.Home_Prob_Combined
            q = 1.0 - p
            ml = row.Home_Odds
            if ml>=0:
                b = (ml/100)
            if ml<0:
                b = (100/abs(ml))
            kc = ((p*b) - q) / b
            bet = kc/kelly
            combined.loc[index, 'Home_Bet_Size_Combined'] = bet

        # Away Kelly Recommendation
        if row.Away_Prob_Diff_Combined < 0:
            combined.loc[index, 'Away_Bet_Size_Combined'] = 0
        else:
            p = row.Away_Prob_Combined
            q = 1.0 - p
            ml = row.Away_Odds
            if ml>=0:
                b = (ml/100)
            if ml<0:
                b = (100/abs(ml))
            kc = ((p*b) - q) / b
            bet = kc/kelly
            combined.loc[index, 'Away_Bet_Size_Combined'] = bet

    # Creating bet columns
    combined['Home_Bet_Combined'] = combined.Home_Bet_Size_Combined * capital_combined
    combined['Away_Bet_Combined'] = combined.Away_Bet_Size_Combined * capital_combined

    # Creating Payoff column
    combined['Potential_Payoff_Combined'] = 0
    for index, row in combined.iterrows():
        if row.Home_Bet_Combined > 0:
            if row.Home_Odds < 0:
                combined.loc[index, 'Potential_Payoff_Combined'] = (row.Home_Bet_Combined/abs(row.Home_Odds))*100
            if row.Home_Odds > 0:
                combined.loc[index, 'Potential_Payoff_Combined'] = row.Home_Bet_Combined * (row.Home_Odds/100)
        if row.Away_Bet_Combined > 0:
            if row.Away_Odds < 0:
                combined.loc[index, 'Potential_Payoff_Combined'] = (row.Away_Bet_Combined/abs(row.Away_Odds))*100
            if row.Away_Odds > 0:
                combined.loc[index, 'Potential_Payoff_Combined'] = row.Away_Bet_Combined * (row.Away_Odds/100)

    # Saving output
    if save:
        file_name = 'In_Season/Data/todays_bets_external.csv'
        combined.to_csv(file_name)


    return combined

def calculate_yesterdays_bet_results_external(winners, capital_538, capital_combined, first_run = False):

    # Initializing necessary objects
    yesterday_bets = pd.read_csv('In_Season/Data/todays_bets_external.csv', index_col = 0)  

    # Determining if bet hit and calculating running total of capital

    yesterday_bets['Won_Bet_538'] = -1 
    yesterday_bets['Won_Bet_Combined'] = -1 
    yesterday_bets['Capital_538'] = capital_538
    yesterday_bets['Capital_Combined'] = capital_combined
    for index, row in yesterday_bets.iterrows():
        if index == 0:
            
            # 538
            if row.Home_Bet > 0:
                if row.Home_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 1
                    yesterday_bets.loc[index, 'Capital_538'] = capital_538 + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 0
                    yesterday_bets.loc[index, 'Capital_538'] = capital_538 - row.Home_Bet
            if row.Away_Bet > 0:
                if row.Away_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 1
                    yesterday_bets.loc[index, 'Capital_538'] = capital_538 + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 0
                    yesterday_bets.loc[index, 'Capital_538'] = capital_538 - row.Away_Bet
            
            # Combined
            if row.Home_Bet_Combined > 0:
                if row.Home_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 1
                    yesterday_bets.loc[index, 'Capital_Combined'] = capital_combined + row.Potential_Payoff_Combined
                else:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 0
                    yesterday_bets.loc[index, 'Capital_Combined'] = capital_combined - row.Home_Bet_Combined
            if row.Away_Bet_Combined > 0:
                if row.Away_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 1
                    yesterday_bets.loc[index, 'Capital_Combined'] = capital_combined + row.Potential_Payoff_Combined
                else:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 0
                    yesterday_bets.loc[index, 'Capital_Combined'] = capital_combined - row.Away_Bet_Combined
        else:
            
            # 538
            if row.Potential_Payoff == 0:
                yesterday_bets.loc[index, 'Capital_538'] = yesterday_bets.loc[(index - 1), 'Capital_538']
            if row.Home_Bet > 0:
                if row.Home_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 1
                    yesterday_bets.loc[index, 'Capital_538'] = yesterday_bets.loc[(index - 1), 'Capital_538'] + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 0
                    yesterday_bets.loc[index, 'Capital_538'] = yesterday_bets.loc[(index - 1), 'Capital_538'] - row.Home_Bet
            if row.Away_Bet > 0:
                if row.Away_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 1
                    yesterday_bets.loc[index, 'Capital_538'] = yesterday_bets.loc[(index - 1), 'Capital_538'] + row.Potential_Payoff
                else:
                    yesterday_bets.loc[index, 'Won_Bet_538'] = 0
                    yesterday_bets.loc[index, 'Capital_538'] = yesterday_bets.loc[(index - 1), 'Capital_538'] - row.Away_Bet
            
            # Combined
            if row.Potential_Payoff_Combined == 0:
                yesterday_bets.loc[index, 'Capital_Combined'] = yesterday_bets.loc[(index - 1), 'Capital_Combined']
            if row.Home_Bet_Combined > 0:
                if row.Home_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 1
                    yesterday_bets.loc[index, 'Capital_Combined'] = yesterday_bets.loc[(index - 1), 'Capital_Combined'] + row.Potential_Payoff_Combined
                else:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 0
                    yesterday_bets.loc[index, 'Capital_Combined'] = yesterday_bets.loc[(index - 1), 'Capital_Combined'] - row.Home_Bet_Combined
            if row.Away_Bet_Combined > 0:
                if row.Away_Team in winners:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 1
                    yesterday_bets.loc[index, 'Capital_Combined'] = yesterday_bets.loc[(index - 1), 'Capital_Combined'] + row.Potential_Payoff_Combined
                else:
                    yesterday_bets.loc[index, 'Won_Bet_Combined'] = 0
                    yesterday_bets.loc[index, 'Capital_Combined'] = yesterday_bets.loc[(index - 1), 'Capital_Combined'] - row.Away_Bet_Combined
        
        # Saving results
        if first_run:
            yesterday_bets.to_csv('In_Season/Data/results_tracker_external.csv')
        else:
            results = pd.read_csv('In_Season/Data/results_tracker_external.csv', index_col = 0)
            results = results.append(yesterday_bets)
            results.reset_index(drop = True, inplace = True)
            results.to_csv('In_Season/Data/results_tracker_external.csv')
            
        return yesterday_bets

# Function to send email with today's bets

def send_email():
    subject = "Today's recommended NBA bets"
    body = "Attached are the recommended bets for today"
    sender_email = "henrysinger24@gmail.com"
    receiver_email = "henrysinger24@gmail.com"
    password = 'Tennessee24'

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    filename = 'In_Season/Data/todays_bets.csv'  # In same directory as script

    # Open PDF file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

    return

##########RUN################

### Calculating results from yesterday

# Proprietary
results = pd.read_csv('In_Season/Data/results_tracker.csv')
yesterday_capital = results.loc[len(results)-1, 'Capital']
results, winners = calculate_yesterdays_bet_results(capital = yesterday_capital, first_run = True)

# External
# results = pd.read_csv('In_Season/Data/results_tracker_external.csv')
# capital_538 = results.loc[len(results)-1, 'Capital_538']
# capital_combined = results.loc[len(results)-1, 'Capital_Combined']
capital_combined = 100000
capital_538 = 100000
results = calculate_yesterdays_bet_results_external(winners = winners, capital_538 = capital_538,
                                capital_combined = capital_combined, first_run = True)

### Calculate todays bets

# Proprietary
results = pd.read_csv('In_Season/Data/results_tracker.csv')
today_capital = results.loc[len(results)-1, 'Capital']
team_vorp_df, missed_players, frac_season = calculate_current_day_team_vorp(current_year)
projected_win_pct_table = calculate_current_day_win_pct(team_vorp_df, frac_season)
bets, odds = calculate_todays_bets(projected_win_pct_table, kelly, capital = today_capital, save = True)
print(bets)
print(missed_players)
send_email()

# External

results = pd.read_csv('In_Season/Data/results_tracker_external.csv')
capital_538 = results.loc[len(results)-1, 'Capital_538']
capital_combined = results.loc[len(results)-1, 'Capital_Combined']
calculate_todays_bets_external(odds = odds, kelly = kelly, capital_538 = capital_538, capital_combined = capital_combined, save = True)
