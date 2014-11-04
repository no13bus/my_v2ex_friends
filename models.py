#coding=utf8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, String, DateTime
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from config import DB_CONNECT_STRING


Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, unique=True)
    status =  Column(String(20), default='')
    url =  Column(String(100), default='')
    username = Column(String(50), default='')
    website = Column(String(100), default='')
    twitter = Column(String(50), default='')
    psn = Column(String(50), default='')
    github = Column(String(50), default='')
    btc = Column(String(50), default='')
    location = Column(String(50), default='')
    tagline = Column(String(50), default='')
    bio = Column(String(1000), default='')
    avatar_normal = Column(String(200), default='')
    user_created = Column(DateTime, default=datetime.now)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'userid:%s_username:%s' % (self.userid, self.username)

class Nodes(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nodeid = Column(Integer, unique=True)
    name =  Column(String(20), default='')
    url =  Column(String(100), default='')
    title = Column(String(50), default='')
    title_alternative = Column(String(50), default='')
    topics = Column(Integer, default=0) ##topic nums
    header = Column(String(1000), default='')
    footer = Column(String(1000), default='')
    node_created = Column(DateTime, default=datetime.now)
    avatar_normal = Column(String(200), default='')
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'name:%s title:%s' % (self.name, self.title)

class Topics(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    topicid = Column(Integer, unique=True)
    title =  Column(String(20), default='')
    url =  Column(String(100), default='')
    content = Column(String(1000), default='')
    content_rendered = Column(String(1000), default='')
    replies = Column(Integer, default=0)
    member = Column(Integer, ForeignKey("users.userid"), default=0)
    node = Column(Integer, ForeignKey("nodes.nodeid"), default=0)
    topic_created = Column(DateTime, default=datetime.now)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'title:%s content:%s' % (self.title, self.content)

class Replies(Base):
    __tablename__ = 'replies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    thanks = Column(Integer, default=0)
    content = Column(String(1000), default='')
    content_rendered = Column(String(1000), default='')
    member = Column(Integer, ForeignKey("users.userid"), default=0)
    reply_created = Column(DateTime, default=datetime.now)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'content:%s' % self.content