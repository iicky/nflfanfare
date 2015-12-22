import nflfanfare as ff

class Statistics:
    ''' Schedule class
    '''

    def __init__(self):
        pass

    def game_tweet_counts(self):
    	''' Returns pandas dataframe of game info and tweet counts
    	'''
    	df = ff.sched.all_games()
    	#df['tweetcount'] = df.gameid.apply(ff.sched.tweet_count)
    	return df

    def teams_list(self):
    	''' Returns a list of team info
    	'''
    	df = ff.team.teams()
    	return df
