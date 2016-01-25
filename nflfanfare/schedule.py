from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import nflgame
import os
import pandas as pd
from pymongo import MongoClient
import pytz
import re
from selenium import webdriver
from StringIO import StringIO
import sys
import urllib2

import nflfanfare as ff


class Schedule:
    ''' Schedule class
    '''

    def __init__(self):
        pass

    def pending_games_csv(self, year):
        ''' Returns csv of pending games for year on Pro-Football Reference
        '''
        try:
            # Open url in browser
            url = 'http://www.pro-football-reference.com/years/%s/games.htm' % year
            browser = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',
                                          service_log_path=os.path.devnull)
            browser.get(url)

            # Click button to get CSV
            csvlink = browser.find_elements_by_xpath(
                "//span[contains(text(), 'CSV')]")
            csvlink[1].click()

            # Get the source code for page
            html = browser.page_source.encode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
        except:
            return None
        finally:
            browser.close()
            browser.quit()

        try:
            # Find preformatted CSV
            games = ""
            ids = soup.find('pre', attrs={'id': 'csv_games_left'})
            for i in ids:
                games = i

            # Reformat CSV
            games = games.split('\n')
            csv = ''
            for line in games:
                if (not line == ''
                        and not line[0] == ','
                        and not 'Week' in line):
                    csv += '%s,%s\n' % (year, line)

            return csv
        except:
            print "Could not scrape pending games from PFR."
            return None

    def completed_games_csv(self, year):
        ''' Returns csv of completed games for year on Pro-Football Reference
        '''
        try:
            # Open url in browser
            url = 'http://www.pro-football-reference.com/years/%s/games.htm' % year
            browser = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',
                                          service_log_path=os.path.devnull)
            browser.get(url)

            # Click button to get CSV
            csvlink = browser.find_elements_by_xpath(
                "//span[contains(text(), 'CSV')]")
            csvlink[0].click()

            # Get the source code for page
            html = browser.page_source.encode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
        except:
            return None
        finally:
            browser.close()
            browser.quit()

        try:
            # Find preformatted CSV
            games = ""
            ids = soup.find('pre', attrs={'id': 'csv_games'})
            for i in ids:
                games = i

            # Reformat CSV
            games = games.split('\n')
            csv = ''
            for line in games:
                if (not line == ''
                        and not line[0] == ','
                        and not 'Week' in line):
                    csv += '%s,%s\n' % (year, line)
            return csv
        except:
            print "Could not scrape completed games from PFR."
            return None

    def pfr_boxscore_link(self, year, month, day, pfrid):
        ''' Returns a Pro-Football Reference boxscore link
        '''
        month = '0' + str(month) if len(str(month)) == 1 else month
        day = '0' + str(day) if len(str(day)) == 1 else day
        baseurl = 'http://www.pro-football-reference.com/boxscores/'
        return '%s%s%s%s0%s.htm' % (baseurl, year, month, day, pfrid)

    def pfr_game_info(self, boxscore):
        ''' Gets game information from Pro-Football reference boxscore URL
        '''
        info = {}

        try:
            page = urllib2.urlopen(boxscore)
            soup = BeautifulSoup(page.read(), "html.parser")

            # Game date
            date = ''
            ids = soup.find('div', {"class": "float_left margin_right"})
            for i in ids:
                date = i

            # Game info
            ids = soup.find_all('table', {"id": "game_info"})
            for i in ids:
                for t in i.find_all('tr'):
                    t = t.text.split('\n')

                    if "Stadium" in t:
                        info['stadium'] = t[2].rstrip()
                    if "Start Time (ET)" in t:
                        info['starttime'] = ' '.join([date, t[2]])
                    if "Won Toss" in t:
                        info['wontoss'] = t[2]
                    if "Duration" in t:
                        info['endtime'] = [int(x) for x in t[2].split(':')]
                    if "Attendance" in t:
                        info['attendance'] = re.sub(',', '', t[2])
                    if "Weather" in t or "Roof" in t:
                        info['weather'] = re.sub('%', '', t[2])
                    if "Vegas Line" in t:
                        info['vegasline'] = t[2]
                    if "Over/Under" in t:
                        info['overunder'] = t[2]

            # Creating dates
            info['starttime'] = datetime.strptime(
                info['starttime'], '%A, %B %d, %Y %I:%M%p')
            info['starttime'] = pytz.timezone(
                'US/Eastern').localize(info['starttime'])

            # Converting dates to UTC and game calculating end time
            info['starttime'] = info[
                'starttime'].astimezone(pytz.timezone('UTC'))
            offset = timedelta(hours=info['endtime'][
                               0], minutes=info['endtime'][1])
            info['endtime'] = info['starttime'] + offset
            info['starttime'] = info['starttime'].replace(tzinfo=None)
            info['endtime'] = info['endtime'].replace(tzinfo=None)

            return info

        except:
            return info

    def nflgame_info(self, hometeam, awayteam, year, week):
        ''' Returns gamekey, eid, and season type from nflgame
        '''
        # Jacksonville fix
        if awayteam == 'JAX':
            awayteam = 'JAC'
        if hometeam == 'JAX':
            hometeam = 'JAC'

        try:
            if week.isdigit():
                game = nflgame.games(year=int(year),
                                     week=int(week),
                                     home=hometeam,
                                     away=awayteam)[0]
            else:
                game = nflgame.games(year=int(year),
                                     kind='POST',
                                     home=hometeam,
                                     away=awayteam)[0]
            return (game.gamekey,
                    game.eid,
                    game.schedule['season_type'])
        except:
            return (None, None, None)

    def completed_games_df(self, year):
        ''' Returns completed games csv as data frame
        '''

        csv = self.completed_games_csv(year)
        if csv == None:
            return pd.DataFrame()

        # Read into pandas dataframe
        columns = ['year', 'week', 'date', 'winner',
                   'atgame', 'loser', 'Wpts', 'Lpts']
        df = pd.read_csv(StringIO(csv), usecols=[
                         0, 1, 3, 5, 6, 7, 8, 9], names=columns)

        # Change winner and loser columns to team IDs
        df['winner'] = df.winner.apply(ff.team.teamid_from_name)
        df['loser'] = df.loser.apply(ff.team.teamid_from_name)

        # Create home and away team columns
        df.loc[df['atgame'] == '@', 'hometeam'] = df.loser
        df.loc[df['atgame'] == '@', 'awayteam'] = df.winner
        df.loc[pd.isnull(df['atgame']), 'hometeam'] = df.winner
        df.loc[pd.isnull(df['atgame']), 'awayteam'] = df.loser

        # Creates month and day columns
        df['month'] = df.date.str.split(' ').str.get(0)
        df['month'] = df.month.apply(
            lambda d: datetime.strptime(d, '%B').month)
        df['day'] = df.date.str.split(' ').str.get(1)

        # Gets nflgame information
        info = df.apply(lambda row: self.nflgame_info(row['hometeam'],
                                                      row['awayteam'],
                                                      row['year'],
                                                      row['week']), axis=1)

        df['gameid'] = info.str.get(0)
        df['eid'] = info.str.get(1)
        df['seasontype'] = info.str.get(2)

        # Year offset fix
        df['year'] = df.apply(lambda row: row['year'] +
                              1 if row['month'] < 7 else row['year'], axis=1)

        # Gets PFRID and boxscore links for hometeams
        df['pfrid'] = df.hometeam.apply(ff.team.pfrid_from_teamid)
        df['boxscore'] = df.apply(lambda row: self.pfr_boxscore_link(row['year'],
                                                                     row['month'],
                                                                     row['day'],
                                                                     row['pfrid']), axis=1)
        df['completed'] = True

        return df

    def pending_games_df(self, year):
        ''' Returns pending games csv as data frame
        '''
        csv = self.pending_games_csv(year)
        if csv == None:
            return pd.DataFrame()

        # Read into pandas dataframe
        columns = ['year', 'week', 'date', 'awayteam', 'hometeam', 'time']
        df = pd.read_csv(StringIO(csv), usecols=[
            0, 1, 3, 4, 6, 7], names=columns)

        # Change hometeam and awayteam columns to team IDs
        df['hometeam'] = df.hometeam.apply(ff.team.teamid_from_name)
        df['awayteam'] = df.awayteam.apply(ff.team.teamid_from_name)

        # Creates month and day columns
        df['month'] = df.date.str.split(' ').str.get(0)
        df['month'] = df.month.apply(
            lambda d: datetime.strptime(d, '%B').month)
        df['day'] = df.date.str.split(' ').str.get(1)

        # Gets nflgame information
        info = df.apply(lambda row: self.nflgame_info(row['hometeam'],
                                                      row['awayteam'],
                                                      row['year'],
                                                      row['week']), axis=1)
        df['gameid'] = info.str.get(0)
        df['eid'] = info.str.get(1)
        df['seasontype'] = info.str.get(2)

        # Year offset fix
        df['year'] = df.apply(lambda row: row['year'] +
                              1 if row['month'] < 7 else row['year'], axis=1)

        # Gets PFRID and boxscore links for hometeams
        df['pfrid'] = df.hometeam.apply(ff.team.pfrid_from_teamid)
        df['boxscore'] = df.apply(lambda row: self.pfr_boxscore_link(row['year'],
                                                                     row['month'],
                                                                     row['day'],
                                                                     row['pfrid']), axis=1)

        # Convert starttime to date
        df['starttime'] = df.apply(lambda row: self.start_time(row['year'],
                                                               row['date'],
                                                               row['time']), axis=1)

        df['completed'] = False

        return df

    def start_time(self, year, date, time):
        ''' Returns game starttime as a string
        '''
        starttime = '%s, %s %s' % (date, year, time)

        # Creating dates
        starttime = datetime.strptime(starttime, '%B %d, %Y %I:%M %p')
        starttime = pytz.timezone('US/Eastern').localize(starttime)
        starttime = starttime.astimezone(pytz.timezone('UTC'))
        starttime = starttime.replace(tzinfo=None)

        return str(starttime)

    def in_db(self, gameid):
        ''' Returns true if gameid is in database
        '''
        if ff.db.games.find({'gameid': gameid}).count() > 0:
            return True
        else:
            return False

    def is_complete(self, gameid):
        ''' Returns true if gameid is complete
        '''
        result = ff.db.games.find_one({'gameid': gameid})
        if not result == None:
            if result.has_key('endtime'):
                if not result['endtime'] == None:
                    return True
        return False

    def add_game(self, row):
        ''' Adds game to database
        '''
        game = {
            'gameid': row['gameid'],
            'eid': row['eid'],
            'week': row['week'],
            'seasontype': row['seasontype'],
            'hometeam': row['hometeam'],
            'awayteam': row['awayteam'],
            'starttime': row['starttime'] if 'starttime' in row.index else None,
            'tweetcounts': {'hometeam': 0, 'awayteam': 0, 'total': 0}
        }
        try:
            result = ff.db.games.insert_one(game)
        except:
            print "Could not add %s to database" % row['gameid']

    def add_pfr_info(self, gameid, info):
        ''' Adds Pro-Football Reference info to database
        '''
        try:
            result = ff.db.games.update_one(
                {"gameid": gameid},
                {
                    "$set": {
                        'starttime': info['starttime'] if info.has_key('starttime') else None,
                        'endtime': info['endtime'] if info.has_key('endtime') else None,
                        'stadium': info['stadium'] if info.has_key('stadium') else None,
                        'weather': info['weather'] if info.has_key('weather') else None,
                        'wontoss': info['wontoss'] if info.has_key('wontoss') else None,
                        'attendance': info['attendance'] if info.has_key('attendance') else None,
                        'vegasline': info['vegasline'] if info.has_key('vegasline') else None,
                        'overunder': info['overunder'] if info.has_key('overunder') else None
                    }
                }
            )
        except:
            print "Could not update %s PFR info." % gameid
            print "Error:", sys.exc_info()

    def update_db_schedule(self):
        ''' Updates schedule table of database
        '''

        cdf = self.completed_games_df('2015')
        pdf = self.pending_games_df('2015')
        if not cdf.empty:
            for i, row in cdf.iterrows():
                if not self.in_db(row['gameid']) and row['gameid'] != None:
                    self.add_game(row)

                # Update game with PFR info
                if not self.is_complete(row['gameid']):
                    info = self.pfr_game_info(row['boxscore'])
                    self.add_pfr_info(row['gameid'], info)

        if not pdf.empty:
            for i, row in pdf.iterrows():
                if not self.in_db(row['gameid']):
                    self.add_game(row)

    def game_info(self, gameid):
        ''' Returns info for game id
        '''
        result = ff.db.games.find_one({'gameid': gameid})
        return result

    def all_games(self):
        ''' Returns dataframe of all games
        '''
        return pd.DataFrame(list(ff.db.games.find({}, {'_id': 0})))

    def completed_games(self):
        ''' Returns dataframe of completed games
        '''
        df = pd.DataFrame(list(ff.db.games.find(
            {'endtime': {'$ne': 'null'}}, {'_id': 0})))
        return df if not df.empty else None

    def pending_games(self):
        ''' Returns dataframe of completed games
        '''
        df = pd.DataFrame(
            list(ff.db.games.find({'endtime': None}, {'_id': 0})))
        return df if not df.empty else None

    def pre_post_times(self, starttime):
        ''' Returns timedelta of pregame and postgame times
        '''
        pregame = starttime - timedelta(hours=1)
        postgame = starttime + timedelta(hours=4)
        return (pregame, postgame)

    def gameid_from_team_and_time(self, teamid, postedtime):
        ''' Returns gameid from a teamid and posted time
        '''
        onehour = 60 * 60 * 1000
        fourhours = 4 * onehour
        result = ff.db.games.aggregate([
                { '$project': {
                    'gameid': '$gameid',
                    'hometeam': '$hometeam',
                    'awayteam': '$awayteam',
                    'starttime': '$starttime',
                    'start': { '$subtract': ['$starttime', onehour] },
                    'end': { '$add': ['$starttime', fourhours] }
                    }
                },
                {'$match': { 
                    '$and': [ 
                        { '$or': [ { 'hometeam': teamid }, 
                                   { 'awayteam': teamid } 
                                 ] },
                        { 'start': { '$lt': postedtime } },
                        { 'end': { '$gte': postedtime } }
                    ]
                    }
                }

            ])
        if not result == None:
            for r in result:
                if 'gameid' in r:
                    return r['gameid']
        return None

    def game_teams(self, gameid):
        ''' Returns a dictionary of teams for a game
        '''
        result = ff.db.games.find_one({'gameid': gameid})
        return {'hometeam': result['hometeam'],
                'awayteam': result['awayteam']}

    def game_status(self, gameid):
        ''' Returns game status
        '''
        start = self.game_info(gameid)['starttime']
        pre, post = self.pre_post_times(start)
        now = datetime.utcnow()
        oneweek = now - timedelta(days=7)
        upcoming = now + timedelta(hours=1)

        if pre < oneweek:   # Historic game (> 1 week)
            return "historic"
        elif pre > oneweek and post < now:  # Recent game (< 1 week)
            return "recent"
        elif pre < now and post > now:  # Live game (on now)
            return "live"
        elif pre > now and pre < upcoming:  # Upcoming game (within 1 hour)
            return "upcoming"
        elif pre > datetime.now():  # Pending game (> 1 hour away)
            return "pending"

    def game_tweet_counts(self, gameid):
        ''' Returns a dictionary of tweet counts for a game
        '''
        counts = {}
        teams = self.game_teams(gameid)
        for t in teams:
            result = ff.db.tweets.find({'gameid': gameid,
                                        'teamid': teams[t],
                                        'sentiment.sent_compound': {'$ne': 0}
                                        }).count()
            counts[t] = result

        counts['total'] = counts['hometeam'] + counts['awayteam']
        return counts

    def update_game_tweet_counts(self, gameid):
        ''' Updates tweet counts in database for a gameid
        '''
        counts = self.game_tweet_counts(gameid)

        try:
            result = ff.db.games.update_one(
                    {"gameid": gameid},
                    {
                        "$set": {
                            'tweetcounts.hometeam': counts['hometeam'],
                            'tweetcounts.awayteam': counts['awayteam'],
                            'tweetcounts.total': counts['total'],
                        }
                    }
            )            
        except:
            print "Could not update %s tweet counts." % gameid

    def update_db_tweet_counts(self):
        ''' Updates tweet counts for games in the database
        '''
        games = list(ff.db.games.find({},{'gameid':1, '_id':0}))
        for g in games:
            self.update_game_tweet_counts(g['gameid'])            

