from datetime import datetime, timedelta
import json
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
import pytz
import random
import re
import subprocess
import sys
import time
from TwitterAPI import TwitterAPI, TwitterRestPager
import tzlocal

import nflfanfare as ff


class API:
    ''' Twitter API Handling
    '''
    def __init__(self):
        ''' Defines tweet properties from API
        '''
        self.api = TwitterAPI(
            ff.sec.twitter_ckey, ff.sec.twitter_csec, auth_type='oAuth2')

    def _quota(self, request):
        ''' Returns quota information for API request
        '''
        result = self.api.request('application/rate_limit_status')
        resources = json.loads(result.response._content)['resources']

        base = re.split('/', request)[1]
        quota = resources[base][request]

        return quota

    def search(self, search, until=None):
        ''' Searches for term and adds tweets to the database
            Waits if API quota has been met
        '''
        result = self.api.request('search/tweets',
                                  {'q': search,
                                   'lang': 'en',
                                   'count': 100,
                                   'until': until})
        remaining = int(result.response.headers['x-rate-limit-remaining'])
        reset = float(result.response.headers['x-rate-limit-reset'])

        # Counters
        added = 0

        # Finds the time until quota reset and sleeps
        if remaining == 0:
            delta = datetime.fromtimestamp(reset) - datetime.now()
            print ("Quota reached for search/tweets. Waiting %s seconds."
                   % delta.total_seconds())
            time.sleep(delta.total_seconds())
            result = self.api.request('search/tweets' % int(tweetid))

        tweets = [Tweet(_, search=search) for _ in list(result)]
        for tweet in tweets:
            # Exclude retweets and tweets without a gameid
            if not tweet.retweeted:
                if tweet.gameid:
                    if tweet._add_db():
                        added += 1

        # Return statistics
        return {'search': search,
                'added': added,
                'total': len(tweets)}

    def pager(self, search, start, end):
        ''' Pages through the search API for tweets between the
            start and end times and adds them to the database
        '''
        if type(start) == datetime:
            # Convert to UTC timezone
            endaware = pytz.timezone('UTC').localize(end)
            startaware = pytz.timezone('UTC').localize(start)

            # Convert to local timezone
            local = tzlocal.get_localzone()
            startaware = startaware.astimezone(local)
            endaware = endaware.astimezone(local)

            # Make timestamp
            startstamp = int(time.mktime(startaware.timetuple()))
            endstamp = int(time.mktime(endaware.timetuple()))
        else:
            start = time.strptime(start, "%Y-%m-%d %H:%M")
            end = time.strptime(end, "%Y-%m-%d %H:%M")
            startstamp = int(time.mktime(start))
            endstamp = int(time.mktime(end))

        # Initalize the pager request
        result = TwitterRestPager(self.api, 'search/tweets',
                                  {'q': search,
                                   'lang': 'en',
                                   'count': 100,
                                   'since': str(startstamp),
                                   'until': str(endstamp)})
        quota = self._quota('/search/tweets')

        # Added counter
        added, total = 0, 0

        for item in result.get_iterator():

            # Check to see if item is tweet
            if 'text' in item:

                # Create tweet object
                tweet = Tweet(item, search=search)

                # Exclude retweets and tweets outside of pre and post game
                if not tweet.retweeted:
                    if tweet.postedtime >= start and tweet.postedtime <= end:
                        if tweet._add_db():
                            added += 1

                total += 1

            # Check API quota
            elif 'message' in item and item['code'] == '88':
                delta = datetime.fromtimestamp(quota['reset']) - datetime.now()
                print ("Quota reached for search/tweets. Waiting %s seconds."
                       % delta.total_seconds())
                time.sleep(delta.total_seconds())

        # Return statistics
        return {'search': search,
                'added': added,
                'total': total}


class Collector:
    ''' Class for collecting tweets
    '''
    def __init__(self):

        # Twitter API
        self.api = API()

        # Logger
        self.log = logging.getLogger('twitter.Collector')

    def collect_recent(self):
        ''' Collects tweets from recent games using the API pager.
            The API pager can collect tweets up to 7 days old.
        '''
        games = ff.games.games('recent')
        for game in games.gameid:
            self.collect_game(game)

    def collect_live(self):
        ''' Collects tweets from live games using the API search.
            Spawns a helper Python script to monitor the live game.
        '''
        # Get live, starting, or upcoming games
        games = ff.games.games(['upcoming', 'starting', 'live'])

        # Find list of games that are already being monitored
        locked = ff.db.games.find({'twitter': {'$exists': True}}, {'_id': 1})
        locked = [_['_id'] for _ in list(locked)]

        if not games.empty:

            # Iterate through games
            for game in games.gameid:
                # Check if game is not already updating
                if game not in locked:
                    subprocess.Popen(['python',
                                      (ff.sec.helper_path +
                                       'monitor_tweets.py'),
                                      '--gameid',
                                      game],
                                     stdin=None,
                                     stdout=None,
                                     stderr=None,
                                     close_fds=True)
            sys.exit(1)

    def collect_game(self, gameid):
        ''' Collects tweets for a game
            Determines if a game is recent or live.
            Uses the API pager for recent games and the API search
            for upcoming, starting, or live games.
            Recent collection of tweets skips colletion for any team
            that has more than 8000 in the database.
        '''
        # Game information
        game = ff.games.Game(gameid)

        # Teams information
        hometeam = ff.teams.Team(game.hometeam)
        awayteam = ff.teams.Team(game.awayteam)

        # Log schedule update
        self.log.info('Starting tweet collection for game %s.' % gameid)

        # Collection process for recent game
        if game.state == 'recent':

            # Teams hashtag pool
            hashtags = []
            if game.hometweets < 8000:
                hashtags += hometeam.hashtags
            if game.awaytweets < 8000:
                hashtags += awayteam.hashtags

            for hashtag in hashtags:

                # Search for hashtag tweets
                result = self.api.pager(hashtag, game.pregame, game.postgame)

                # Log tweet page update
                self.log.info('Added %s of %s tweets to the database for %s.' %
                              (result['added'],
                               result['total'],
                               result['search']))

        # Collection process for live or upcoming games
        if game.state in ['upcoming', 'starting', 'live']:
            now = datetime.utcnow()
            end = game.scheduled + timedelta(hours=4)

            # Teams hashtag pool
            hashtags = hometeam.hashtags + awayteam.hashtags

            try:
                # Mark game as being scraped
                ff.db.games.update_one({'_id': game.gameid},
                                       {'$set': {'twitter': True}})

                # Monitor until end of game
                while now <= end:

                    # Update now time
                    now = datetime.utcnow()

                    try:
                        # Wait a random lognormal amount of seconds
                        time.sleep(np.random.lognormal(2, .5, 1)[0])

                        # Choose and API search a random hashtag
                        hashtag = random.choice(hashtags)
                        result = self.api.search(hashtag)

                        # Log collection update
                        self.log.info('Added %s of %s tweets to the '
                                      'database for %s.' % (result['added'],
                                                            result['total'],
                                                            result['search']))
                    except:
                        pass

            except:
                self.log.error('Unknown error: %s line %s: %s' %
                               (sys.exc_info()[0],
                                sys.exc_info()[2].tb_lineno,
                                sys.exc_info()[1]))

            finally:
                # Mark game as finished
                ff.db.games.update_one({'_id': gameid},
                                       {'$unset': {'twitter': ''}})
                self.log.info('Stopping tweet collection for game %s.'
                              % gameid)


class Tweet:
    ''' Returns tweet object from API result
    '''
    def __init__(self, tweet, **kwargs):
        ''' Defines tweet properties from API
        '''
        # Source information
        self._id = tweet['id']
        self.tweetid = tweet['id']
        self.source = 'api'

        # Team and search information
        self.search = None
        self.teamid = None

        # Keyword information
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

        # Team information
        if self.search:
            self.teamid = ff.teams.Team(self.search).teamid

        # Tweet information
        self.tweettext = re.sub(r'\\|\"|\'', '', tweet['text'])
        self.language = tweet['lang']
        self.hashtags = ([h['text'] for h in tweet['entities']['hashtags']]
                         if len(tweet['entities']['hashtags']) > 0
                         else None)
        self.usermentions = ([h['screen_name']
                             for h in tweet['entities']['user_mentions']]
                             if len(tweet['entities']['user_mentions']) > 0
                             else None)
        self.postedtime = datetime.strptime(
            tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        self.collectedtime = datetime.utcnow()
        self.retweeted = False if 'retweeted_status' not in tweet else True

        # User information
        self.user = self._user_info(tweet)

        # Sentiment information
        self.sentiment = self._sentiment(tweet)

        # Game information
        self.gameid = self._gameid()

    def _user_info(self, tweet):
        ''' Returns user information dictionary for a tweet
        '''
        return {
            'userid': tweet['user']['id'],
            'username': tweet['user']['screen_name'],
            'realname': re.sub(r'\\|\"|\'', '',
                               tweet['user']['name']),
            'userlocation': (tweet['user']['location']
                             if not tweet['user']['location'] == ''
                             else None),
            'usertimezone': tweet['user']['time_zone'],
            'userprofileimg': tweet['user']['profile_image_url']
        }

    def _sentiment(self, tweet):
        ''' Returns sentiment dictionary for a tweet
        '''
        sid = SentimentIntensityAnalyzer().polarity_scores(tweet['text'])

        return {
            'sent_pos': round(sid['pos'], 3),
            'sent_neg':  round(sid['neg'], 3),
            'sent_neu':  round(sid['neu'], 3),
            'sent_compound':  round(sid['compound'], 3)
        }

    def _in_db(self):
        ''' Returns true if tweet is in database
        '''
        if ff.db.tweets.find_one({'tweetid': self.tweetid}):
            return True
        else:
            return False

    def _gameid(self):
        ''' Returns the gameid for a tweet based on posted time and teamid
        '''
        if self.teamid:
            onehour = 60 * 60 * 1000
            fourhours = 4 * onehour
            result = ff.db.games.aggregate([
                {'$project': {
                    'gameid': '$gameid',
                    'hometeam': '$hometeam',
                    'awayteam': '$awayteam',
                    'scheduled': '$scheduled',
                    'start': {'$subtract': ['$scheduled', onehour]},
                    'end': {'$add': ['$scheduled', fourhours]}
                }
                },
                {'$match': {
                    '$and': [
                        {'$or': [{'hometeam': self.teamid},
                                 {'awayteam': self.teamid}
                                 ]},
                        {'start': {'$lte': self.postedtime}},
                        {'end': {'$gte': self.postedtime}}
                    ]
                }
                }

            ])

            if result:
                for r in result:
                    if 'gameid' in r:
                        return r['gameid']
            return None

    def _dict(self):
        ''' Returns a dictionary for the tweet object
        '''
        return vars(self)

    def _add_db(self):
        ''' Adds the tweet to the database
        '''
        try:
            # Skip if retweeted
            if not self.retweeted:
                # Check if tweet is in database
                if not self._in_db():
                    result = ff.db.tweets.insert_one(self._dict())
                    return True
            return False
        except:
            print "Could not add %s to database." % (self.tweetid)
            print "Error:", sys.exc_info()
