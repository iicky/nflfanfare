import pandas as pd
from sqlalchemy.sql.expression import func

import nflfanfare as ff


class Team:
    ''' Schedule class
    '''

    def __init__(self):
        pass

    def team_ids(self):
        ''' Returns NFL Team IDs as a list
        '''
        with ff.db.con() as ses:
            result = ses.query(ff.db.teams).all()
            return [r.teamid for r in result]

    def team_hashtags(self, teamid):
        ''' Returns all hashtags for NFL team
        '''
        with ff.db.con() as ses:
            result = ses.query(ff.db.teamhashtags).filter_by(
                teamid=teamid).all()
            return [r.hashtag for r in result]

    def rand_hashtag(self, teamid):
        ''' Returns random hashtag for NFL team
        '''
        with ff.db.con() as ses:
            result = ses.query(ff.db.teamhashtags).filter_by(
                teamid=teamid).order_by(func.rand()).first()
            return result.hashtag

    def teamid_from_name(self, teamname):
        ''' Returns the team id from team full name
        '''
        with ff.db.con() as ses:
            result = ses.query(ff.db.teams).filter(func.concat(
                Teams.teamcity, ' ', Teams.teamname) == teamname).one()
            return result.teamid

    def teamid_from_hashtag(self, hashtag):
        ''' Returns the teamid for a hashtag
        '''
        with ff.db.con() as ses:
            result = ses.query(ff.db.teamhashtags).filter_by(
                hashtag=hashtag).one()
            return result.teamid

    def pfrid_from_teamid(self, teamid):
        ''' Returns the PFR ID from team id
        '''
        with ff.db.con() as ses:
            result = ses.query(ff.db.teams).filter_by(teamid=teamid).one()
            return result.pfrid

    def teams(self):
        ''' Returns teams as dataframe
        '''
        df = pd.read_sql_table('teams', ff.db.engine)
        return df
