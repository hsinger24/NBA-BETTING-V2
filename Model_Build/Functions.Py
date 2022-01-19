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

def calculate_point_differential_win_pct_equation(save = False):
    
    # Scrape data on historical points scored
    years = [2019, 2018, 2017, 2016, 2015, 2014, 2013]
    points_scored_table = pd.DataFrame(columns = ['Team', 'Points_Scored_PG', 'Points_Scored', 
                                                'Year'])
    for year in years:
        link = f'https://www.teamrankings.com/nba/stat/points-per-game?date={str(year)}-10-12'
        tables = pd.read_html(link)
        table = tables[0]
        table = table[['Team', str(year-1)]]
        table.columns = ['Team', 'Points_Scored_PG']
        table['Points_Scored'] = table.Points_Scored_PG*82
        table['Year'] = year
        points_scored_table = points_scored_table.append(table)

    # Scrape data on historical points allowed
    years = [2019, 2018, 2017, 2016, 2015, 2014, 2013]
    points_allowed_table = pd.DataFrame(columns = ['Team', 'Points_Allowed_PG', 'Points_Allowed', 
                                                'Year'])
    for year in years:
        link = f'https://www.teamrankings.com/nba/stat/opponent-points-per-game?date={str(year)}-06-14'
        tables = pd.read_html(link)
        table = tables[0]
        table = table[['Team', str(year-1)]]
        table.columns = ['Team', 'Points_Allowed_PG']
        table['Points_Allowed'] = table.Points_Allowed_PG*82
        table['Year'] = year
        points_allowed_table = points_allowed_table.append(table)

    # Scrape data on historical win percentage 
    years = [2019, 2018, 2017, 2016, 2015, 2014, 2013]
    win_pct_table = pd.DataFrame(columns = ['Team', 'Win_Pct', 'Year'])
    for year in years:
        link = f'https://www.teamrankings.com/nba/stat/win-pct-all-games?date={str(year)}-06-14'
        tables = pd.read_html(link)
        table = tables[0]
        table = table[['Team', str(year-1)]]
        table.columns = ['Team', 'Win_Pct']
        table['Year'] = year
        win_pct_table = win_pct_table.append(table)

    # Merge three tables
    merged = pd.merge(points_scored_table, points_allowed_table, on = ['Team', 'Year'], how = 'inner')
    merged = merged[['Team', 'Year', 'Points_Scored', 'Points_Allowed']]
    merged['Point_Differential'] = merged.Points_Scored - merged.Points_Allowed
    merged = pd.merge(merged, win_pct_table, on = ['Team', 'Year'], how = 'inner')

    # Calculate linear regression
    x = merged[['Point_Differential']]
    y = merged.Win_Pct
    model = LinearRegression()
    model.fit(x,y)
    # r_squared = model.score(x,y)
    # print('The y-intercept is: ', model.intercept_)
    # print('The slope is: ', model.coef_)
    # print('The r-squared is: ', r_squared)

    # Save regression results
    if save:
        file_name = 'Model_Build/Data/win_pct_regression.pickle'
        with open(file_name, 'wb') as f:
            pickle.dump(model, f)
    
    return merged, model

def calculate_vorp_win_pct_equation(merged, save = False):

    # Creating team maps to change team names in order to create a matching column
    team_map = {
        'TOR' : 'Toronto Raptors',
        'MEM' : 'Memphis Grizzlies',
        'MIA' : 'Miami Heat',
        'BRK' : 'Brooklyn Nets',
        'NOP' : 'New Orleans Pelicans',
        'NOH' : 'New Orleans Hornets',
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
        'CHA' : 'Charlotte Hornets',
        'CHI' : 'Chicago Bulls',
        'ATL' : 'Atlanta Hawks',
        'NYK' : 'New York Knicks',
        'DEN' : 'Denver Nuggets',
        'PHI' : 'Philadelphia 76ers',
        'SAS' : 'San Antonio Spurs',
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

    team_map_differential = {
    'Milwaukee' : 'Milwaukee Bucks',
    'Golden State' : 'Golden State Warriors',
    'New Orleans' : 'New Orleans Pelicans',
    'LA Clippers' : 'Los Angeles Clippers',
    'Philadelphia' : 'Philadelphia 76ers',
    'Sacramento' : 'Sacramento Kings',
    'Washington' : 'Washington Wizards',
    'Okla City' : 'Oklahoma City Thunder',
    'Portland' : 'Portland Trailblazers',
    'Atlanta' : 'Atlanta Hawks',
    'Houston' : 'Houston Rockets',
    'Toronto' : 'Toronto Raptors',
    'Minnesota' : 'Minnesota Timberwolves',
    'Brooklyn' : 'Brooklyn Nets',
    'LA Lakers' : 'Los Angeles Lakers',
    'Boston' : 'Boston Celtics',
    'San Antonio' : 'San Antonio Spurs',
    'Utah' : 'Utah Jazz',
    'Charlotte' : 'Charlotte Hornets',
    'Denver' : 'Denver Nuggets',
    'Dallas' : 'Dallas Mavericks',
    'Phoenix' : 'Phoenix Suns',
    'Indiana' : 'Indiana Pacers',
    'Detroit' : 'Detroit Pistons',
    'Orlando' : 'Orlando Magic',
    'Miami' : 'Miami Heat',
    'Chicago' : 'Chicago Bulls',
    'New York' : 'New York Knicks',
    'Cleveland' : 'Cleveland Cavaliers',
    'Memphis' : 'Memphis Grizzlies'
    }

    # Retrieving cumulative VORP for each team over the relevant timeframe
    years = [2019, 2018, 2017, 2016, 2015, 2014, 2013]
    vorp_table = pd.DataFrame(columns = ['Team', 'VORP', 'Year'])
    for year in years:
        tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(year)}_advanced.html')
        table = tables[0]
        table = table[['Player', 'Tm', 'VORP']]
        table.columns = ['Player', 'Team', 'VORP']
        table = table[table.Team != 'Tm']
        table['Team'] = table.Team.apply(lambda x: team_map[x])
        table['VORP'] = table.VORP.apply(pd.to_numeric)
        team_vorp = table.groupby('Team')['VORP'].sum()
        team_vorp = pd.DataFrame(team_vorp)
        team_vorp.reset_index(drop = False, inplace = True)
        team_vorp.columns = ['Team', 'VORP']
        team_vorp['Year'] = year
        vorp_table = vorp_table.append(team_vorp)
    

    # Merging point differential and VORP tables
    merged['Team'] = merged.Team.apply(lambda x: team_map_differential[x])
    merged_all = pd.merge(vorp_table, merged, on = ['Team', 'Year'], how = 'inner')
    merged_all = merged_all[['Team', 'Year', 'VORP', 'Point_Differential']]
    
    # Performing linear regression on VORP and win_pct
    x = merged_all[['VORP']]
    y = merged_all.Point_Differential
    model = LinearRegression()
    model.fit(x,y)
    # r_squared = model.score(x,y)
    # print('The y-intercept is: ', model.intercept_)
    # print('The slope is: ', model.coef_)
    # print('The r-squared is: ', r_squared)

    # Saving model to data folder
    if save:
        file_name = 'Model_Build/Data/vorp_regression.pickle'
        with open(file_name, 'wb') as f:
            pickle.dump(model, f)

    return model

def calculate_vorp_projection_equation(save = False):

    # Creating dataset
    years = [2019, 2018, 2017, 2016, 2015, 2014]
    dataset_columns = ['Player', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 
                    'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48',
                    'OBPM', 'DBPM', 'BPM', 'VORP_Prior_Year']
    dataset = pd.DataFrame(columns = dataset_columns)

    for year in years:
        # Getting VORP for a given year
        tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(year)}_advanced.html')
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
        player_vorp['Year'] = year
        
        # Getting predictive advanced stats from the prior year
        tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(year-1)}_advanced.html')
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
        
        # Merging VORP with prior year's predictive stats
        merged = pd.merge(player_vorp, player_predictive, on = 'Player', how = 'inner')
        
        # Appending to full dataset
        dataset = dataset.append(merged)
    dataset = dataset.dropna()
    
    # Creating linear regression model 
    x = dataset[['Age', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 
                'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48',
                'OBPM', 'DBPM', 'BPM', 'VORP_Prior_Year']]
    y = dataset.VORP
    model = LinearRegression()
    model.fit(x,y)
    # r_squared = model.score(x,y)
    # print('The y-intercept is: ', model.intercept_)
    # print('The slope is: ', model.coef_)
    # print('The r-squared is: ', r_squared)

    # Saving model to data folder
    if save:
        file_name = 'Model_Build/Data/predict_vorp_regression.pickle'
        with open(file_name, 'wb') as f:
            pickle.dump(model, f)

    return model

def calculate_vorp_raptor_equation(save = False):

    # Obtaining historical RAPTOR data
    raptor_df = pd.read_csv('Model_Build/Data/raptor_data.csv', index_col = 0)

    # Obtaining historical VORP data
    years = [2019, 2018, 2017, 2016, 2015, 2014]
    vorp_df = pd.DataFrame(columns = ['Player', 'VORP', 'Year'])
    for year in years:
        # Getting VORP for a given year
        tables = pd.read_html(f'https://www.basketball-reference.com/leagues/NBA_{str(year)}_advanced.html')
        table = tables[0]
        table = table[['Player', 'Tm', 'VORP']]
        table.columns = ['Player', 'Team', 'VORP']
        table = table[table.Team != 'Tm']
        table['VORP'] = table.VORP.apply(pd.to_numeric)
        player_vorp = table.groupby('Player')['VORP'].sum()
        player_vorp = pd.DataFrame(player_vorp)
        player_vorp.reset_index(drop = False, inplace = True)
        player_vorp.columns = ['Player', 'VORP']
        player_vorp['Year'] = year
        vorp_df = vorp_df.append(player_vorp)
    
    # Combining VORP and RAPTOR data
    combined_df = pd.merge(raptor_df, vorp_df, on = ['Player', 'Year'], how = 'inner')

    # Running regression
    x = combined_df[['RAPTOR']]
    y = combined_df.VORP
    model = LinearRegression()
    model.fit(x,y)
    # r_squared = model.score(x,y)
    # print('The y-intercept is: ', model.intercept_)
    # print('The slope is: ', model.coef_)
    # print('The r-squared is: ', r_squared)

    # Saving regression
    if save:
        file_name = 'Model_Build/Data/predict_vorp_regression.pickle'
        with open(file_name, 'wb') as f:
            pickle.dump(model, f)

    return model