from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse
import inspect
import json
import logging
import logging.config
import numpy as np
import os
import pandas as pd
import pymongo
import pytz
import requests
import subprocess
import sys
import time

import nflfanfare as ff


class Schedule:
    ''' Class for obtaining NFL Scoreboard game information
    '''
    def __init__(self):

        # Logger
        self.log = logging.getLogger('gamecenter.Schedule')

        # Week list per season type
        self.weeks = {
            'PRE': range(1, 4+1),
            'REG': range(1, 17+1),
            'POST': range(18, 22+1)
        }

    def _get_week(self, season, season_type, week):
        ''' Returns a data frame of schedule data for a given
            season, season type, and week
        '''
        # Create URL
        url = ('http://www.nfl.com/ajax/scorestrip?'
               'season=%s&seasonType=%s&week=%s' %
               (season, season_type, week))

        # Wait a random lognormal amount of seconds
        time.sleep(np.random.lognormal(1, .5, 1)[0])

        # Return XML if response was successful
        r = requests.get(url)
        if r.status_code == 200:
            if len(r.text) > 50:
                return self._parse_games(r.text)

            # Response does not contain data
            print ('No data contained in XML for %s %s week %s.' %
                   (season_type, season, week))
            return pd.DataFrame()

        # Response was unsuccessful
        print ('Could not find XML data for %s %s week %s.' %
               (season_type, season, week))
        return pd.DataFrame()

    def _parse_games(self, xml):
        ''' Returns a data frame from XML data
        '''

        # Data dictionary
        data_dict = {
            'd': 'day',
            't': 'time',
            'eid': 'eid',
            'gsis': 'gameid',
            'gt': 'seasontype',
            'h': 'hometeam',
            'v': 'awayteam',
            'hs': 'homescore',
            'vs': 'awayscore',
            'q': 'status',
            'scheduled': 'scheduled',
            'week': 'week',
            'season': 'season',
            '_id': '_id'
        }

        # Parse XML
        soup = BeautifulSoup(xml, 'html.parser')

        # Week information
        week = soup.find_all('gms')[0].attrs

        # Convert games to dataframe
        games = soup.find_all('g')
        df = pd.DataFrame([_.attrs for _ in games])

        # Create _id column for MongoDB
        df['_id'] = df.gsis

        # Create date from EID and time accounting for London games
        gdate = df.eid.apply(lambda x: x[:-2])
        gtime = df.t.apply(lambda x:
                           x + ' AM' if x == '9:30' else x + ' PM')

        # Convert scheduled time to datetime and localize to UTC
        df['scheduled'] = gdate + ' ' + gtime
        df['scheduled'] = pd.to_datetime(df.scheduled)
        df['scheduled'] = df.scheduled.apply(
                              lambda x:
                              pytz.timezone('US/Eastern').localize(x))
        df['scheduled'] = df.scheduled.apply(
                                lambda x:
                                x.astimezone(pytz.timezone('UTC')))

        # Add week information
        df['week'] = week['w']
        df['season'] = week['y']

        # Rename and drop columns
        df.rename(columns=data_dict, inplace=True)
        df = df[data_dict.values()]

        return df

    def _get_schedule(self, season):
        ''' Returns a dataframe of all games for a season
        '''
        df = pd.DataFrame()

        # Get last game in database
        last = self._last_game(season)

        # Iterate through season types and week
        for season_type in self.weeks.keys():
            for week in self.weeks[season_type]:

                # Check to see week is already parsed
                week_check = (last['seasontype'] == season_type and
                              last['week'] < week)

                # Check to see if last game is old and postseason
                date_check = (season_type == 'POST' and
                              last['scheduled'] < datetime.utcnow())

                # Get week schedule and add if not empty
                if (week_check or date_check):
                    games = self._get_week(season, season_type, week)
                    if not games.empty:
                        df = df.append(games)

        return df

    def _get_update(self):
        ''' Returns a dataframe of the updated season schdule
        '''
        # Create URL
        url = 'http://www.nfl.com/liveupdate/scorestrip/ss.xml'

        # Wait a random lognormal amount of seconds
        time.sleep(np.random.lognormal(2, .5, 1)[0])

        try:
            # Return XML if response was successful
            r = requests.get(url)
            if r.status_code == 200:
                if len(r.text) > 50:
                    return self._parse_games(r.text)
        except:
            return pd.DataFrame()

    def _add_schedule(self, season):
        ''' Adds scheduled games to database
        '''
        # Converts schedule data frame to dictionary
        data = self._get_schedule(season).to_dict(orient='records')

        # Insert each game into database
        for d in data:

            # Check to see if game is already in database
            result = ff.db.games.find_one({'_id': d['_id']})
            if not result:
                try:
                    # Insert game into database
                    ff.db.games.insert_one(d)

                    # Log schedule update
                    self.log.info('Inserting game %s to the database.' %
                                  d['_id'])
                except:
                    pass

    def _update(self):
        ''' Adds game updates to database and returns updated
            schedule dataframe
        '''
        # Converts schedule data frame to dictionary
        df = self._get_update()
        if not df.empty:
            data = df.to_dict(orient='records')

            # Log schedule update
            self.log.info('Updating schedule.')

            # Update each game in the database
            for d in data:
                try:
                    ff.db.games.update_one({'_id': d['_id']},
                                           {'$set': d})
                except:
                    pass

        return df

    def _last_game(self, season):
        ''' Finds the date of the lastest game in the database
        '''
        result = ff.db.games.find().sort('scheduled',
                                         pymongo.DESCENDING).limit(1)
        return list(result)[0]


class Game:
    ''' Class for obtaining NFL Scoreboard game information
    '''
    def __init__(self, gameid):

        # Logger
        self.log = logging.getLogger('gamecenter.Game')

        # Game ID
        self.gameid = gameid

        # Game info
        self.info = self._game_info(self.gameid)

        # JSON url for game
        self.url = ('http://www.nfl.com/liveupdate/game-center/'
                    '%s/%s_gtd.json' % (self.info['eid'], self.info['eid']))

        # Game status
        self.status = self._status()

    def _game_info(self, gameid):
        ''' Returns a dictionary of the game info
        '''
        result = ff.db.games.find_one({'gameid': gameid})
        if result:
            return result

        self.log.error('The game id %s was not found in the database.' %
                       gameid)
        return None

    def _get_feed(self):
        ''' Retreives JSON data for a game
        '''
        # Return XML if response was successful
        try:
            r = requests.get(self.url)
            if r.status_code == 200:
                if len(r.text) > 50:
                    return json.loads(r.text)[self.info['eid']]
        except:
            return None

    def _parse_feed(self):
        ''' Parses the JSON feed plays and returns a data frame
        '''
        feed = self._get_feed()

        # Empty dataframe for plays
        df = pd.DataFrame()

        # Check if feed contains data
        if feed:

            # Convert drive keys to interger and sort
            drives = feed['drives']
            driveid = sorted([int(_) for _ in drives if not _ == 'crntdrv'])

            # Iterate through drives
            for d in driveid:

                # Iterate through plays
                plays = drives[str(d)]['plays']
                for p in plays:

                    # Add additional play information
                    plays[p]['gameid'] = self.info['gameid']
                    plays[p]['_id'] = self.info['gameid'] + '-' + p
                    plays[p]['playid'] = int(p)
                    plays[p]['collected_time'] = datetime.utcnow()
                    plays[p]['homescore'] = int(feed['home']['score']['T'])
                    plays[p]['awayscore'] = int(feed['away']['score']['T'])
                    plays[p]['drive'] = d

                    df = df.append(pd.Series(plays[p]), ignore_index=True)

        return df

    def _update(self):
        ''' Updates the play information for a game
        '''
        plays = self._parse_feed()

        # Check to see if any plays
        if not plays.empty:
            plays = plays.to_dict(orient='records')

            # Iterate through plays
            for play in plays:

                # Check to see if play is in the database
                result = ff.db.plays.find_one({'_id': play['_id']})
                if not result:
                    try:
                        ff.db.plays.insert_one(play)

                        self.log.info('Adding play %s to the database '
                                      'for game %s. [%s: %s | %s: %s].' %
                                      (play['playid'], play['gameid'],
                                       self.info['hometeam'],
                                       play['homescore'],
                                       self.info['awayteam'],
                                       play['awayscore']))
                    except:
                        pass

    def _pre_post_times(self, starttime):
        ''' Returns timedelta of pregame and postgame times
        '''
        pregame = starttime - timedelta(hours=1)
        postgame = starttime + timedelta(hours=4)
        return (pregame, postgame)

    def _status(self):
        ''' Returns game status
        '''
        if self.info:
            start = self.info['scheduled']
            pre, post = self._pre_post_times(start)
            now = datetime.utcnow()
            oneweek = now - timedelta(days=7)
            upcoming = now + timedelta(hours=1)
            starting = now + timedelta(minutes=15)

            # Historic game (> 1 week)
            if start < oneweek:
                return "historic"
            # Recent game (< 1 week)
            elif start > oneweek and post < now:
                return "recent"
            # Live game (on now)
            elif start < now and post > now:
                return "live"
            # Game starting (within 15 minutes)
            elif start > now and start < starting:
                return "starting"
            # Upcoming game (within 1 hour)
            elif start > now and start < upcoming:
                return "upcoming"
            # Pending game (> 1 hour away)
            elif start > datetime.now():
                return "pending"

        return None


class Collector:
    ''' Class for updating Game Center information in the database
    '''
    def __init__(self):

        # Logger
        self.log = logging.getLogger('gamecenter.Collector')

        # Get schedule update
        self.schedule = ff.gc.Schedule()._update()

    def _pending(self):
        ''' Returns a data frame of pending games
        '''
        if not self.schedule.empty:
            df = self.schedule[self.schedule.status != 'F'].copy()

            # Determine game status
            df['status'] = df.gameid.apply(lambda x: Game(x).status)

        return df

    def _spawn(self):
        ''' Spawns the monitoring process for all upcoming games
        '''
        # Get pending games
        df = self._pending()

        if not df.empty:
            # Iterate through games
            for i, r in df.iterrows():

                if r['status'] == 'live' or r['status'] == 'starting':
                    info = ff.gc.Game(r['gameid']).info

                    # Check if game is not already updating
                    if 'updating' not in info.keys():
                        subprocess.Popen(['python',
                                          (ff.sec.helper_path +
                                           'monitor_game.py'),
                                          '--gameid',
                                          r['gameid']],
                                         stdin=None,
                                         stdout=None,
                                         stderr=None,
                                         close_fds=True)
            sys.exit(1)

    def _monitor(self, gameid):
        ''' Monitors a game JSON feed to update plays
        '''
        try:
            game = ff.gc.Game(gameid)

            if game.info:

                # Ignore if game has not started
                if (not game.status == 'starting' and
                        not game.status == 'live'):
                    self.log.warn('Game %s is not starting and is %s.' %
                                  (gameid, game.status))
                    return None

                # Mark game as being scraped
                ff.db.games.update_one({'_id': game.info['_id']},
                                       {'$set': {'updating': True}})
                self.log.info('Starting monitoring game %s.' % gameid)

                # Current time and end time
                now = datetime.utcnow()
                end = game.info['scheduled'] + timedelta(hours=4)

                # Monitor until end of game
                while now < end:
                    # Wait a random lognormal amount of seconds
                    time.sleep(np.random.lognormal(2, .5, 1)[0])

                    # Update game plays and current time
                    now = datetime.utcnow()

                    # Try to update game plays
                    try:
                        game._update()
                    except:
                        pass

                    # Stop monitoring if game status is final
                    game = ff.gc.Game(gameid)
                    if game.info['status'] == 'F':
                        self.log.info('Game %s has ended.' % gameid)
                        break
            else:
                # Notify if game info not found for game id
                self.log.error('Could not retrieve game information for %s.' %
                               gameid)

        except:
            self.log.error('Unknown error: %s line %s: %s' %
                           (sys.exc_info()[0],
                            sys.exc_info()[2].tb_lineno,
                            sys.exc_info()[1]))

        finally:
            # Mark game as finished
            ff.db.games.update_one({'_id': gameid},
                                   {'$unset': {'updating': ''}})
            self.log.info('Stopping monitoring game %s.' % gameid)
