#!/usr/bin/env python

import nflfanfare as ff

games = ff.sched.all_games()

for g in games.gameid:
	status = ff.sched.game_status(g)
	if status == "recent":
		if ff.sched.tweet_count(g) < 5000:
			try:
				ff.col.collect_recent(g, verbose=True)
			except:
				pass
		