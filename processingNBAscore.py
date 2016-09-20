# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 13:57:50 2016

@author: ning
"""

from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import pandas as pd
import numpy as np
import math
import re
#import pymc
import matplotlib.pyplot as plt

url='http://www.basketball-reference.com/leagues/NBA_%s.html'

def make_soup(url):
    return bs(urlopen(url),'lxml')
def get_games(date,target='boxscore'):
    '''This works only under espn.com'''
    soup = make_soup(url + '/_/date/%s'%(date))
    scriptObject = soup.find_all('script')
    scriptString = str(scriptObject)
    temp_game_href=[]
    for item in scriptString.split(','):
        if 'href' in item and '%s?gameId'%target in item and 'nba' in item:
            temp_game_href.append(item)
    game_links =[]
    for item in temp_game_href:
        game_link = item.split('":"')[1][:-1]
        game_links.append(game_link)
    return game_links
def get_sec(time_str):
    m, s = time_str.split(':')
    return int(m) * 60 + int(s)
def get_plays(game_links):
    soup=make_soup(game_links)
    totalplayBYplay=[]
    totalTime = 720
    for q in range(4):
        quater = soup.find('div',{'id':'gp-quarter-%d'% (q+1)})
        plays = quater.find_all('tr')#row of table
        tempplayBYplay = [[td.findChildren(text=True) for td in tr.findAll("td")] for tr in plays] # parsing content
        teams=[[str(td.find('img',{'class':'team-logo'})).split('/')[-2][:3] for td in tr.findAll("td",{'class':'logo'})] for tr in plays]
        playBYplay=[]
        for eachplay,team in zip(tempplayBYplay,teams):
            if len(eachplay) == 0:
                pass
            else:
                temp_play=np.concatenate((list(np.array([x for x in eachplay if x != []]).flatten()),team))
                temp_play[0] = totalTime - get_sec(temp_play[0])
                playBYplay.append(temp_play)
        totalTime += 720
        totalplayBYplay.append(playBYplay)
    plays = np.concatenate(totalplayBYplay)
    gameName = np.unique(plays[:,3])[0] + ' @ ' + np.unique(plays[:,3])[1]
    playbyplay=np.concatenate(totalplayBYplay)
    playbyplay=parse_content_to_table(playbyplay)
    return playbyplay, gameName
def parse_content_to_table(plays):
    
    result={    'time played (in sec)': plays[:,0],
                'description': plays[:,1],
                'score'      : plays[:,2],
                'team'       : plays[:,3]}
    return pd.DataFrame(result)
def get_boxscore(game_links):
    soup=make_soup(game_links)
    table_area = soup.find('article',{'class':'boxscore-tabs game-package-box-score'})
    tempTable=[[td.findChildren(text=True) for td in tr.findAll("td")] for tr in table_area.find_all('tr')]
    table_list = ['name','min','FG','3PT','FT','offensive reb','defensive reb','total reb','Ast','Stl','Blk','Turnover','fouls','contribution','points']
    dict_table_A={}
    dict_table_B={}
    for aa in table_list:
        dict_table_A[aa]=[]
        dict_table_B[aa]=[]
    baseline=len(tempTable)
    for ii,row in enumerate(tempTable):
        if len(row) <=1:
            pass
        elif np.array(row)[0] == ['\xa0']:
            pass
        elif ii < baseline:
            if np.array(row)[0] == ['TEAM']:
                baseline = ii + 1
                pass
            elif 'DNP' in np.array(row)[1][0]:
                dict_table_A['name'].append(np.array(row)[0][0])
                for jj,atr in enumerate(table_list[1:]):
                    dict_table_A[atr].append(0)
            else:
                for jj,atr in enumerate(table_list):
                    try:
                        dict_table_A[atr].append(int(np.array(row)[jj][0]))
                    except:
                        dict_table_A[atr].append(np.array(row)[jj][0])
        
        elif ii > baseline:
            if np.array(row)[0] == ['TEAM']:
                pass
            elif 'DNP' in np.array(row)[1][0]:
                dict_table_B['name'].append(np.array(row)[0][0])
                for jj,atr in enumerate(table_list[1:]):
                    dict_table_B[atr].append(0)
            else:
                for jj, atr in enumerate(table_list):
                    try:
                        dict_table_B[atr].append(int(np.array(row)[jj][0]))
                    except:
                        dict_table_B[atr].append(np.array(row)[jj][0])
    return pd.DataFrame(dict_table_A),pd.DataFrame(dict_table_B)
def get_game_score(game_links):
    soup=make_soup(game_links)
    table_area = soup.find('article',{'class':'boxscore-tabs game-package-box-score'})
    tempTable=[[td.findChildren(text=True) for td in tr.findAll("td")] for tr in table_area.find_all('tr')]
    temp_score=[]
    for ii, row in enumerate(np.array(tempTable)):
        if np.array(row).size == 0:
            pass
        elif np.array(row)[0] == ['TEAM']:
            temp_score.append(np.array(row)[-1][0])
    nameItem=soup.find_all('div',{'class':'team-name'})
    tempName=[]
    for item in nameItem:
        try:
            x = str(item).index('.png')
            tempName.append(str(item)[x-4:x].replace('/','').replace('0',''))
        except:
            pass
    gameName = tempName[0]+' @ '+tempName[1]   
    return gameName, str(temp_score[0])+' - '+str(temp_score[1])
def get_game_rebs(game_links):
    soup=make_soup(game_links)
    table_area = soup.find('article',{'class':'boxscore-tabs game-package-box-score'})
    tempTable=[[td.findChildren(text=True) for td in tr.findAll("td")] for tr in table_area.find_all('tr')]
    temp_reb=[]
    for ii, row in enumerate(np.array(tempTable)):
        if np.array(row).size == 0:
            pass
        elif np.array(row)[0] == ['TEAM']:
            temp_reb.append(np.array(row)[7][0])
    nameItem=soup.find_all('div',{'class':'team-name'})
    tempName=[]
    for item in nameItem:
        try:
            x = str(item).index('.png')
            tempName.append(str(item)[x-4:x].replace('/','').replace('0',''))
        except:
            pass
    gameName = tempName[0]+' @ '+tempName[1]   
    return gameName, str(temp_reb[0])+' - '+str(temp_reb[1])
def get_game_d(day = '20150214'):
    games=get_games(day)
    dict_game={}
    for ii,game in enumerate(games):
        plays,gameName=get_plays(game)
        print(gameName)
        dict_game[str(gameName)]=plays
    return dict(day=dict_game)
def get_key_from_value(dictionary,search_val):
    for key, value in dictionary.items():
        if value == search_val:
            return key
map_team_stats = {'team':0,'empty':[1,-2],'field goal':2,'3pt':3,'FT':4,'offreb':5,'defreb':6,'reb':7,
                  'assist':8,'blk':9,'stl':10,'TO':-4,'personal foul':-3,'score':-1}
def get_game_stats(game_links,target='score'):
    soup=make_soup(game_links)
    table_area = soup.find('article',{'class':'boxscore-tabs game-package-box-score'})
    tempTable=[[td.findChildren(text=True) for td in tr.findAll("td")] for tr in table_area.find_all('tr')]
    temp_stats=[]
    target_position=map_team_stats[target]
    for ii, row in enumerate(np.array(tempTable)):
        if np.array(row).size == 0:
            pass
        elif np.array(row)[0] == ['TEAM']:
            temp_stats.append(np.array(row)[target_position][0])
    nameItem=soup.find_all('div',{'class':'team-name'})
    tempName=[]
    for item in nameItem:
        try:
            x = str(item).index('.png')
            tempName.append(str(item)[x-4:x].replace('/','').replace('0',''))
        except:
            pass
    gameName = tempName[0]+' @ '+tempName[1]   
    return gameName, str(temp_stats[0])+' - '+str(temp_stats[1])
def get_stats_from_ESPN(start_date,end_date,save=False,target='score'):
    result={'game':[],target:[]}
    for day in pd.date_range(start_date,end_date):
        day = str(day)[:10].replace('-','')
        print('\n',day,end=',')
        games = get_games(day,target='boxscore')
        print('%d Games' % len(games))
        for game in games:
            gameName,stats = get_game_stats(game,target)
            print(gameName,end=',')
            result['game'].append(gameName)
            result[target].append(stats)
    if save:
        result=pd.DataFrame(result)
        result.to_csv('NBAscore %s.csv'%(start_date[:4]+'-'+end_date[:4]))
    return result
def get_score_from_ESPN(start_date,end_date,save=False):
    result={'game':[],'score':[]}
    for day in pd.date_range(start_date,end_date):
        day = str(day)[:10].replace('-','')
        print('\n',day,end=',')
        games = get_games(day,target='boxscore')
        print('%d Games' % len(games))
        for game in games:
            gameName,score = get_game_score(game)
            print(gameName,end=',')
            result['game'].append(gameName)
            result['score'].append(score)
    if save:
        result=pd.DataFrame(result)
        result.to_csv('NBAscore %s.csv'%(start_date[:4]+'-'+end_date[:4]))
    return result
def get_reb_from_ESPN(start_date,end_date,save=False):
    result={'game':[],'score':[]}
    for day in pd.date_range(start_date,end_date):
        day = str(day)[:10].replace('-','')
        print('\n',day,end=',')
        games = get_games(day,target='boxscore')
        print('%d Games' % len(games))
        for game in games:
            gameName,reb = get_game_rebs(game)
            print(gameName,end=',')
            result['game'].append(gameName)
            result['score'].append(reb)
    if save:
        result=pd.DataFrame(result)
        result.to_csv('NBAreb %s.csv'%(start_date[:4]+'-'+end_date[:4]))
    return result
def create_map(strings):
    values_ = strings.split(' @ ')
    tempDict={}
    for ii,item in enumerate(values_):
        tempDict[item]=ii
    return tempDict
def split_value_string(strings):
    values_ = strings.split(' - ')
    return values_
def parse_string_to_value(table):
    x = pd.DataFrame(table.groupby('game').count())['score']
    tempDict={}
    for item in x.index:
        y = table['score'][table['game']==item]
        tempArray=[]
        for scores in y:
            tempArray.append(list(map(int,split_value_string(scores))))
        if len(tempArray) > 1:
            tempArray = np.array(tempArray).mean(0)
        else:
            tempArray = np.array(tempArray)
        tempDict[item]=tempArray
    return tempDict
def map_dict_team(tempDict):
    for ii,key in enumerate(tempDict.keys()):
        try:
            score = tempDict[key][0][0],tempDict[key][0][1]
        except:
            score = tempDict[key][0],tempDict[key][1]
        away,home = key.split(' @ ')
    return away,home,score
def simulate_season(atts,home, intercept,df,defs):
    """
    Simulate a season once, using one random draw from the mcmc chain. 
    """
    num_samples = atts.trace().shape[0]
    draw = np.random.randint(0, num_samples)
    atts_draw = pd.DataFrame({'att': atts.trace()[draw, :],})
    defs_draw = pd.DataFrame({'def': defs.trace()[draw, :],})
    home_draw = home.trace()[draw]
    intercept_draw = intercept.trace()[draw]
    season = df.copy()
    season = pd.merge(season, atts_draw, left_on='i_home', right_index=True)
    season = pd.merge(season, defs_draw, left_on='i_home', right_index=True)
    season = season.rename(columns = {'att': 'att_home', 'def': 'def_home'})
    season = pd.merge(season, atts_draw, left_on='i_away', right_index=True)
    season = pd.merge(season, defs_draw, left_on='i_away', right_index=True)
    season = season.rename(columns = {'att': 'att_away', 'def': 'def_away'})
    season['home'] = home_draw
    season['intercept'] = intercept_draw
    season['home_theta'] = season.apply(lambda x: math.exp(x['intercept'] + 
                                                           x['home'] + 
                                                           x['att_home'] + 
                                                           x['def_away']), axis=1)
    season['away_theta'] = season.apply(lambda x: math.exp(x['intercept'] + 
                                                           x['att_away'] + 
                                                           x['def_home']), axis=1)
    season['home_scores'] = season.apply(lambda x: np.random.poisson(x['home_theta']), axis=1)
    season['away_scores'] = season.apply(lambda x: np.random.poisson(x['away_theta']), axis=1)
    season['home_outcome'] = season.apply(lambda x: 'win' if x['home_scores'] > x['away_scores'] else 
                                                    'loss' if x['home_scores'] < x['away_scores'] else 'draw', axis=1)
    season['away_outcome'] = season.apply(lambda x: 'win' if x['home_scores'] < x['away_scores'] else 
                                                    'loss' if x['home_scores'] > x['away_scores'] else 'draw', axis=1)
    season = season.join(pd.get_dummies(season.home_outcome, prefix='home'))
    season = season.join(pd.get_dummies(season.away_outcome, prefix='away'))
    return season


def create_season_table(season,teams):
    """
    Using a season dataframe output by simulate_season(), create a summary dataframe with wins, losses, goals for, etc.
    
    """
    g = season.groupby('i_home')    
    home = pd.DataFrame({'home_scores': g.home_scores.sum(),
                         'home_scores_against': g.away_scores.sum(),
                         'home_wins': g.home_win.sum(),
                         'home_draws': g.home_draw.sum(),
                         'home_losses': g.home_loss.sum()
                         })
    g = season.groupby('i_away')    
    away = pd.DataFrame({'away_scores': g.away_scores.sum(),
                         'away_scores_against': g.home_scores.sum(),
                         'away_wins': g.away_win.sum(),
                         'away_draws': g.away_draw.sum(),
                         'away_losses': g.away_loss.sum()
                         })
    df = home.join(away)
    df['wins'] = df.home_wins + df.away_wins
    df['draws'] = df.home_draws + df.away_draws
    df['losses'] = df.home_losses + df.away_losses
    df['points'] = df.wins + df.draws
    df['gf'] = (df.home_scores + df.away_scores)/82
    df['ga'] = (df.home_scores_against + df.away_scores_against)/82
    df['gd'] = df.gf - df.ga
    df = pd.merge(teams, df, left_on='i', right_index=True)
    df = df.sort_index(by='points', ascending=False)
    df = df.reset_index()
    df['position'] = df.index + 1
    df['champion'] = (df.position == 1).astype(int)
    df['qualified_for_final_4'] = (df.position < 4).astype(int)
    df['no_playoffs'] = (df.position > 16).astype(int)
    return df  
    
def simulate_seasons(atts,home, intercept,df, defs,teams,n=100):
    dfs = []
    for i in range(n):
        s = simulate_season(atts,home, intercept,df,defs)
        t = create_season_table(s,teams)
        t['iteration'] = i
        dfs.append(t)
    return pd.concat(dfs, ignore_index=True)
def plot_simulation(simulation,team, attribution='wins',start_date='2015',end_date='2016'):
    ax = simulation[attribution][simulation['team']==team].hist(figsize=(7,5))
    ax.set(title='%s: %s - %s %s, 1000 simulations'%(team, start_date[:4],end_date[:4],attribution))
    ax.axvline(simulation[attribution][simulation['team']==team].mean())
    stats=simulation[attribution][simulation['team']==team].mean()
    _=plt.annotate('Mean: %d' % stats, xy=(stats+1,ax.get_ylim()[1]-10))
    return ax
def get_roster_links(season):
    '''season is the year in which the playoffs open'''
    soup=make_soup(url%str(season))
    T=soup.find('div',{'class':'standings_divs table_wrapper'})
    hrefs=T.findAll('a',href=True)[:30]
    links=[];teamName=[]
    for href in hrefs:
        l=url.split('/l')[0]+href.attrs['href']
        links.append(l)
        teamName.append(href.attrs['href'].split('/')[-2].lower())
    return links,teamName
def get_roster(roster_link,side=False,attrN='NAME'):
    soup=make_soup(roster_link)
    table_area = soup.find('table',{'id':'roster'})
    columns=['NAME','Position','H','W','Birth','Exp','College']
    tempTable=[[td.findChildren(text=True) for td in tr.findAll("td")] for tr in table_area.find_all('tr')]
    tempTable=np.array(tempTable[1:]);size=tempTable.shape;tempTable=tempTable.reshape(size[0],size[1])
    tempTable=pd.DataFrame(tempTable,columns=columns)
    Names=np.concatenate(tempTable.NAME.values)
    if side:
        attr=np.concatenate(tempTable[attrN].values)
        return attr
    else:
        return Names