#coding: utf-8

from sqlalchemy import desc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DBSession = sessionmaker(autoflush=True, expire_on_commit=False)

def ConnectDB():
    DB_CONNECT_STRING = 'mysql+mysqldb://root:root@localhost/v2exfriends?charset=utf8'
    engine = create_engine(DB_CONNECT_STRING, encoding='utf8', convert_unicode=True)
    DBSession.configure(bind=engine)
    session = DBSession()
    return session

