#!/usr/bin/env python

import argparse
import logging
import os
import pymongo
import sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if path not in sys.path:
    sys.path.insert(1, path)
del path

log = logging.getLogger('helpers.monitor_game')

import nflfanfare as ff

# Parse the game gameid for monitoring
parser = argparse.ArgumentParser()
parser.add_argument("--gameid", help="The game id to monitor.")
args = parser.parse_args()

try:

    # Check if gameid is a valid game
    result = ff.db.games.find_one({'gameid': args.gameid})
    if not result:
        log.error('Could not find game %s in the database.' % args.gameid)
    else:
        # Begin monitoring the gameid
        col = ff.gc.Collector()
        col._monitor(args.gameid)

except:
    log.error('Unknown error: %s line %s: %s' %
              (sys.exc_info()[0],
               sys.exc_info()[2].tb_lineno,
               sys.exc_info()[1]))
