from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import numpy as np
import os
import pytz
import re
import secrets as sec
from selenium import webdriver
import sys
import time
import tzlocal
from TwitterAPI import TwitterAPI, TwitterRestPager
import urllib2

import nflfanfare as ff


class Twitter:
    ''' Twitter API Handling
    '''

    def __init__(self):
        ''' Defines tweet properties from API
        '''
        self.twi = TwitterAPI(
            sec.twitter_ckey, sec.twitter_csec, auth_type='oAuth2')

    def quota(self, request):
        ''' Returns quota information for API request
        '''
        result = self.twi.request('application/rate_limit_status')
        resources = json.loads(result.response._content)['resources']

        base = re.split('/', request)[1]
        quota = resources[base][request]

        return quota

    def search(self, search):
        ''' Searches for term and returns tweets
            Waits if API quota has been met
        '''
        result = self.twi.request(
            'search/tweets', {'q': search, 'lang': 'en', 'count': 100})
        remaining = int(result.response.headers['x-rate-limit-remaining'])
        reset = float(result.response.headers['x-rate-limit-reset'])

        # Finds the time until quota reset and sleeps
        if remaining == 0:
            delta = datetime.fromtimestamp(reset) - datetime.now()
            print "Quota reached for search/tweets. Waiting %s seconds." % delta.total_seconds()
            time.sleep(delta.total_seconds())
            result = self.twi.request('search/tweets' % int(tweetid))
            return result

        return result

    def searchid(self, tweetid):
        ''' Returns a tweet by id as string
                Waits if API quota has been met
        '''
        result = self.twi.request('statuses/show/:%d' % int(tweetid))
        remaining = int(result.response.headers['x-rate-limit-remaining'])
        reset = float(result.response.headers['x-rate-limit-reset'])

        # Finds the time until quota reset and sleeps
        if remaining == 0:
            delta = datetime.fromtimestamp(reset) - datetime.now()
            print "Quota reached for statuses/show/:id. Waiting %s seconds." % delta.total_seconds()
            time.sleep(delta.total_seconds())
            result = self.twi.request('statuses/show/:%d' % int(tweetid))
            return result

        return result

    def in_db(self, tweetid):
        ''' Returns true if tweet is in database
        '''
        result = ff.db.tweets.query.filter_by(tweetid=tweetid)
        return ff.db.session.query(result.exists()).scalar()

    def add_to_db(self, tweet, teamid, verbose=False):
        ''' Adds a tweet object to the database
        '''
        query = ff.db.tweets(tweetid=tweet.tweetid,
                             teamid=teamid,
                             userid=tweet.userid,
                             username=tweet.username,
                             realname=tweet.realname,
                             userlocation=tweet.userlocation,
                             usertimezone=tweet.usertimezone,
                             userprofileimg=tweet.userprofileimg,
                             tweettext=tweet.tweettext,
                             language=tweet.language,
                             hashtags=tweet.hashtags,
                             usermentions=tweet.usermentions,
                             postedtime=tweet.postedtime,
                             collectedtime=tweet.collectedtime,
                             sent_pos=tweet.sent_pos,
                             sent_neg=tweet.sent_neg,
                             sent_neu=tweet.sent_neu,
                             sent_compound=tweet.sent_compound)

        try:
            if not self.in_db(tweet.tweetid):
                if verbose == True:
                    print "Adding %s: %s to database for %s." % (tweet.username, tweet.tweettext, teamid)

                ff.db.session.add(query)
                ff.db.session.commit()

            else:
                if verbose == True:
                    print "Tweet %s is already in the database." % tweet.tweetid
        except:
            if verbose == True:
                print "Could not add %s to database." % (tweet.tweetid)
                print "Error:", sys.exc_info()
                ff.db.session.rollback()

    def search_historic(self, search, start, end, live=True, verbose=False):
        ''' Finds historic tweets and adds them to the database
        '''
        # Get NFL teamid from hashtag
        team = ff.team.teamid_from_hashtag(search)

        # Clean up inputs
        search = urllib2.quote('#' + search, safe='')
        
        if type(start) == datetime:
            # Convert to UTC timezone
            start = pytz.timezone('UTC').localize(start)
            end = pytz.timezone('UTC').localize(end)

            # Convert to local timezone
            local = tzlocal.get_localzone()
            start = start.astimezone(local)
            end = end.astimezone(local)

            # Make timestamp
            start = int(time.mktime(start.timetuple()))
            end = int(time.mktime(end.timetuple()))
        else:
            start = int(time.mktime(time.strptime(start, "%Y-%m-%d %H:%M")))
            end = int(time.mktime(time.strptime(end, "%Y-%m-%d %H:%M")))


        mod = '' if not live else 'f=tweets&'

        # Generate url queries
        url = 'http://mobile.twitter.com/search'
        url += '?%svertical=default' % mod
        url += '&q=%s%%20lang%%3Aen%%20' % search
        url += 'since%%3A%s%%20' % start
        url += 'until%%3A%s&src=typd' % end

        # Open url in browser
        browser = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',
                                      service_log_path=os.path.devnull)
        browser.get(url)

        # Pretend to be a human
        time.sleep(np.random.lognormal(1, .5, 1)[0])

        i = 1
        while True:

            print "Scraping page %s for %s..." % (i, urllib2.unquote(search))

            # Get the source code for page
            html = browser.page_source.encode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # Scrape tweets on page
            tweetids = soup.find_all('a', class_='last')

            for tweetid in tweetids:
                tweetid = tweetid.attrs['href'].split('/')[3]
                if self.in_db(tweetid):
                    continue
                try:
                    responses = self.searchid(tweetid)
                    for response in responses:
                        tweet = ff.tweet.Tweet(response)
                        if not tweet.retweeted:
                            self.add_to_db(tweet, team, verbose=verbose)
                except:
                    pass

            # Get the next page button and exit if does not exit
            loadmore = browser.find_elements_by_xpath(
                "//a[contains(text(), ' Load older Tweets ')]")
            if len(loadmore) == 0:
                print "End of results."
                break

            # Click the button
            button = loadmore[0]
            time.sleep(np.random.lognormal(1, .5, 1)[0])
            button.click()
            i += 1

        browser.close()
        browser.quit()

    def search_recent(self, search, start, end, verbose=False):
        ''' Pages through search API for tweets under 7 days old
        '''

        if type(start) == datetime:
            # Convert to UTC timezone
            endaware = pytz.timezone('UTC').localize(end)

            # Convert to local timezone
            local = tzlocal.get_localzone()
            endaware = endaware.astimezone(local)

            # Make timestamp
            endstamp = int(time.mktime(endaware.timetuple()))
        else:
            start = time.strptime(start, "%Y-%m-%d %H:%M")
            end = time.strptime(end, "%Y-%m-%d %H:%M")
            endstamp = int(time.mktime(end))

        # Get NFL teamid from hashtag
        team = ff.team.teamid_from_hashtag(search)
        search = '#'+search

        result = TwitterRestPager(
            self.twi, 'search/tweets', {'q': search, 'lang': 'en', 'count': 100, 'until': str(endstamp)})
        quota = self.quota('/search/tweets')

        for item in result.get_iterator():
            
            if 'text' in item:
                tweet = ff.tweet.Tweet(item)

                if not tweet.retweeted:
                    if tweet.postedtime > start and tweet.postedtime < end:
                        self.add_to_db(tweet, team, verbose=verbose)
                    elif tweet.postedtime < start:
                        break

            elif 'message' in item and item['code'] == '88':
                delta = datetime.fromtimestamp(quota['reset']) - datetime.now()
                print "Quota reached for search/tweets. Waiting %s seconds." % delta.total_seconds()
                time.sleep(delta.total_seconds())

    def search_game_tweets(self, gameid):
        ''' Finds tweets for a gameid
        '''
        info = ff.sched.game_info(gameid)
        pre, post = ff.sched.pre_post_times(info['starttime'])
        now = datetime.utcnow()

        startage = now - pre
        endage = now - post
        oneweek = now - timedelta(days=7)
        upcoming = now + timedelta(hours=1)

        if pre < oneweek:   # Historic game (> 1 week)
            print "historic game"
        elif pre > oneweek and post < now:  # Recent game (< 1 week)
            print "recent game"
        elif pre < now and post > now:  # Live game (on now)
            print "live game"
        elif pre > now and pre < upcoming:  # Upcoming game (within 1 hour)
            print "upcoming game"
        elif pre > datetime.now():  # Pending game (> 1 hour away)
            print "pending game"

    def tweet_gameid(self, tweetid):
        ''' Returns the game id for a tweet in database
        '''
        result = ff.db.session.query(ff.db.tweets, ff.db.schedule).\
            join(ff.db.schedule, sql.or_(
                ff.db.tweets.teamid == ff.db.schedule.hometeam,
                ff.db.tweets.teamid == ff.db.schedule.awayteam)).\
            filter(ff.db.tweets.tweetid == tweetid).\
            filter(ff.db.tweets.postedtime.between(
                sql.text('schedule.starttime - INTERVAL 1 HOUR'),
                sql.text('schedule.starttime + INTERVAL 4 HOUR'))).first()

        if hasattr(result, 'Schedule'):
            return result.Schedule.gameid
        return None