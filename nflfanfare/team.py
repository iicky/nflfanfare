import pandas as pd
from pymongo import MongoClient
import random

import nflfanfare as ff


class Team:
    ''' Schedule class
    '''

    def __init__(self):
        pass

    def team_ids(self):
        ''' Returns NFL Team IDs as a list
        '''
        return ff.db.teams.\
            find({}, {'teamid': 1, '_id': 0}).\
            distinct('teamid')

    def team_hashtags(self, teamid):
        ''' Returns all hashtags for NFL team
        '''
        try:
            return ff.db.teams.find_one({'teamid': teamid})['hashtags']
        except:
            return None

    def rand_hashtag(self, teamid):
        ''' Returns random hashtag for NFL team
        '''
        try:
            return random.choice(
                ff.db.teams.find_one({'teamid': teamid})['hashtags'])
        except:
            return None

    def teamid_from_name(self, teamname):
        ''' Returns the team id from team full name
        '''
        try:
            result = ff.db.teams.aggregate([
                {'$project': {
                    'teamid': '$teamid',
                    'fullname': {'$concat': ['$teamcity', ' ', '$teamname']}
                }
                },
                {'$match': {'fullname': teamname}}
            ])
            return list(result)[0]['teamid']
        except:
            return None

    def teamid_from_hashtag(self, hashtag):
        ''' Returns the teamid for a hashtag
        '''
        try:
            return ff.db.teams.find_one({'hashtags': {"$in": [hashtag]}})['teamid']
        except:
            return None

    def pfrid_from_teamid(self, teamid):
        ''' Returns the PFR ID from team id
        '''
        try:
            return ff.db.teams.find_one({'teamid': teamid})['pfrid']
        except:
            return None

    def teamid_from_pfrid(self, pfrid):
        ''' Returns the team id from PFR ID
        '''
        try:
            return ff.db.teams.find_one({'pfrid': pfrid})['teamid']
        except:
            return None

    def teams(self):
        ''' Returns teams as dataframe
        '''
        return pd.DataFrame(list(ff.db.teams.find({}, {'_id': 0})))
