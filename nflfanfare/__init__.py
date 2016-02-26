#!/usr/bin/env python

import nflfanfare.collector as col
import nflfanfare.database as db
import nflfanfare.plays as plays
import nflfanfare.schedule as sched
import nflfanfare.secrets as sec
import nflfanfare.statistics as stats
import nflfanfare.team as team
import nflfanfare.tweet as tweet
import nflfanfare.twitter as twitter


col = col.Collector()
db = db.DB()
plays = plays.Plays()
sched = sched.Schedule()
stats = stats.Statistics()
team = team.Team()
twitter = twitter.Twitter()
