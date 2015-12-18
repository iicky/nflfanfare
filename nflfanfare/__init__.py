#!/usr/bin/env python

import nflfanfare.database as db
import nflfanfare.schedule as sched
import nflfanfare.team as team
import nflfanfare.tweet as tweet
import nflfanfare.twitter as twitter


db = db.DB()
sched = sched.Schedule()
team = team.Team()
twitter = twitter.Twitter()

# Database tables
db.schedule = database.Schedule
db.teamhashtags = database.TeamHashtags
db.teams = database.Teams
db.tweets = database.Tweets

