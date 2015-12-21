#!/usr/bin/env python

import nflfanfare.collector as col
import nflfanfare.database as db
import nflfanfare.schedule as sched
import nflfanfare.statistics as stats
import nflfanfare.team as team
import nflfanfare.tweet as tweet
import nflfanfare.twitter as twitter


col = col.Collector()
db = db.DB()
sched = sched.Schedule()
stats = stats.Statistics()
team = team.Team()
twitter = twitter.Twitter()

# Database tables
db.schedule = database.Schedule
db.teamhashtags = database.TeamHashtags
db.teams = database.Teams
db.tweets = database.Tweets

