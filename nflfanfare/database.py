from pymongo import MongoClient

from nflfanfare import secrets as sec


class DB:
    ''' Database handling
    '''

    def __init__(self):
        ''' Creates database engine
        '''
        self.client = MongoClient(
            'mongodb://%s:%s@%s:27017/NFL2016' % (sec.mongouser,
                                                  sec.mongopwd,
                                                  sec.mongohost))
        self.db = self.client.NFL2016

        self.teams = self.db.teams
        self.games = self.db.games
        self.plays = self.db.plays
        self.pfrplays = self.db.pfrplays
        self.tweets = self.db.tweets
        self.teamtweets = self.db.teamtweets
