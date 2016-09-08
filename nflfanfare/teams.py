import pandas as pd
import random

import nflfanfare as ff


def team_ids():
    ''' Returns the NFL team ids in the database as a list
    '''
    return sorted(ff.db.teams.
                  find({}, {'teamid': 1, '_id': 0}).
                  distinct('teamid'))


def teams():
    ''' Returns the NFL teams and information as a data frame
    '''
    return pd.DataFrame(list(ff.db.teams.find({}, {'_id': 0})))


class Team:
    ''' Class for handling team information
    '''
    def __init__(self, match):

        # Match query
        self.match = match

        # Info dictionary
        self.info = self._info()

        # Team identifiers
        self.teamid = None
        self.pfrid = None
        self.username = None
        self.teamcity = None
        self.teamname = None
        self.fullname = None

        # Geographic
        self.conference = None
        self.division = None

        # Team attributes
        self.colors = None
        self.hashtags = None

        # Populate team properties if match
        if self.info:
            self._properties()

    def _info(self):
        ''' Returns a team info dictionary from the teams dataframe.
            Allows for matching by NFL ID, PFR ID, Twitter username,
            and full team name, and team name.
        '''
        # Data frame of all teams in database
        df = teams()

        # Add full name for teams
        df['fullname'] = (df.teamcity + ' ' + df.teamname)

        column = None
        # NFL ID
        if self.match in list(df.teamid):
            column = 'df.teamid'
        # PFR ID
        if self.match in list(df.pfrid):
            column = 'df.pfrid'
        # Twitter username
        if self.match in list(df.username):
            column = 'df.username'
        # Full name
        if self.match in list(df.fullname):
            column = 'df.fullname'
        # Team name
        if self.match in list(df.teamname):
            column = 'df.teamname'

        # Return dictionary if match
        if column:
            return df[eval(column) == self.match].\
                   to_dict(orient='records')[0]
        return None

    def _properties(self):
        ''' Populates the team properties using the team information
        '''
        if self.info:
            # Team identifiers
            self.teamid = self.info['teamid']
            self.pfrid = self.info['pfrid']
            self.username = self.info['username']
            self.teamcity = self.info['teamcity']
            self.teamname = self.info['teamname']
            self.fullname = (self.info['teamcity'] + ' ' +
                             self.info['teamname'])

            # Geographic
            self.conference = self.info['conference']
            self.division = self.info['division']

            # Team attributes
            self.colors = self.info['colors']
            self.hashtags = self.info['hashtags']

    def random_hashtag(self):
        ''' Returns a random team hashtag
        '''
        if self.hashtags:
            return random.choice(self.hashtags)
        return None
