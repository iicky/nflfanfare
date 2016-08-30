#!/usr/bin/env python

from datetime import datetime
import logging
import os
import pytz
import sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if path not in sys.path:
    sys.path.insert(1, path)
del path

import nflfanfare as ff

log = logging.getLogger('helpers.start_collector')

now = pytz.timezone('UTC').localize(datetime.utcnow())
now = now.astimezone(pytz.timezone('US/Eastern'))

if (now.hour >= 8) or (now.hour < 2):
    log.info('Collector started.')
    ff.gc.Collector()._spawn()
