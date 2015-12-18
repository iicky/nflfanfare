import nflfanfare as ff


class Team:
    ''' Schedule class
    '''

    def __init__(self):
    	pass

    def team_ids(self):
        ''' Returns NFL Team IDs as a list
        '''
        query = """SELECT `teamid` FROM `teams`;"""
        result = list(ff.db.engine.execute(query))
        return [r[0] for r in result]

    def team_hashtags(self, teamid):
        ''' Returns all hashtags for NFL team
        '''
        query = """SELECT `hashtag` FROM `teamhashtags`
					WHERE `teamid`='%s';
				""" % (teamid)
        result = list(ff.db.engine.execute(query))
        return [r[0] for r in result]

    def rand_hashtag(self, teamid):
        ''' Returns random hashtag for NFL team
        '''
        query = """SELECT `hashtag` FROM `teamhashtags`
						WHERE `teamid`='%s'
						ORDER BY RAND() LIMIT 1;
			""" % (teamid)
        return list(ff.db.engine.execute(query))[0][0]

    def team_hashtag(self, hashtag):
        ''' Returns the teamid for a hashtag
        '''
        query = """ SELECT `teamid` FROM `teamhashtags`
					WHERE `hashtag`='%s'
					LIMIT 1;
				""" % (hashtag)
        return list(ff.db.engine.execute(query))[0][0]

    def teamid_from_name(self, teamname):
        ''' Returns the team id from team full name
        '''
        query = """ SELECT `teamid` FROM `teams`
					WHERE CONCAT(`teamcity`, ' ', `teamname`) = '%s';
				""" % teamname
        return list(ff.db.engine.execute(query))[0][0]

    def teamid_from_hashtag(self, hashtag):
        ''' Returns the teamid for a hashtag
        '''
        query = """ SELECT `teamid` FROM `teamhashtags`
					WHERE `hashtag`='%s'
					LIMIT 1;
				""" % (hashtag)
        return list(ff.db.engine.execute(query))[0][0]

    def pfrid_from_teamid(self, teamid):
		''' Returns the PFR ID from team id
		'''
		query = """ SELECT `PFRid` FROM `teams`
					WHERE `teamid` = '%s';
				""" % teamid
		return list(ff.db.engine.execute(query))[0][0]
