#!/usr/bin/env python

import os, sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

import nflfanfare as ff

games = list(ff.db.games.find())

for g in games:
	status = ff.sched.game_status(g['gameid'])
	if status == "historic":
		if g['tweetcounts']['hometeam'] < 3000:
			try:
				ff.col.collect_historic_by_team(g['gameid'], g['hometeam'], verbose=True, method='bulk')
			except:
				pass
		if g['tweetcounts']['awayteam'] < 3000:
			try:
				ff.col.collect_historic_by_team(g['gameid'], g['awayteam'], verbose=True, method='bulk')
			except:
				pass	
