from datetime import datetime, timedelta
import pandas as pd

import nflfanfare as ff


class Plays:
    ''' Plays class
    '''
    def __init__(self, gameid):

        # Game id and game information
        self.gameid = gameid
        self.game = ff.games.Game(gameid)

        if self.game.info:

            # Game plays
            self.plays = self._plays()
            self.plays = self._timeouts()

    def _plays(self):
        ''' Returns a data frame of plays for a game
        '''
        result = ff.db.plays.find({'gameid': self.gameid})
        if result:
            df = pd.DataFrame(list(result))

            # Jacksonvile fix
            fixcols = ['desc', 'posteam', 'yrdln']
            if (self.game.hometeam == 'JAX' or
                    self.game.awayteam == 'JAX'):
                for fcol in fixcols:
                    df[fcol] = df[fcol].str.replace('JAC', 'JAX')

            # Set timeouts to 3
            df['awaytimeouts'] = 3
            df['hometimeouts'] = 3

            return df
        return None

    def _timeouts(self):
        ''' Calculates the number of time outs for each team
        '''
        df = self.plays

        # Remaining time out lookup
        lookup = {'#1': 2, '#2': 1, '#3': 0}

        halfs = [df.loc[df.qtr <= 2],
                 df.loc[(df.qtr > 2) & (df.qtr < 5)],
                 df.loc[df.qtr >= 5]]

        # Empty plays dataframe
        df = pd.DataFrame()

        for half in halfs:

            # Half timeouts
            tos = half.desc[half.desc.str.contains('Timeout #')]

            # Iterate through timeouts
            for i, to in tos.iteritems():

                # Timeouts left
                toleft = lookup[to.split(' ')[1]]

                # Deduct home or away timeouts
                if self.game.hometeam in to:
                    half.loc[half.index >= i,
                             'hometimeouts'] = toleft
                if self.game.awayteam in to:
                    half.loc[half.index >= i,
                             'awaytimeouts'] = toleft

            # Append half to game plays
            df = df.append(half)

        return df
