#!/usr/bin/env python
import logging
import logging.config
import os
import yaml

import nflfanfare.database as db
import nflfanfare.gamecenter as gc
import nflfanfare.games as games
import nflfanfare.secrets as sec
import nflfanfare.statistics as stats
import nflfanfare.teams as teams
import nflfanfare.twitter as twitter


def log_path():
    return logging.FileHandler(sec.log_path)

# Read and define logger
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
with open(path + '/logger.yaml', 'rt') as f:
    config = yaml.safe_load(f.read())
logging.config.dictConfig(config)

db = db.DB()
