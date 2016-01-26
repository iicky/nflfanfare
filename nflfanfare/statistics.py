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
        times = [pre + timedelta(minutes=x) for x in xrange(0, 5*60, 5)]
        tdf = pd.DataFrame({'time':times})
        
        # Find tweets by teamid
        tweets = ff.db.tweets.aggregate([
            {'$match': {'gameid': gameid, 
                        'teamid': teamid, 
                        'sentiment.sent_compound': {'$ne': 0}
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
            tindex = pd.DatetimeIndex(df['postedtime'])

            for i in range(0, len(tdf.time)):
                index = tindex.indexer_between_time(tdf.time[i].time(), 
                                            (tdf.time[i]+timedelta(minutes=5)).time(),
                                            include_end=False)
                df.ix[index, 'group'] = i
                            
            group = df.groupby('group')    
            counts = group.sent_compound.count()
            means = group.sent_compound.mean()
            stats = pd.concat({'count': counts, 'mean_sent': means}, axis=1)
            tdf = tdf.merge(stats, how='outer', left_index=True, right_index=True)
            
            tdf['count'] = tdf['count'].fillna(0).astype(int)
            tdf = tdf.reset_index(drop=True)   
            return tdf.to_dict(orient='records')
            
        else:
            tdf['count'] = 0
            tdf['mean_sent'] = None
            tdf = tdf.reset_index(drop=True)
            return tdf.to_dict(orient='records')

    def gametime_sentiment(self, gameid):
        ''' Returns gametime sentment by game and teamid
        '''
        game = ff.db.games.find_one({'gameid': gameid})

        # Team colors
        homecolors = ff.db.teams.find_one({'teamid': game['hometeam']})['colors']
        awaycolors = ff.db.teams.find_one({'teamid': game['awayteam']})['colors']

        game['homecolor'] = homecolors[0]
        if game['homecolor'] == awaycolors[0]:
            game['awaycolor'] = awaycolors[1]
        else:
            game['awaycolor'] = awaycolors[0]

        return game
