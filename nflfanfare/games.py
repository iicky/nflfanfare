from datetime import datetime, timedelta
import pandas as pd

import nflfanfare as ff


def games(state=None):
    ''' Returns a dataframe of game ids in the database
    '''
    # Find games
    result = ff.db.games.find({},
                              {'gameid': 1, 'eid': '1',
                               'scheduled': 1, '_id': 0})

    # Add game state
    df = pd.DataFrame(list(result))
    df['state'] = df.scheduled.apply(lambda x: _state(x))

    # Subset if state argument is set
    if state:
        # Convert to list if state is string
        if type(state) is str:
            state = [state]
        return df[df.state.isin(state)].reset_index(drop=True)
    return df


def _state(start):
    ''' Returns game state
    '''
    pre = start - timedelta(hours=1)
    post = start + timedelta(hours=4)
    now = datetime.utcnow()
    oneweek = now - timedelta(days=7)
    upcoming = now + timedelta(hours=1)
    starting = now + timedelta(minutes=15)

    # Historic game (> 1 week)
    if start < oneweek:
        return "historic"
    # Recent game (< 1 week)
    elif start > oneweek and post < now:
        return "recent"
    # Live game (on now)
    elif start < now and post > now:
        return "live"
    # Game starting (within 15 minutes)
    elif start > now and start < starting:
        return "starting"
    # Upcoming game (within 1 hour)
    elif start > now and start < upcoming:
        return "upcoming"
    # Pending game (> 1 hour away)
    elif start > datetime.now():
        return "pending"

    return None


class Game:
    ''' Class for handling game information
    '''
    def __init__(self, match):

        # Match query
        self.match = match

        # Info dictionary
        self.info = self._info()

        if self.info:

            # Set parameters from dictionary
            for key in self.info.keys():
                setattr(self, key, self.info[key])

            # Pre and post game times
            self.pregame = self.scheduled - timedelta(hours=1)
            self.postgame = self.scheduled + timedelta(hours=4)

            self.state = _state(self.scheduled)

    def _info(self):
        ''' Returns a game info dictionary from the database.
            Allows for matching by gameid or EID.
        '''
        df = games()

        query = None
        if self.match in list(df.gameid):
            query = 'gameid'
        if self.match in list(df.eid):
            query = 'eid'

        if query:
            result = ff.db.games.find_one({query: self.match})
            return result
        return None
