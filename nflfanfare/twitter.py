from bs4 import BeautifulSoup
from datetime import datetime
import numpy as np
import os
import secrets as sec
from selenium import webdriver
import sys
import time
from TwitterAPI import TwitterAPI
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

    def search(self, searchterm):
        ''' Searches for term and returns tweets
            Waits if API quota has been met
        '''
        result = self.twi.request(
            'search/tweets', {'q': searchterm, 'lang': 'en', 'count': 100})
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

    def search_historic(self, search, start, end, live=True):
        ''' Finds historic tweets and adds them to the database
        '''
        # Get NFL teamid from hashtag
        team = ff.team.teamid_from_hashtag(search)

        # Clean up inputs
        search = urllib2.quote('#' + search, safe='')
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
                            self.add_to_db(tweet, team, verbose=True)
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

        browser.quit()

    def search_game_tweets(self, gameid):
        ''' Finds tweets for a gameid
        '''
        pass
