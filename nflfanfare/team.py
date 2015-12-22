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
        result = ff.db.teams.query.all()
        return [r.teamid for r in result]

    def team_hashtags(self, teamid):
        ''' Returns all hashtags for NFL team
        '''
        result = ff.db.teamhashtags.query.filter_by(teamid=teamid).all()
        return [r.hashtag for r in result]

    def rand_hashtag(self, teamid):
        ''' Returns random hashtag for NFL team
        '''
        result = ff.db.teamhashtags.query.filter_by(
            teamid=teamid).order_by(func.rand()).first()
        return result.hashtag

    def teamid_from_name(self, teamname):
        ''' Returns the team id from team full name
        '''
        result = ff.db.teams.query.filter(func.concat(
            ff.db.teams.teamcity, ' ', ff.db.teams.teamname) == teamname).one()
        return result.teamid

    def teamid_from_hashtag(self, hashtag):
        ''' Returns the teamid for a hashtag
        '''
        result = ff.db.teamhashtags.query.filter_by(hashtag=hashtag).one()
        return result.teamid

    def pfrid_from_teamid(self, teamid):
        ''' Returns the PFR ID from team id
        '''
        result = ff.db.teams.query.filter_by(teamid=teamid).one()
        return result.pfrid

    def teams(self):
        ''' Returns teams as dataframe
        '''
        df = pd.read_sql_table('teams', ff.db.engine)
        return df
