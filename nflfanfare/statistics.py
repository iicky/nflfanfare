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

    def gametime_sentiment_by_team(self, gameid, teamid):
        ''' Returns gametime sentment by game and teamid
        '''
        # Creates timeseries dataframe for gameid
        game = ff.db.games.find_one({'gameid': gameid})
        pre = game['starttime'] - timedelta(hours=1)
        times = [pre + timedelta(minutes=x) for x in xrange(0, 5 * 60, 5)]
        tdf = pd.DataFrame(index=times)

        # Find tweets by teamid
        tweets = ff.db.tweets.aggregate([
            {'$match': {'gameid': gameid,
                        'teamid': teamid,
                        'sentiment.sent_compound': {'$ne': '0'}
                        }
             },
            {'$project': {'_id': 0,
                          'teamid': '$teamid',
                          'sent_compound': '$sentiment.sent_compound',
                          'postedtime': '$postedtime'
                          }
             }
        ])
        df = pd.DataFrame(list(tweets))

        # Returns dataframe of gametime sentiment
        if not df.empty:
            # Processes dataframe grouping
            df = df.set_index('postedtime')
            df['sent_compound'] = df['sent_compound'].astype(float)
            group = df.groupby(pd.TimeGrouper('5Min'))

            tdf['count'] = group.sent_compound.count()
            tdf['count'] = tdf['count'].fillna(0).astype(int)
            tdf['mean_sent'] = group.sent_compound.mean()
            tdf['time'] = tdf.index
            tdf = tdf.reset_index(drop=True)
            return json.loads(tdf.to_json(orient='records'))

        else:
            tdf['count'] = 0
            tdf['mean'] = None
            tdf['time'] = tdf.index
            tdf = tdf.reset_index(drop=True)
            return json.loads(tdf.to_json(orient='records'))

    def gametime_sentiment(self, gameid):
        ''' Returns gametime sentment by game and teamid
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        game['homesent'] = self.gametime_sentiment_by_team(gameid, game['hometeam'])
        game['awaysent'] = self.gametime_sentiment_by_team(gameid, game['awayteam'])

        return game

