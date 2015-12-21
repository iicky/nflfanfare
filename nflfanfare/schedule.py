from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import nflgame
import os
import pandas as pd
import pytz
import re
from selenium import webdriver
from StringIO import StringIO
import sqlalchemy as sql
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
        browser.quit()

        # Find preformatted CSV
        games = ""
        ids = soup.find('pre', attrs={'id': 'csv_games_left'})
        for i in ids:
            games = i

        # Reformat CSV
        games = games.split('\n')
        csv = ''
        for line in games:
            if not line == '' and not re.match('Week', line):
                csv += '%s,%s\n' % (year, line)

        return csv

    def completed_games_csv(self, year):
        ''' Returns csv of completed games for year on Pro-Football Reference
        '''
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
        browser.quit()

        # Find preformatted CSV
        games = ""
        ids = soup.find('pre', attrs={'id': 'csv_games'})
        for i in ids:
            games = i

        # Reformat CSV
        games = games.split('\n')
        csv = ''
        for line in games:
            if not line == '' and not re.match('Week', line):
                csv += '%s,%s\n' % (year, line)

        return csv

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

    def nflgame_info(self, hometeam, awayteam, year, month, day):
        ''' Returns gamekey, eid, and season type from nflgame
        '''
        # Filling in missing information from nflgame
        sched = nflgame.sched.games
        for g in sched:

            # Jacksonville fix
            if sched[g]['away'] == 'JAC':
                sched[g]['away'] = 'JAX'
            if sched[g]['home'] == 'JAC':
                sched[g]['home'] = 'JAX'

            if (sched[g]['home'] == hometeam
                and sched[g]['away'] == awayteam
                and sched[g]['year'] == int(year)
                and sched[g]['month'] == int(month)
                and sched[g]['day'] == int(day)
                ):
                return (sched[g]['gamekey'],
                        sched[g]['eid'],
                        sched[g]['season_type'])

    def completed_games_df(self, year):
        ''' Returns completed games csv as data frame
        '''

        csv = self.completed_games_csv(year)

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
                                                      row['month'],
                                                      row['day']), axis=1)
        df['gameid'] = info.str.get(0)
        df['eid'] = info.str.get(1)
        df['seasontype'] = info.str.get(2)

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
                                                      row['month'],
                                                      row['day']), axis=1)
        df['gameid'] = info.str.get(0)
        df['eid'] = info.str.get(1)
        df['seasontype'] = info.str.get(2)

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
        result = ff.db.schedule.query.filter_by(gameid=gameid)
        return ff.db.session.query(result.exists()).scalar()

    def is_complete(self, gameid):
        ''' Returns true if gameid is in database
        '''
        result = ff.db.schedule.query.filter_by(gameid=gameid).one()
        if not result.endtime == None:
            return True
        return False

    def add_game(self, row):
        ''' Adds game to database
        '''
        query = ff.db.schedule(gameid=row['gameid'],
                               eid=row['eid'],
                               week=row['week'],
                               seasontype=row['seasontype'],
                               hometeam=row['hometeam'],
                               awayteam=row['awayteam'],
                               starttime=row[
                                   'starttime'] if 'starttime' in row.index else None
                               )
        try:
            ff.db.session.add(query)
            ff.db.session.commit()
        except:
            print "Could not add %s to database" % row['gameid']
            print "Error:", sys.exc_info()
            ff.db.session.rollback()

    def add_pfr_info(self, gameid, info):
        ''' Adds Pro-Football Reference info to database
        '''
        table = ff.db.session.query(ff.db.schedule).get(gameid)

        table.starttime = info['starttime'] if info.has_key(
            'starttime') else None
        table.endtime = info['endtime'] if info.has_key('endtime') else None
        table.stadium = info['stadium'] if info.has_key('stadium') else None
        table.weather = info['weather'] if info.has_key('weather') else None
        table.wontoss = info['wontoss'] if info.has_key('wontoss') else None
        table.attendance = info['attendance'] if info.has_key(
            'attendance') else None
        table.vegasline = info['vegasline'] if info.has_key(
            'vegasline') else None
        table.overunder = info['overunder'] if info.has_key(
            'overunder') else None

        try:
            ff.db.session.commit()
        except:
            print "Could not update %s PFR info." % gameid
            print "Error:", sys.exc_info()
            ff.db.session.rollback()

    def update_db(self):
        ''' Updates schedule table of database
        '''

        cdf = self.completed_games_df('2015')
        pdf = self.pending_games_df('2015')

        for i, row in cdf.iterrows():

            if not self.in_db(row['gameid']):
                self.add_game(row)

            # Update game with PFR info
            if not self.is_complete(row['gameid']):
                info = self.pfr_game_info(row['boxscore'])
                if info.has_key('endtime'):
                    self.add_pfr_info(row['gameid'], info)

        for i, row in pdf.iterrows():

            if not self.in_db(row['gameid']):
                self.add_game(row)

    def game_info(self, gameid):
        ''' Returns info for game id
        '''
        result = ff.db.schedule.query.filter_by(gameid=gameid).one()
        return result.__dict__

    def completed_games(self):
        ''' Returns dataframe of completed games
        '''
        df = pd.read_sql_table('schedule', ff.db.engine)
        df = df[pd.notnull(df.endtime)]
        return df if not df.empty else None

    def pending_games(self):
        ''' Returns dataframe of pending games
        '''
        df = pd.read_sql_table('schedule', ff.db.engine)
        df = df[pd.isnull(df.endtime)]
        return df if not df.empty else None

    def pre_post_times(self, starttime):
        ''' Returns timedelta of pregame and postgame times
        '''
        pregame = starttime - timedelta(hours=1)
        postgame = starttime + timedelta(hours=4)
        return (pregame, postgame)

    def tweet_count(self, gameid):
        ''' Returns the tweet count for a game
        '''
        info = self.game_info(gameid)
        result = ff.db.session.query(ff.db.tweets, ff.db.schedule).\
            join(ff.db.schedule, sql.or_(
                ff.db.tweets.teamid == ff.db.schedule.hometeam,
                ff.db.tweets.teamid == ff.db.schedule.awayteam)).\
                filter(ff.db.schedule.gameid == gameid).\
                filter(ff.db.tweets.postedtime >= str(info['starttime'])).\
                filter(ff.db.tweets.postedtime <= str(info['endtime'])).count()
        return 

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

