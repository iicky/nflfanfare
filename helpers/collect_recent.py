#!/usr/bin/env python

import os, sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from nflfanfare import schedule

games = ff.sched.all_games()

for g in games.gameid:
	status = ff.sched.game_status(g)
	if status == "recent":
		if ff.sched.tweet_count(g) < 5000:
			try:
				ff.col.collect_recent(g, verbose=True)
			except:
				pass
		
