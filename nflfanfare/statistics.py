from datetime import datetime
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
