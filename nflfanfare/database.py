from contextlib import contextmanager
import secrets as sec
import sqlalchemy as sql
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime


class DB:
    ''' Database handling
    '''

    def __init__(self):
        ''' Creates database engine
        '''
        self.enginestr = 'mysql+pymysql://%s:%s@%s:3306/NFL?charset=utf8mb4&use_unicode=1' % (
            sec.mysqluser, sec.mysqlpwd, sec.mysqlhost)
        self.engine = sql.create_engine(self.enginestr, pool_recycle=86400)
        self.Session = sessionmaker(bind=self.engine)
        self.Base = declarative_base()

    @contextmanager
    def con(self):
        session = scoped_session(self.Session)
        try:
            yield session
        except:
            session.rollback()
        finally:
            session.close()


class Schedule(DB().Base):
    __tablename__ = 'schedule'

    gameid = Column(String, primary_key=True)
    eid = Column(String)
    week = Column(String)
    seasontype = Column(String)
    hometeam = Column(String)
    awayteam = Column(String)
    starttime = Column(DateTime)
    endtime = Column(DateTime)
    stadium = Column(String)
    weather = Column(String)
    wontoss = Column(String)
    attendance = Column(String)
    vegasline = Column(String)
    overunder = Column(String)

    def __init__(self, gameid=None,
                 eid=None,
                 week=None,
                 seasontype=None,
                 hometeam=None,
                 awayteam=None,
                 starttime=None,
                 endtime=None,
                 stadium=None,
                 weather=None,
                 wontoss=None,
                 attendance=None,
                 vegasline=None,
                 overunder=None):
        self.gameid = gameid
        self.eid = eid
        self.week = week
        self.seasontype = seasontype
        self.hometeam = hometeam
        self.awayteam = awayteam
        self.starttime = starttime
        self.endtime = endtime
        self.stadium = stadium
        self.weather = weather
        self.wontoss = attendance
        self.vegasline = vegasline
        self.overunder = overunder


class TeamHashtags(DB().Base):
    __tablename__ = 'teamhashtags'

    hashtag = Column(String, primary_key=True)
    teamid = Column(String)

    def __init__(self, hashtag=None,
                 teamid=None):
        self.hashtag = hashtag
        self.teamid = teamid


class Tweets(DB().Base):
    __tablename__ = 'tweets'

    tweetid = Column(String, primary_key=True)
    teamid = Column(String)
    userid = Column(String)
    username = Column(String)
    realname = Column(String)
    userlocation = Column(String)
    usertimezone = Column(String)
    userprofileimg = Column(String)
    tweettext = Column(String)
    language = Column(String)
    hashtags = Column(String)
    usermentions = Column(String)
    postedtime = Column(DateTime)
    collectedtime = Column(DateTime)
    sent_pos = Column(String)
    sent_neg = Column(String)
    sent_neu = Column(String)
    sent_compound = Column(String)
    gameid = Column(String)
    source = Column(String)

    def __init__(self, tweetid=None,
                 teamid=None,
                 userid=None,
                 username=None,
                 realname=None,
                 userlocation=None,
                 usertimezone=None,
                 userprofileimg=None,
                 tweettext=None,
                 language=None,
                 hashtags=None,
                 usermentions=None,
                 postedtime=None,
                 collectedtime=None,
                 sent_pos=None,
                 sent_neg=None,
                 sent_neu=None,
                 sent_compound=None,
                 gameid=None,
                 source=None):
        self.tweetid = tweetid
        self.teamid = teamid
        self.userid = userid
        self.username = username
        self.realname = realname
        self.userlocation = userlocation
        self.usertimezone = usertimezone
        self.userprofileimg = userprofileimg
        self.tweettext = tweettext
        self.language = language
        self.hashtags = hashtags
        self.usermentions = usermentions
        self.postedtime = postedtime
        self.collectedtime = collectedtime
        self.sent_pos = sent_pos
        self.sent_neg = sent_neg
        self.sent_neu = sent_neu
        self.sent_compound = sent_compound
        self.gameid = gameid
        self.source = source


class Teams(DB().Base):
    __tablename__ = 'teams'

    teamid = Column(String, primary_key=True)
    teamcity = Column(String)
    teamname = Column(String)
    conference = Column(String)
    division = Column(String)
    homecolor = Column(String)
    awaycolor = Column(String)
    pfrid = Column(String)

    def __init__(self, teamid=None,
                 teamcity=None,
                 teamname=None,
                 conference=None,
                 division=None,
                 homecolor=None,
                 awaycolor=None,
                 pfrid=None):
        self.teamid = teamid
        self.teamcity = teamcity
        self.teamname = teamname
        self.conference = conference
        self.division = division
        self.homecolor = homecolor
        self.awaycolor = awaycolor
        self.pfrid = pfrid
