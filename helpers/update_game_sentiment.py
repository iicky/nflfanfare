#!/usr/bin/env python

import os, sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from nflfanfare import schedule

schedule.Schedule().update_db_game_sentiment()
