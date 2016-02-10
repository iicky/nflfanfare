from datetime import datetime, timedelta
import json
import pandas as pd
import pymongo
import pytz
import tzlocal

import nflfanfare as ff


class Statistics:
    ''' Schedule class
    '''

    def __init__(self):
        pass

    def game_tweet_counts(self):
        ''' Returns pandas dataframe of game info and tweet counts
        '''

        result = ff.db.games.find().sort([('gameid', pymongo.ASCENDING)])
        df = pd.DataFrame(list(result))

        df['hometweets'] = df.tweetcounts.map(lambda t: t['hometeam'])
        df['awaytweets'] = df.tweetcounts.map(lambda t: t['awayteam'])
        df['totaltweets'] = df.tweetcounts.map(lambda t: t['total'])

        df = df[["gameid", "week", "seasontype", "hometeam",
                 "awayteam", "starttime", "hometweets", "awaytweets", "totaltweets"]]

        df['status'] = df.gameid.apply(ff.sched.game_status)

        # Convert to UTC then local timezone
        local = tzlocal.get_localzone()
        df['starttime'] = df.starttime.apply(
            lambda d: pytz.timezone('UTC').localize(d)).astype(datetime)
        df['starttime'] = df.starttime.apply(lambda d: datetime.strftime(
            d.astimezone(local), '%Y/%m/%d %I:%M%p %Z'))
        df['starttime'] = df.starttime.astype(str)

        return df

    def teams_list(self):
        ''' Returns a list of team info
        '''
        df = ff.team.teams()
        return df

    def gametimes(self, gameid):
        ''' Returns timeseries for gameid
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        pre = game['starttime'] - timedelta(hours=1)
        times = [pre + timedelta(minutes=x) for x in xrange(0, 5 * 60, 5)]

        return times

    def game_tweets_df(self, gameid):
        ''' Returns tweets dataframe for gameid
        '''
        times = self.gametimes(gameid)

        # Find tweets by teamid
        tweets = ff.db.tweets.aggregate([
            {'$match': {'gameid': gameid}},
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

        df = pd.DataFrame(list(tweets))
        if not df.empty:
            tindex = pd.DatetimeIndex(df['postedtime'])
            for i in range(0, len(times)):
                index = tindex.indexer_between_time(times[i].time(),
                                                    (times[
                                                     i] + timedelta(minutes=5)).time(),
                                                    include_end=False)
                df.ix[index, 'timegroup'] = i
                df.ix[index, 'gametime'] = times[i]
        return df

    def gametime_sentiment(self, gameid):
        ''' Returns dataframe of gametime sentiment
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        tdf = self.game_tweets_df(gameid)
        gdf = pd.DataFrame({'time': self.gametimes(gameid)})

        if not tdf.empty:
            tdf = tdf[tdf.sent_compound != 0]
            group = tdf.groupby(['teamid', 'timegroup'])
            counts = group.sent_compound.count()
            means = group.sent_compound.mean()
            teams = tdf.teamid.unique()

            # Handling empty teams
            if game['hometeam'] in teams:
                stats = pd.concat({'homecount': counts[game['hometeam']],
                                   'homesentiment': means[game['hometeam']],
                                   }, axis=1)
                gdf = gdf.merge(stats, how='outer',
                                left_index=True, right_index=True)
            else:
                gdf['homecount'] = 0
                gdf['homesentiment'] = None

            if game['awayteam'] in teams:
                stats = pd.concat({'awaycount': counts[game['awayteam']],
                                   'awaysentiment': means[game['awayteam']],
                                   }, axis=1)
                gdf = gdf.merge(stats, how='outer',
                                left_index=True, right_index=True)
            else:
                gdf['awaycount'] = 0
                gdf['awaysentiment'] = None

            gdf['homecount'] = gdf['homecount'].fillna(0).astype(int)
            gdf['awaycount'] = gdf['awaycount'].fillna(0).astype(int)
            gdf = gdf.where((pd.notnull(gdf)), None)

            return gdf

        else:
            gdf['homecount'] = 0
            gdf['awaycount'] = 0
            gdf['homesentiment'] = None
            gdf['awaysentiment'] = None

            return gdf

    def gametime_info(self, gameid):
        ''' Returns gametime sentment by game and teamid
        '''
        game = ff.db.games.find_one({'gameid': gameid})

        # Team colors
        homecolors = ff.db.teams.find_one({'teamid': game['hometeam']})['colors']
        awaycolors = ff.db.teams.find_one({'teamid': game['awayteam']})['colors']

        # Primary color
        game['homecolorpri'] = homecolors[0]
        if game['homecolorpri'] == awaycolors[0]:
            game['awaycolorpri'] = awaycolors[1]
        else:
            game['awaycolorpri'] = awaycolors[0]

        # Secondary color
        game['homecolorsec'] = homecolors[1]
        if game['homecolorsec'] == awaycolors[1]:
            game['awaycolorsec'] = awaycolors[0]
        else:
            game['awaycolorsec'] = awaycolors[1]

        return game
