# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 13:08:09 2017

@author: ning
"""

from bs4 import BeautifulSoup as bs # tools to collect xml data
import pandas as pd # put everything into a table (dataframe)
import numpy as np
from urllib.request import urlopen # open an url
from matplotlib import pyplot as plt
import re # string matching
import seaborn as sns # beautiful plotting
from tqdm import tqdm # to iterate through a counter


def detect_star(x):
    # if there is a star ('*') behind a team's name, it means it went to the 
    # playoffs that season, otherwise, not.
    if '*' in x:
        return True
    else:
        return 'no playoffs'
def hasNumbers(inputString):
    # to check weather a string contains number digits
    return any(char.isdigit() for char in inputString)
def find_team(x,):
    # search through the data frame and find the rows that contain the team
    # name we determine outside this function, which is why the variable 
    # "team_name" a global variable
    global team_name
    keyword = re.compile(team_name,re.IGNORECASE) # prepare the team's name as a keyword for searching
    if keyword.search(x) is not None:
        # any match, return true
        return True
    else:
        return False
def get_table(url_,id_='all_misc_stats',skip_row=1,season=True):
    """
    Arguments:
        url_: string of url
        id_ : html id used in the website
        skip_row: for some cases, we need to skip the first row, but for the others, we don't
        season: if true, we are parsing the data of regular season
                if false, we are parsing the data of playoffs
                
    return:
        df: a data frame contains these columns:
            'Rk', 'Team', 'Age', 'W', 'L', 'PW', 'PL', 'MOV', 'SOS', 'SRS', 'ORtg',
       'DRtg', 'Pace', 'FTr', '3PAr', 'TS%', 'eFG%', 'TOV%', 'ORB%', 'FT/FGA',
       'eFG%.1', 'TOV%.1', 'DRB%', 'FT/FGA.1', 'Arena', 'Attendance',
       'playoffs', 'season'
       reference: https://www.basketball-reference.com/leagues/
    
    """
    soup = bs(urlopen(url_),'lxml') # open an url for one season, and parse to beautifulsoup object
    table = soup.find('div',{'id':id_})# get the table content based on the xml id
    content_field = [temp for temp in table if (temp != '\n')] # the table variable is a multi-element list, and some of them are only for wrapping to the next line: \n
    content_field = content_field[-1] # the last element of the list is always irrelevant
    parse_to_html = bs(content_field, 'html.parser')# re-parse the strings to a beautifulsoup object
    for body in parse_to_html('tbody'):# in the beautifulsoup object, we unwrap the contents if they are in the table body
        body.unwrap()
    # for the data of regular season, we skip the first row, which is the name of the table, not the headers
    df = pd.read_html(str(parse_to_html),flavor="bs4",header=skip_row)
    df = df[0]# for some reason, pandas returns a list
    
    if season:
        df['playoffs'] = df['Team'].apply(detect_star) # for the teams that don't get in the playoffs
        df['season'] = re.findall('\d+',url_)[0] # this is the year when the playoffs take place
    return df
def normalize(x):
    # you don't normalization?
    return (x - x.mean())/x.std()
url = 'https://www.basketball-reference.com/leagues/'
# get the page to become a beautifulsoup object for the url above
soup = bs(urlopen(url),'lxml')
# get the first table, which is also the only table of this web page
Index_ = soup.find('div',{'id':'content'})
# get the column "season"
rows = Index_.findAll('th',{'data-stat':'season'})
# I don't need the header, or the seasons before 1955
rows = rows[1:-9]
url_all_seasons=[]
for c in rows:
    j=c.find('a',href=True) # get the link url for each season since 1955
    season = j['href'] # this is the link in string
    url_season = url[:-9] + season # make a readable url string
    url_all_seasons.append(url_season)# save the url string for each season since 1955
url_all_seasons=[s for s in url_all_seasons if ('NBA' in s)]# don't care ABA seasons

seasons_stats = []
for url_ in tqdm(url_all_seasons):
    if '2018' not in url_:
        df_season = get_table(url_,) # parse the data of regular season to a data frame
        # parse the data of the playoffs of the same season to a data frame
        df_playoffs = get_table(url_,id_='all_all_playoffs',skip_row=None,season=False)
        # the rounds, like first round, semifinals, finals are in the first column
        playoff_rounds = df_playoffs[0]
        # a complicated way to get rows that contain the names of rounds I want
        k = [f for f in playoff_rounds.to_string().split('\n') if ('Finals' in f) or ('Division' in f) or ('Conference' in f)]
        # after I use "to_string", the index of the row concatenate to the content and becomes a single string variable,
        # thus, I need to use the regular expression to match the row indeces
        row_index = [int(re.findall('\d+', strings)[0]) for strings in k]
        # the teams that play the first round, semifinals, finals
        playoff_teams = df_playoffs[1]
        # use the row indeces to get the rows of teams matching we need, same as the rows for the games in the next line
        teams = playoff_teams[row_index].to_string().split('\n')
        games = playoff_rounds[row_index]
        results_ = []
        for ii, (game_,teams_) in enumerate(zip(games,teams)):
            # game_ contains maybe Finals
            # teams_ contains both sides, and they are seperated by the word: over
            teams_ = [re.findall('\w+',tt) for tt in teams_.split(' over ')]
            team1 = ' '.join(teams_[0][1:])# the first element is a number we don't need
            
            team2 = ' '.join(teams_[1])# just get the full string for the second team, but we will need further process
            while len(re.findall('\d+',team2)) > 0:
                # the string variable for the second team contains irregular length of digits
                # the while loop is to eliminate the digit (if any) one by one
                team2 = team2[:-2]
            # handle specially string matching cases
            if 'St ' in team1:
                team1 = 'St. ' + team1[3:]
            if 'St ' in team2:
                team2 = 'St. ' + team2[3:]
            if 'Omaha' in team2:
                team2 = 'Kansas City-Omaha Kings'
            results_.append([game_,team1,team2])
            
        for game,team1,team2 in results_[::-1]:# reverse the list of games because we want to update the teams that play in these games from low level (first round) to high level (Finals)
            team_name = team1 # make the team_name variable and use it globally
            row_of_team1 = df_season['Team'].apply(find_team) # row index of that team in the data of regular season
            team_name = team2
            row_of_team2 = df_season['Team'].apply(find_team)
            logical_index = np.logical_or(row_of_team1,row_of_team2) # make a logical or combination of two teams' row index
            df_season['playoffs'][logical_index] = game # game is a string: could be "first round", "semifinals", "finals"
        # normalize the offensive and defensive rates within the same season
        df_season['ORtg']=normalize(df_season['ORtg'])
        df_season['DRtg']=normalize(df_season['DRtg'])
        # save the data of one season
        seasons_stats.append(df_season)
    else:
        # since in year 2017, season 17-18 has just started, and no team plays more than 20 games,
        # no team gets into playoffs
        df_season = get_table(url_,)
        df_season['ORtg']=normalize(df_season['ORtg'])
        df_season['DRtg']=normalize(df_season['DRtg'])
        seasons_stats.append(df_season)
    
seasons_stats = pd.concat(seasons_stats) # join all data of the seasons since 1955 to make a big table
seasons_stats.to_csv('season_stats.csv',index=False)# save it

seasons_stats = seasons_stats[seasons_stats['Team'] != 'League Average']# take the rows contain leagure average for each season
# re-code the strings of the playoffs with simplier classifications
recoder = {'Western Conference Finals':'Conference Finals',
           'Western Conference Semifinals':'Conference Semifinals',
           'Western Conference First Round':'First Round',
           'Eastern Conference Semifinals':'Conference Semifinals',
           'Eastern Conference Finals':'Conference Finals',
           'Eastern Conference First Round':'First Round',
           'Eastern Division Finals':'Conference Finals',
           'Eastern Division Semifinals':'Conference Semifinals',
           'Western Division Finals':'Conference Finals',
           'Western Division Semifinals':'Conference Semifinals',
           'Finals':'Finals',
           'no playoffs':'no playoffs',
           'Eastern Division Third Place Tiebreaker':'Eastern Division Third Place Tiebreaker'}
# map the re-code
seasons_stats['playoffs_'] = seasons_stats['playoffs'].map(recoder)
# a convoluted way to reorder the strings
orders = list(pd.unique(seasons_stats['playoffs_']))
orders_ = []
for ii in orders[1:]:
    orders_.append(ii)
orders_.append(orders[0])

# make sure no figures in the memory
plt.close('all')
# seaborn lmplot: https://seaborn.pydata.org/generated/seaborn.lmplot.html
g=sns.lmplot(x='ORtg',y='DRtg',data=seasons_stats,hue='playoffs_',fit_reg=False,palette='coolwarm',hue_order=orders_,size=8,
             x_jitter=0.01,y_jitter=0.01)
g.set(xlabel='Offense rating',ylabel='Defense rating',title='1955 - 2018 season')

# add extra annotations to the figure
team_select = 'Chicago Bulls'   # the name of the team we want to see  
season_select = '1996'  # the year when the team played in the playoffs
textxy=[3,-2]  # we could only determine this after we know the coordinates of the team
team_name = team_select# update global variable "team_name"
print(season_select,team_select)# print to check
# a join condition of the team and season, and the join condition should return one True
team_idx = np.logical_and((seasons_stats['season'] == season_select) , (seasons_stats['Team'].apply(find_team)))
# I am just lazy to create a new variable to save the values
team_idx = seasons_stats[team_idx][['ORtg','DRtg']].values[0]
print(team_name,team_idx)
# add the annotation to the axes, with an arrow
g.fig.axes[0].annotate('%s-%s'%(team_select,season_select),xy=(team_idx[0],team_idx[1]),xytext=(textxy[0],textxy[1]),
              arrowprops=dict(facecolor='black', shrink=0.05))


team_select = 'Golden State Warriors'    
season_select = '2017'    
textxy=[3,-1.5]
team_name = team_select
print(season_select,team_select)
team_idx = np.logical_and((seasons_stats['season'] == season_select) , (seasons_stats['Team'].apply(find_team)))
team_idx = seasons_stats[team_idx][['ORtg','DRtg']].values[0]
print(team_name,team_idx)
g.fig.axes[0].annotate('%s-%s'%(team_select,season_select),xy=(team_idx[0],team_idx[1]),xytext=(textxy[0],textxy[1]),
              arrowprops=dict(facecolor='black', shrink=0.05))

team_select = 'San Antonio Spurs'    
season_select = '2014'    
textxy=[-2,-3]
team_name = team_select
print(season_select,team_select)
team_idx = np.logical_and((seasons_stats['season'] == season_select) , (seasons_stats['Team'].apply(find_team)))
team_idx = seasons_stats[team_idx][['ORtg','DRtg']].values[0]
print(team_name,team_idx)
g.fig.axes[0].annotate('%s-%s'%(team_select,season_select),xy=(team_idx[0],team_idx[1]),xytext=(textxy[0],textxy[1]),
              arrowprops=dict(facecolor='black', shrink=0.05))

team_select = 'Cleveland Cavaliers'    
season_select = '2018'    
textxy=[2,2.5]
team_name = team_select
print(season_select,team_select)
team_idx = np.logical_and((seasons_stats['season'] == season_select) , (seasons_stats['Team'].apply(find_team)))
team_idx = seasons_stats[team_idx][['ORtg','DRtg']].values[0]
print(team_name,team_idx)
g.fig.axes[0].annotate('%s-%s'%(team_select,season_select),xy=(team_idx[0],team_idx[1]),xytext=(textxy[0],textxy[1]),
              arrowprops=dict(facecolor='black', shrink=0.05))

g.fig.savefig('C:\\Users\\ning\\OneDrive\\python works\\NBA project\\Hierarchical_model_of_NBA_score-master\\I dont know.png',dpi=400)


















