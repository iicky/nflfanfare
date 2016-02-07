from datetime import datetime, timedelta
import numpy as np
import os
import pandas as pd
import nflgame
import nflvid
import urllib2
import pytz
import time
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
        return '%s %s' % (ff.team.teamid_from_pfrid(location[0].lower()), location[1])

    def pfr_plays(self, gameid):
        ''' Returns dataframe of plays from Pro Football Reference
        '''
        game = ff.db.games.find_one({'gameid': gameid})
        start = pytz.timezone('UTC').localize(game['starttime'])
        start = start.astimezone(pytz.timezone('US/Eastern'))
        pfrid = ff.team.pfrid_from_teamid(game['hometeam'])
        url = self.pfr_boxscore_link(start.year, start.month, start.day, pfrid)

        try:
            # Open url in browser
            browser = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',
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
                if (not line == ''
                        and not line[0] == ','
                        and not 'Quarter' in line):
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
        df = df.sort_values(by=['drive', 'quarter', 'gameclock', 'playid'], ascending=[
                            True, True, False, True])

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

        for play in df.playid:
            url = self.neulion_url(game, play, start)
            path = self.download_path(game, play)

            if not self.has_film_info(gameid, play):
                self.download_video(url, path, verbose=verbose)
                self.add_film_info(gameid, play, verbose=verbose)
            else:
                if verbose:
                    print "Film info for game %s play %s is already collected." % (gameid, play)
            if os.path.exists(path):
                os.remove(path)

        directory = '/'.join(path.split('/')[0:-1])
        if os.path.exists(directory):
            if not os.listdir(directory):
                os.rmdir(directory)

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

    def add_film_info(self, gameid, playid, verbose=False):
        ''' Adds film information for play into database
        '''
        warnings.filterwarnings("ignore")
        game = ff.db.games.find_one({'gameid': gameid})
        info = nflgame.game.Game(game['eid'])
        start = self.to_eastern(game['starttime'])

        try:
            play = nflvid.play(info, str(playid))

            if not play == None:
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
                filmurl, filmstart, filmend, filmlength = None, None, None, None

            ff.db.games.update_one({'gameid': gameid,
                                    'plays.playid': playid},
                                   {'$set': {
                                       'plays.$.filmurl': filmurl,
                                       'plays.$.filmstart': None if filmstart == None else str(filmstart),
                                       'plays.$.filmend': None if filmend == None else str(filmend),
                                       'plays.$.filmlength': None if filmlength == None else str(filmlength)
                                   }
            })
            if verbose:
                print "Added film info for game %s play %s to database." % (gameid, playid)

        except:
            print "Could not add film info for game %s play %s" % (gameid, playid)

    def has_film_info(self, gameid, playid):
        ''' Returns true if play has film info
        '''
        result = ff.db.games.find_one({'gameid': gameid,
                                       'plays': {
                                           '$elemMatch': {
                                               'playid': playid,
                                               'filmstart': {'$exists': 'true'}
                                           }}
                                       })
        if not result == None:
            return True
        return False

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
