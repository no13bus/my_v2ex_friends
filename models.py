#coding=utf8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, String, DateTime
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey



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
    topicid = Column(Integer, unique=True, index=True)
    title =  Column(String(240), default='')
    url =  Column(String(100), default='')
    content = Column(String(10000), default='')
    content_rendered = Column(String(10000), default='')
    replies = Column(Integer, default=0)
    member = Column(Integer, ForeignKey("users.userid"), default=0)
    node = Column(Integer, ForeignKey("nodes.nodeid"), default=0)
    topic_created = Column(DateTime, default=datetime.now)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'title:%s content:%s' % (self.title, self.content)

###这个是不是要考虑放到redis里面去呢？
class Tags(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), default='')
    created = Column(DateTime, default=datetime.now)
    def __repr__(self):
        return 'name:%s ' % self.name
###这个是不是要考虑放到redis里面去呢？
class User_Tag(Base):
    __tablename__ = 'user_tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer, ForeignKey("users.userid"), default=0)
    tag = Column(Integer, ForeignKey("tags.id"), default=0)
    created = Column(DateTime, default=datetime.now)
    def __repr__(self):
        return 'username:%s tag_name:%s' % (self.user.username, self.tag.name)

###用户的每次统计的最热点击帖子 回复最多帖子 最新帖子 这个统计结果是不是要入库 还是redis缓存起来
###还有就是2个人之间的比较结果？

class Replies(Base):
    __tablename__ = 'replies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    replyid = Column(Integer, unique=True, index=True)
    thanks = Column(Integer, default=0)
    content = Column(String(1000), default='')
    content_rendered = Column(String(1000), default='')
    member = Column(Integer, ForeignKey("users.userid"), default=0)
    topic = Column(Integer, ForeignKey("topics.topicid"), default=0)
    reply_created = Column(DateTime, default=datetime.now)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'content:%s' % self.content