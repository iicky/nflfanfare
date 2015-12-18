from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

class Tweet:
    ''' Returns tweet object from API result
    '''

    def __init__(self, tweet):
        ''' Defines tweet properties from API
        '''

        self.tweetid = tweet['id']

        # User information
        self.userid = tweet['user']['id']
        self.username = tweet['user']['screen_name']
        self.realname = re.sub(r'\\|\"|\'', '', tweet['user']['name'])
        self.userlocation = tweet['user']['location'] if not tweet[
            'user']['location'] == '' else None
        self.usertimezone = tweet['user']['time_zone']
        self.userprofileimg = tweet['user']['profile_image_url']

        # Tweet information
        self.tweettext = re.sub(r'\\|\"|\'', '', tweet['text'])
        self.language = tweet['lang']
        self.hashtags = ', '.join([h['text'] for h in tweet['entities']['hashtags']]) if len(
            tweet['entities']['hashtags']) > 0 else None
        self.usermentions = ' ,'.join([h['screen_name'] for h in tweet['entities'][
                                      'user_mentions']]) if len(tweet['entities']['user_mentions']) > 0 else None
        self.postedtime = datetime.strptime(
            tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        self.collectedtime = datetime.utcnow()
        self.retweeted = False if not tweet.has_key(
            'retweeted_status') else True

        # Sentiment information
        sid = SentimentIntensityAnalyzer().polarity_scores(tweet['text'])
        self.sent_pos = round(sid['pos'], 3)
        self.sent_neg = round(sid['neg'], 3)
        self.sent_neu = round(sid['neu'], 3)
        self.sent_compound = round(sid['compound'], 3)