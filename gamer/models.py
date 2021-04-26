from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, DateTime, Text
from scrapy.utils.project import get_project_settings

Base = declarative_base()


def db_connect():
    database_url = get_project_settings().get('CONNECTION_STRING')
    if 'mysql' in database_url:
        return create_engine(database_url, pool_size=30)
    else:
        return create_engine(database_url)


def create_table(engine):
    Base.metadata.create_all(engine)


class Forum(Base):
    __tablename__ = 'forums'
    id = Column(Integer, primary_key=True)
    name = Column('forum_name', String(80))


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column('user_name', String(20), unique=True)


class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    forum_id = Column(Integer, ForeignKey('forums.id'), primary_key=True)
    name = Column('topic_name', String(150))
    last_time = Column('last_reply_time', DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    forum_id = Column(Integer, ForeignKey('forums.id'), primary_key=True)
    floor = Column('post_floor', Integer)
    time = Column('posting_time', DateTime)
    content = Column('post_content', Text())
    user_id = Column(Integer, ForeignKey('users.id'))


class Commend(Base):
    __tablename__ = 'commends'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), primary_key=True)
    forum_id = Column(Integer, ForeignKey('forums.id'), primary_key=True)
    floor = Column('commend_floor', Integer)
    time = Column('posting_time', DateTime)
    content = Column('commend_content', String(255))
    user_id = Column(Integer, ForeignKey('users.id'))
