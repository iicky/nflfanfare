import secrets as sec
import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class DB:
    ''' Database handling
    '''

    def __init__(self):
        ''' Creates database engine
        '''
        self.enginestr = 'mysql+pymysql://%s:%s@%s/NFL?charset=utf8mb4&use_unicode=1' % (
            sec.mysqluser, sec.mysqlpwd, sec.mysqlhost)
        self.engine = sql.create_engine(self.enginestr)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()


class Schedule(Base):
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

class TeamHashtags(Base):
    __tablename__ = 'teamhashtags'
    
    hashtag = Column(String, primary_key=True)
    teamid = Column(String)
    
class Tweets(Base):
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
    
class Teams(Base):
    __tablename__ = 'teams'
    
    teamid = Column(String, primary_key=True)
    teamcity = Column(String)
    teamname = Column(String)
    conference = Column(String)
    division = Column(String)
    homecolor = Column(String)
    awaycolor = Column(String)
    pfrid = Column(String)