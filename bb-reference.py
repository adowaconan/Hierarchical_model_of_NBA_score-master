# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 13:08:09 2017

@author: ning
"""

from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
from urllib.request import urlopen
from matplotlib import pyplot as plt
import re
import seaborn as sns
from tqdm import tqdm


def detect_star(x):
    if '*' in x:
        return True
    else:
        return 'no playoffs'
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)
def find_team(x,):
    global team_name
    keyword = re.compile(team_name,re.IGNORECASE)
    if keyword.search(x) is not None:
        return True
    else:
        return False
def get_table(url_,id_='all_misc_stats',skip_row=1,season=True):
    soup = bs(urlopen(url_),'lxml')
    table = soup.find('div',{'id':id_})
    content_field = [temp for temp in table if (temp != '\n')]
    content_field = content_field[-1]
    parse_to_html = bs(content_field, 'html.parser')
    for body in parse_to_html('tbody'):
        body.unwrap()
        
    df = pd.read_html(str(parse_to_html),flavor="bs4",header=skip_row)
    df = df[0]
    
    if season:
        df['playoffs'] = df['Team'].apply(detect_star)
        df['season'] = re.findall('\d+',url_)[0]
    return df
def normalize(x):
    return (x - x.mean())/x.std()
url = 'https://www.basketball-reference.com/leagues/'
soup = bs(urlopen(url),'lxml')

Index_ = soup.find('div',{'id':'content'})
rows = Index_.findAll('th',{'data-stat':'season'})
rows = rows[1:-9]
url_all_seasons=[]
for c in rows:
    j=c.find('a',href=True)
    season = j['href']
    url_season = url[:-9] + season
    url_all_seasons.append(url_season)
url_all_seasons=[s for s in url_all_seasons if ('NBA' in s)]

seasons_stats = []
for url_ in tqdm(url_all_seasons):
    if '2018' not in url_:
        df_season = get_table(url_,)
        df_playoffs = get_table(url_,id_='all_all_playoffs',skip_row=None,season=False)
        playoff_rounds = df_playoffs[0]
        k = [f for f in playoff_rounds.to_string().split('\n') if ('Finals' in f) or ('Division' in f) or ('Conference' in f)]
        row_index = [int(re.findall('\d+', strings)[0]) for strings in k]
        
        playoff_teams = df_playoffs[1]
        teams = playoff_teams[row_index].to_string().split('\n')
        games = playoff_rounds[row_index]
        results_ = []
        for ii, (game_,teams_) in enumerate(zip(games,teams)):
            
            teams_ = [re.findall('\w+',tt) for tt in teams_.split(' over ')]
            team1 = ' '.join(teams_[0][1:])
            
            team2 = ' '.join(teams_[1])
            while len(re.findall('\d+',team2)) > 0:
                team2 = team2[:-2]
            if 'St ' in team1:
                team1 = 'St. ' + team1[3:]
            if 'St ' in team2:
                team2 = 'St. ' + team2[3:]
            if 'Omaha' in team2:
                team2 = 'Kansas City-Omaha Kings'
            results_.append([game_,team1,team2])
            
        for game,team1,team2 in results_[::-1]:
            team_name = team1
            row_of_team1 = df_season['Team'].apply(find_team)
            team_name = team2
            row_of_team2 = df_season['Team'].apply(find_team)
            logical_index = np.logical_or(row_of_team1,row_of_team2)
            df_season['playoffs'][logical_index] = game
        
        df_season['ORtg']=normalize(df_season['ORtg'])
        df_season['DRtg']=normalize(df_season['DRtg'])
        seasons_stats.append(df_season)
    else:
        df_season = get_table(url_,)
        df_season['ORtg']=normalize(df_season['ORtg'])
        df_season['DRtg']=normalize(df_season['DRtg'])
        seasons_stats.append(df_season)
    
seasons_stats = pd.concat(seasons_stats)
seasons_stats.to_csv('season_stats.csv',index=False)


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
seasons_stats['playoffs_'] = seasons_stats['playoffs'].map(recoder)
orders = list(pd.unique(seasons_stats['playoffs_']))
orders_ = []
for ii in orders[1:]:
    orders_.append(ii)
orders_.append(orders[0])
plt.close('all')
g=sns.lmplot(x='ORtg',y='DRtg',data=seasons_stats,hue='playoffs_',fit_reg=False,palette='coolwarm',hue_order=orders_,size=8,
             x_jitter=None,y_jitter=None)
g.set(xlabel='Offense rating',ylabel='Defense rating',title='1955 - 2018 season')

team_select = 'Chicago Bulls'    
season_select = '1996'  
textxy=[3,-2]  
team_name = team_select
print(season_select,team_select)
team_idx = np.logical_and((seasons_stats['season'] == season_select) , (seasons_stats['Team'].apply(find_team)))
team_idx = seasons_stats[team_idx][['ORtg','DRtg']].values[0]
print(team_name,team_idx)
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
textxy=[2,3]
team_name = team_select
print(season_select,team_select)
team_idx = np.logical_and((seasons_stats['season'] == season_select) , (seasons_stats['Team'].apply(find_team)))
team_idx = seasons_stats[team_idx][['ORtg','DRtg']].values[0]
print(team_name,team_idx)
g.fig.axes[0].annotate('%s-%s'%(team_select,season_select),xy=(team_idx[0],team_idx[1]),xytext=(textxy[0],textxy[1]),
              arrowprops=dict(facecolor='black', shrink=0.05))

g.fig.savefig('D:\\I dont know.png',dpi=400)


















