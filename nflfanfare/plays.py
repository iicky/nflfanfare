from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import difflib
import numpy as np
import os
import pandas as pd
import nflgame
import nflvid
import nltk
from nltk import wordnet
import nltk.corpus
import nltk.tokenize.punkt
import pymongo
from selenium import webdriver
import string
from StringIO import StringIO
import pytz
import time
import urllib2
import warnings

import nflfanfare as ff


class Plays:
    ''' Plays class
    '''

    def __init__(self):
        pass

    def fix_location(self, location):
        ''' Changes pfrid to teamid in play location
        '''
        location = location.split()
        return '%s %s' % (ff.team.teamid_from_pfrid(location[0].lower()),
                          location[1])

    def pfr_plays(self, gameid):
        ''' Returns dataframe of plays from Pro Football Reference
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        start = pytz.timezone('UTC').localize(game['starttime'])
        start = start.astimezone(pytz.timezone('US/Eastern'))
        pfrid = ff.team.pfrid_from_teamid(game['hometeam'])
        url = ff.sched.pfr_boxscore_link(start.year,
                                         start.month,
                                         start.day,
                                         pfrid)

        try:
            # Open url in browser
            browser = webdriver.PhantomJS(
                executable_path='/usr/local/bin/phantomjs',
                service_log_path=os.path.devnull)
            browser.get(url)

            # Click button to get CSV
            csvlink = browser.find_elements_by_xpath(
                "//span[contains(text(), 'CSV')]")
            csvlink[1].click()

            # Get the source code for page
            html = browser.page_source.encode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
        except:
            return None
        finally:
            browser.close()
            browser.quit()

        try:
            # Find preformatted CSV
            plays = ""
            ids = soup.find('pre', attrs={'id': 'csv_pbp_data'})
            for i in ids:
                plays = i

            # Reformat CSV
            plays = plays.split('\n')
            csv = ''
            for line in plays:
                if (not line == '' and not
                        line[0] == ',' and
                        'Quarter' not in line):
                    csv += '%s\n' % line

            # Read into pandas dataframe
            columns = ['quarter', 'time', 'down', 'togo',
                       'location', 'description', 'awayscore', 'homescore']
            df = pd.read_csv(StringIO(csv), usecols=[
                             0, 1, 2, 3, 4, 5, 6, 7], names=columns)
            df = df.where((pd.notnull(df)), None)
            df['location'] = df.location.apply(self.fix_location)

            return df

        except:
            print "Could not scrape plays from PFR."
            return None

    def nflgame_plays(self, gameid):
        ''' Returns dataframe of plays from nflgame
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        info = nflgame.game.Game(game['eid'])
        drives = info.data['drives']

        events = {'playid': [],
                  'quarter': [],
                  'gameclock': [],
                  'team': [],
                  'drive': [],
                  'down': [],
                  'ydstogo': [],
                  'ydline': [],
                  'note': [],
                  'description': []
                  }

        for d in drives:
            if not d == 'crntdrv':
                plays = drives[d]['plays']
                for p in plays:
                    if 'END' in plays[p]['desc']:
                        continue
                    else:
                        events['playid'].append(p)
                        events['team'].append(plays[p]['posteam'])
                        events['drive'].append(int(d))
                        events['down'].append(plays[p]['down'])
                        events['ydstogo'].append(plays[p]['ydstogo'])
                        events['ydline'].append(plays[p]['yrdln'])
                        events['note'].append(plays[p]['note'])
                        events['description'].append(plays[p]['desc'])
                        events['quarter'].append(plays[p]['qtr'])
                        events['gameclock'].append(plays[p]['time'])

        df = pd.DataFrame(events)

        # Jacksonville fixes
        df['team'] = df.team.apply(lambda x: 'JAX' if x == 'JAC' else x)
        df['description'] = df.description.apply(
            lambda x: x.replace('JAC', 'JAX') if 'JAC' in x else x)
        df['ydline'] = df.ydline.apply(
            lambda x: x.replace('JAC', 'JAX') if 'JAC' in x else x)

        # Change playid to integer and sort
        df['playid'] = df.playid.astype(int)
        df = df.sort_values(by=['drive', 'quarter', 'gameclock', 'playid'],
                            ascending=[True, True, False, True])
        df = df.reset_index(drop=True)

        # Insert pregame
        pregame = {'playid': 'pre', 'quarter': 'PREGAME', 'note': 'PREGAME'}
        line = pd.DataFrame(pregame, index=[0])
        df = pd.concat([line, df.ix[0:]]).reset_index(drop=True)

        # Insert halftime
        halftime = {'playid': ['halfst', 'halfend'],
                    'quarter': ['HALFTIME', 'HALFTIME'],
                    'note': ['HALFTIME', 'HALFTIME']}
        line = pd.DataFrame(halftime, index=[0, 1])
        end2 = df[df.quarter == 2].iloc[-1].name
        start3 = df[df.quarter == 3].iloc[0].name
        df = pd.concat([df.ix[0:end2], line, df.ix[start3:]]
                       ).reset_index(drop=True)

        # Insert postgame
        postgame = {'playid': 'post',
                    'quarter': 'POSTGAME', 'note': 'POSTGAME'}
        line = pd.DataFrame(postgame, index=[0])
        df = pd.concat([df.ix[0:], line]).reset_index(drop=True)

        df = df.where((pd.notnull(df)), None)

        # Calculate current score for each play
        homescore = []
        awayscore = []
        hscore = 0
        ascore = 0
        for index, row in df.iterrows():
            if row['team'] == game['hometeam']:
                hscore += self.score_increase(row['note'])
            if row['team'] == game['awayteam']:
                ascore += self.score_increase(row['note'])
            homescore.append(hscore)
            awayscore.append(ascore)
        df['homescore'] = homescore
        df['awayscore'] = awayscore

        return df

    def score_increase(self, note):
        ''' Returns score increase based on nflgame play note
        '''
        if note == 'TD':
            return 6
        elif note == 'FG':
            return 3
        elif note == '2PS':
            return 2
        elif note == 'SAF':
            return 2
        elif note == 'XP':
            return 1
        else:
            return 0

    def add_plays(self, gameid):
        ''' Add plays for gameid to the database
        '''
        df = self.nflgame_plays(gameid)

        try:
            update = ff.db.games.update_one(
                {'gameid': gameid},
                {'$set': {
                    'plays': df.to_dict(orient='records')
                }
                })
        except:
            print "Could not add plays for %s to database." % gameid

    def has_play(self, gameid, playid):
        ''' Returns true if play in database
        '''
        result = ff.db.games.find_one({'gameid': gameid,
                                       'plays': {
                                           '$elemMatch': {
                                               'playid': playid}}
                                       })
        if result is not None:
            return True
        return False


class Film:
    ''' Coaches film downloader class
    '''

    def __init__(self):
        pass

    def download_video(self, url, path, verbose=False):
        ''' Downloads coaches video from NeuLion
        '''
        directory = '/'.join(path.split('/')[0:-1])
        if not os.path.exists(directory):
            os.makedirs(directory)

        if os.path.exists(path):
            if verbose:
                print "Already downloaded %s" % url
            return False

        try:
            time.sleep(np.random.lognormal(1, .5, 1)[0])
            f = urllib2.urlopen(url)
            data = f.read()
            with open(path, "wb") as code:
                code.write(data)
            if verbose:
                print "Downloaded video from %s" % url
            return True
        except:
            if verbose:
                print "Could not download from %s" % url
            return False

    def to_eastern(self, start):
        ''' Converts game starttime to US Eastern
        '''
        start = pytz.timezone('UTC').localize(start)
        return start.astimezone(pytz.timezone('US/Eastern'))

    def neulion_url(self, game, play, start):
        ''' Returns NeuLion video url
        '''
        month = '0' + str(start.month) if start.month < 10 else start.month
        day = '0' + str(start.day) if start.day < 10 else start.day

        url = 'http://smb.cdnllnwnl.neulion.com/u/nfl/nfl/coachtapes/'
        url += '%s/%s/%s/' % (start.year, month, day)
        url += '%s_%s/pc/%s_%s_1600.mp4' % (
            game['gameid'], play, game['gameid'], play)

        return url

    def download_path(self, game, play):
        ''' Returns NeuLion video download path
        '''
        path = '%s/%s/%s.mp4' % (ff.sec.downpath, game['eid'], play)
        return path

    def download_plays(self, gameid, verbose=False):
        ''' Downloads all video plays for a gameid
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        info = nflgame.game.Game(game['eid'])
        df = self.nflgame_plays(gameid)
        start = self.to_eastern(game['starttime'])

        if self.film_info_togo(gameid) > 0:

            for play in df.playid:

                url = self.neulion_url(game, play, start)
                path = self.download_path(game, play)

                if not self.has_film_info(gameid, play):
                    self.download_video(url, path, verbose=verbose)
                    self.add_film_info(gameid, play, verbose=verbose)
                else:
                    if verbose:
                        print ("Film info for game %s play %s ",
                               "is already collected.") % (gameid, play)
                if os.path.exists(path):
                    os.remove(path)

            directory = '/'.join(path.split('/')[0:-1])
            if os.path.exists(directory):
                if not os.listdir(directory):
                    os.rmdir(directory)

    def film_info_togo(self, gameid):
        ''' Returns the number of play film info missing from a gameid
        '''
        try:
            total = list(ff.db.games.aggregate([
                {'$match': {'gameid': gameid}},
                {'$project': {
                    '_id': 0,
                    'total': {'$size': '$plays'},
                }
                }]))

            done = list(ff.db.games.aggregate([
                {'$match': {'gameid': gameid}},
                {'$unwind': '$plays'},
                {'$match': {'plays.filmstart': {'$exists': 'true'}}},
                {'$group': {'_id': 'null', 'count': {'$sum': 1}}}
            ]))

            if not list(done) == []:
                return total[0]['total'] - done[0]['count']
            else:
                return total[0]['total']

        except:
            print "Could not get film info counts for game %s" % gameid
        return None

    def has_film_info(self, gameid, playid):
        ''' Returns true if play has film info
        '''
        result = ff.db.games.find_one(
            {'gameid': gameid,
             'plays': {
                 '$elemMatch': {
                     'playid': playid,
                     'filmstart': {'$exists': 'true'}
                 }}
             })
        if result is not None:
            return True
        return False

    def add_film_info(self, gameid, playid, verbose=False):
        ''' Adds film information for play into database
        '''
        warnings.filterwarnings("ignore")
        game = ff.db.games.find_one({'gameid': gameid})
        info = nflgame.game.Game(game['eid'])
        start = self.to_eastern(game['starttime'])

        try:
            play = nflvid.play(info, str(playid))

            if play is not None:
                filmurl = self.neulion_url(game, playid, start)

                filmstart = timedelta(hours=play.start.hh,
                                      minutes=play.start.mm,
                                      seconds=play.start.ss)

                if hasattr(play.end, 'ss'):
                    filmend = timedelta(hours=play.end.hh,
                                        minutes=play.end.mm,
                                        seconds=play.end.ss)
                    filmlength = filmend - filmstart
                else:
                    filmend = None
                    filmlength = None
            else:
                filmurl,
                filmstart,
                filmend,
                filmlength = None, None, None, None

            ff.db.games.update_one(
                {'gameid': gameid,
                 'plays.playid': playid},
                {'$set': {
                    'plays.$.filmurl': filmurl,
                    'plays.$.filmstart': (None if filmstart is None
                                          else str(filmstart)),
                    'plays.$.filmend': (None if filmend is None
                                        else str(filmend)),
                    'plays.$.filmlength': (None if filmlength is None
                                           else str(filmlength))
                }})
            if verbose:
                print ("Added film info for game ",
                       "%s play %s to database.") % (gameid, playid)

        except:
            print ("Could not add film info ",
                   "for game %s play %s") % (gameid, playid)


class Matcher:
    ''' Matches nflgame plays with PFR plays
    '''

    def __init__(self):
        self.tokenizer = nltk.tokenize.WordPunctTokenizer()
        self.lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

        self.stopwords = nltk.corpus.stopwords.words('english')
        self.stopwords.extend(string.punctuation)
        self.stopwords.append('')

    def pfrplays(self, gameid):
        ''' Returns dataframe of Pro Football Reference plays
        '''
        plays = list(ff.db.pfrplays.find({'gameid': gameid}).
                     sort('sequence', pymongo.ASCENDING))
        return pd.DataFrame(plays)

    def nflplays(self, gameid):
        ''' Returns dataframe of nflgame plays
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        return pd.DataFrame(list(game['plays']))

    def wordnet_pos(self, pos_tag):
        ''' Returns part of speech for a word
        '''
        if pos_tag[1].startswith('J'):
            return (pos_tag[0], wordnet.wordnet.ADJ)
        elif pos_tag[1].startswith('V'):
            return (pos_tag[0], wordnet.wordnet.VERB)
        elif pos_tag[1].startswith('N'):
            return (pos_tag[0], wordnet.wordnet.NOUN)
        elif pos_tag[1].startswith('R'):
            return (pos_tag[0], wordnet.wordnet.ADV)
        else:
            return (pos_tag[0], wordnet.wordnet.NOUN)

    def lemma_match(self, a, b):
        ''' Returns match ratio for play lemmae
        '''
        pos_a = map(self.wordnet_pos,
                    nltk.pos_tag(self.tokenizer.tokenize(a)))
        pos_b = map(self.wordnet_pos,
                    nltk.pos_tag(self.tokenizer.tokenize(b)))

        lemmae_a = [self.lemmatizer.lemmatize(
                    token.lower().strip(string.punctuation), pos)
                    for token, pos in pos_a
                    if token.lower().strip(string.punctuation)
                    not in self.stopwords]
        lemmae_b = [self.lemmatizer.lemmatize(
                    token.lower().strip(string.punctuation), pos)
                    for token, pos in pos_b
                    if token.lower().strip(string.punctuation)
                    not in self.stopwords]

        s = difflib.SequenceMatcher(None, lemmae_a, lemmae_b)
        return s.ratio()

    def match_plays(self, gameid):
        ''' Matches nflgame plays to PFR plays
            Adds update to database
        '''
        pfr = self.pfrplays(gameid)
        nfl = self.nflplays(gameid)

        for i1, r1 in pfr.iterrows():
            jac, row, ind = 0, None, None
            for i2, r2 in nfl.iterrows():

                if (r1['quarter'] == r2['quarter'] and
                        r1['down'] == r2['down']):

                    gc1 = r1['gameclock'].split(':')
                    gc2 = r2['gameclock'].split(':')
                    min1, sec1 = gc1[0], int(gc1[1])
                    min2, sec2 = gc2[0], int(gc2[1])

                    if (min1 == min2 or r1['location'] == r2['ydline']):
                        if abs(sec1 - sec2) < 10:
                            if abs(i1 - i2) < 15:
                                sim = self.lemma_match(r1['PFRdescription'],
                                                       r2['description'])
                                if sim > jac:
                                    jac = sim
                                    row = r2
                                    ind = i2

            matchid = '%s-%s' % (gameid, i1)

            if row is None:
                update = ff.db.pfrplays.update_one(
                    {'_id': matchid},
                    {'$set': {
                        'note': None,
                        'playid': None,
                        'team': None,
                        'filmstart': None,
                        'filmurl': None,
                        'filmlength': None,
                        'filmend': None,
                        'hometimeouts': None,
                        'awaytimeouts': None,
                        'predtime': None,
                        'description': None
                    }})
            else:
                update = ff.db.pfrplays.update_one(
                    {'_id': matchid},
                    {'$set': {
                        'note': row['note'],
                        'playid': row['playid'],
                        'team': row['team'],
                        'filmstart': row['filmstart'],
                        'filmurl': row['filmurl'],
                        'filmlength': row['filmlength'],
                        'filmend': row['filmend'],
                        'hometimeouts': row['hometimeouts'],
                        'awaytimeouts': row['awaytimeouts'],
                        'predtime': row['predtime'],
                        'description': row['description']
                    }})

    def mark_matched(self, gameid):
        ''' Marks a gameid as completely mark_matched
        '''
        try:
            ff.db.games.update_one(
                {'gameid': gameid},
                {'$set': {
                    'matched': True
                }})
        except:
            print "Could not tag %s as complete." % gameid

    def is_matched(self, gameid):
        ''' Returns true if play matching is complete for gameid
        '''
        result = ff.db.games.find_one(
            {'gameid': gameid,
             'matched': True
             })
        if result is not None:
            return True
        return False
