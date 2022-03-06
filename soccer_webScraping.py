import bs4
import re
import requests
import itertools

import pandas as pd
import matplotlib.pyplot as plt

"""
Functioning web scrapper to remove data from fbref for the select teams and years.
A few pressing flaws before it can be generalized:

1) The web scrapper extract ALL matches, which also includes relegation/promotion playoffs, which skews data.
I have to manually clean this afterwards.

2) To identify the URL for the season/league, I find the first match (or Bundesliga the second). If want to 
generalize to other leagues this can't happen. 

possible solution: 
- https://fbref.com/en/ has select page numbers for some leagues, so I could cross check that the
  links found have them.
- other possible solution is to compare with the country found next to it. 
`
3) Season 2021-2022 is stored in a different format of url, so to access can't use find_url. 

"""

def single_season_results(url,country, season_year, as_df = False):
    """extract and parse the match scores for a given seasons per league. 

    Args:
        url (string): a string from soccerstats linking to a season to extract matches
        country (string): string corresponding to the country 
        season_year (int): integer corresponding to the season year

    Returns:x
        list: each element is a different match containing season year, country, home team, home goals, away team, away goals
    """
    soup = requests.get(url).text
    soup = bs4.BeautifulSoup(soup,'html.parser')

    season_details = []
    for game in soup.find_all('td',attrs={'data-stat':'score'}):
        
        if not game.get_text(): #if this isn't a game (i.e., no score)
            continue
        
        #some seasons xG is embedded in the table BEFORE team name, shifting everything.
        #So we check if we can make it a float, if we can then we have to look at columns +1 
        #from planned  and -1 from planne
        try: 
            float(game.previousSibling.get_text()) 
            home_team = game.previousSibling.previousSibling.get_text()
            away_team = game.nextSibling.nextSibling.get_text()
            attendance = game.nextSibling.nextSibling.nextSibling.get_text()
        except:
            home_team = game.previousSibling.get_text()
            away_team = game.nextSibling.get_text()
            attendance = game.nextSibling.nextSibling.get_text()
            
        #the '-' is a utf-8 byte, and string - is encoded as b'-'. Not sure how to get them to match, so I just
        #set the "splitter" as the utf-8 byte and then decode it into a string.
        score = game.get_text().split((b'\xe2\x80\x93').decode('utf-8'))
        
        season_details.append([season_year, country, home_team, int(score[0]), away_team, int(score[1]), attendance])
    
    if as_df:
        season_details = pd.DataFrame(season_details,columns = ['SeasonYear','Country','HomeTeam','HomeGoals','AwayTeam','AwayGoals','Attendance'])
    return season_details

def datasets_to_collect():    
    """Variables determining which datasets to collect

    Returns:
        countries: list of strings representing the countries to process
        years: list of integers representing the years to collect the data from
    """
    leagues = {'England':'Premier League', 'Spain':'Liga BBVA|LaLiga|La Liga','Germany': 'Bundesliga','France' : 'Ligue 1', 'Italy':'Serie A'}
    years = [2014,2015,2016,2017,2018,2019,2020]#,2021]    
    
    return leagues,years

def identify_url(league,year):
    """Identify the url at fbref.com corresponding to this league + year

    Args:
        league (string): league name to identify the matches
        year (int):  season year to identify the matches

    Returns:
        url: url for the matches to find
    """
    #The Austrian Bundesliga is the first find, so look at the SECOND of find_all, not the first
    indx = (1 if league == 'Bundesliga' else 0) 
    
    #Find the page ID corresponding 
    main_url = f'https://fbref.com/en/comps/season/{year}-{year+1}'
    soup = bs4.BeautifulSoup(requests.get(main_url).text,'html.parser')
    season_id = soup.find_all('a',string = re.compile(f'^.*?{league}.*?$'))[indx].attrs['href']
    
    #Embed schedule to see the actual match results
    embed_id = season_id.rfind('/')
    new_url = 'https://fbref.com' + season_id[:embed_id] + '/schedule' + season_id[embed_id:]
    
    return new_url

def collect_all_matches(save= True):
    """Iterate through all the countries and matches defined

    Args:
        save (bool, optional): save dataframe to csv. Defaults to True.

    Returns:
        dataFrame: dataframe of all matches across years and countries
    """
    leagues,years = datasets_to_collect()
    
    all_matches = []
    for (country,league), year in itertools.product(leagues.items(),years):
        url = identify_url(league,year)
        season_details = single_season_results(url,country,year)
        all_matches += season_details
    
    all_matches = pd.DataFrame(all_matches,columns = ['SeasonYear','Country','HomeTeam','HomeGoals','AwayTeam','AwayGoals','Attendance'])
    
    if save:
        all_matches.to_csv('soccer_results.csv',index=False,sep=',')  
          
    return all_matches
    
if __name__ == '__main__': 
    df = collect_all_matches()
    
