from datetime import datetime, timedelta
import pytz
import time

import nflfanfare as ff


class Collector:
    ''' Tweet collector class
    '''

    def __init__(self):
        pass

    def manual_live(self, gameid):
        ''' Manually start scraping of live game
        '''

        #started = datetime.utcnow()

        info = ff.sched.game_info(gameid)

        homehash = ff.team.team_hashtags(info['hometeam'])
        awayhash = ff.team.team_hashtags(info['awayteam'])
        hashtags = homehash + awayhash

        pre = info['starttime'] - timedelta(hours=1)
        post = info['starttime'] + timedelta(hours=4)

        time.sleep(3)
        started = datetime.utcnow()

        startwait = (pre - started).total_seconds()
        totalwait = (post - pre).total_seconds()

        print "Start time\t", pre
        print "Stop time\t", post
        print "Now time\t", started
        print
        print "Total time:\t", totalwait
        print "Start wait:\t", startwait



    def collect_historic(self, gameid):
        ''' Collects historic tweets for a game
        '''
        info = ff.sched.game_info(gameid)
        pre, post = ff.sched.pre_post_times(info['starttime'])

        homehash = ff.team.team_hashtags(info['hometeam'])
        awayhash = ff.team.team_hashtags(info['awayteam'])
        hashtags = homehash + awayhash

        for hashtag in hashtags:
            ff.twitter.search_historic(hashtag, pre, post, verbose=True)





