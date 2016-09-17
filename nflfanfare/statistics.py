from datetime import datetime, timedelta
import json
import pandas as pd
import pymongo
import pytz
import tzlocal

import nflfanfare as ff


class Game():
    ''' Class for calculating game statistics
        Initialized based on a gameid string.
        The paramater tweet_buckets sets the number of minutes into
        which the gametime is divided when calculating the sentiment.
    '''
    def __init__(self, gameid, tweet_buckets=5):

        # Game id and game information
        self.gameid = gameid
        self.game = ff.games.Game(gameid)

        if self.game.info:

            # Time series
            self.times = None

            # Game tweets
            self.tweets = self._tweets()
            self.tweets = self._timeseries(self.tweets,
                                           tweet_buckets,
                                           'postedtime')

    def _tweets(self):
        ''' Returns a dataframe containing the game tweets
        '''
        # Find tweets
        tweets = ff.db.tweets.aggregate([
            {'$match': {'gameid': self.gameid,
                        'sentiment.sent_compound': {'$ne': 0}}},
            {'$project': {'_id': 0,
                          'teamid': '$teamid',
                          'tweettext': '$tweettext',
                          'hashtags': '$hashtags',
                          'usermentions': '$usermentions',
                          'sent_compound': '$sentiment.sent_compound',
                          'postedtime': '$postedtime'
                          }
             }
        ])

        # Create data frame
        return pd.DataFrame(list(tweets))

    def _timeseries(self, df, x, time_column):
        ''' Creates a time series for a game in x minute intervals
            between the pre and post gametimes using the
            time_column as an index.
            Returns a dataframe with the time group and gametime
            marked within new columns.
        '''
        # Minutes between pre and post game
        minutes = (self.game.postgame -
                   self.game.pregame).seconds / 60

        # Creates a list of datetimes in 5 minute intervals
        self.times = [self.game.pregame + timedelta(minutes=_)
                      for _ in xrange(0, minutes, x)]

        # Check if not empty
        if not df.empty:

            # Set tweet postedtime as index
            tindex = pd.DatetimeIndex(df[time_column])

            # Creates an index of all the times within the dataframe
            # between two times
            for i in range(0, len(self.times)):
                index = tindex.indexer_between_time(
                    self.times[i].time(),
                    (self.times[i] +
                     timedelta(minutes=x)).time(),
                    include_end=False)

                # Mark the time group and gametime
                df.ix[index, 'timegroup'] = i
                df.ix[index, 'gametime'] = self.times[i]

        return df

    def _sentiment(self):
        ''' Returns a data frame of gametime sentiment
        '''
        # Set dataframe with times
        df = pd.DataFrame({'gametime': self.times})

        if not self.tweets.empty:

            # Determine teams in game tweets
            teams = self.tweets.teamid.unique()

            # Group by teamid and timegroup
            group = self.tweets.groupby(['teamid', 'gametime'])

            # Aggregate columns
            counts = group.sent_compound.count()
            means = group.sent_compound.mean()

            # Home team sentiment
            # Check if home team has tweets
            if self.game.hometeam in teams:

                # Concatenate aggregate columns for hometeam
                stats = pd.concat({'homecount': counts[self.game.hometeam],
                                   'homesentiment': means[self.game.hometeam]},
                                  axis=1).reset_index()
                # Merge onto dataframe
                df = df.merge(stats, how='outer', on='gametime')
            else:
                df['homecount'] = 0
                df['homesentiment'] = 0

            # Away team sentiment
            # Check if away team has tweets
            if self.game.awayteam in teams:

                # Concatenate aggregate columns for awayteam
                stats = pd.concat({'awaycount': counts[self.game.awayteam],
                                   'awaysentiment': means[self.game.awayteam]},
                                  axis=1).reset_index()
                # Merge onto dataframe
                df = df.merge(stats, how='outer', on='gametime')
            else:
                df['awaycount'] = 0
                df['awaysentiment'] = 0

            # Replace empty counts with 0 and empty sentiment with None
            df['homecount'] = df['homecount'].fillna(0).astype(int)
            df['awaycount'] = df['awaycount'].fillna(0).astype(int)
            df = df.where((pd.notnull(df)), None)

        return df
