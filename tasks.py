#coding=utf8
from celery import Celery,platforms,group,chain
import time
import settings
import requests
import json
from db import ConnectDB
from models import Users, Nodes, Replies, Topics
import datetime

import re
import random
from bs4 import BeautifulSoup
import redis
import logging
import logging.handlers
from redis.exceptions import LockError, WatchError


celery = Celery(
    'v2ex', broker='redis://localhost:6379/0', backend='redis://localhost')
celery.config_from_object('settings')
session = ConnectDB()

LOG_FILE = 'v2ex.log'
handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=1024 * 1024 * 50, backupCount=5)
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('crawlog')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
rd = settings.RD

class ForException(Exception):
    pass


class ForException2(Exception):
    pass

@celery.task
def test2():
    time.sleep(3)
    p_len = settings.RD.llen('ip_port')
    if p_len>=4:
        print settings.RD.lpop('ip_port')
        print '---delete'
        print settings.RD.llen('ip_port')

@celery.task
def test1():
    with r.pipeline() as pipe:
        while 1:
            try:
                pipe.watch('ip_port')
                p_len = pipe.llen('ip_port')
                if p_len>=4:
                    pipe.multi()
                    pipe.lpop('ip_port')
                    pipe.execute()
                    print pipe.llen('ip_port')
                    break
                else:
                    pipe.unwatch()
                    break
            except WatchError:
                continue



# @celery.task
# def user_topics(username):
#     url = 'http://v2ex.com/member/%s/topics?p=1' % username
#     r = requests.get(url, timeout=60*4)
#     c = r.content
#     b = BeautifulSoup(c)
#     page_num = b.select('.inner')[2].select('.fade')[0].text
#     page_num = int(page_num.replace('1/',''))
#     for page in xrange(1,page_num+1):
#         url = 'http://v2ex.com/member/%s/topics?p=%s' % (username, page)
#         r = requests.get(url, timeout=60*4)
#         c = r.content
#         b = BeautifulSoup(c)
#         topics = b.select('.cell.item')
#         for topic in topics:
#             title = topic.select('span')[0].string
#             repies_count = int(topic.select('.count_livid')[0]) if topic.select('.count_livid') else 0
#             topic_info = topic.select('span')[1].text.split(u'\xa0\u2022\xa0')
#             topic_node_name = topic_info[0].replace(' ','')
#             topic_url = 'http://v2ex.com%s' % topic.select('span')[0].a['href']
#             patt = re.compile(u'.*?t/(\d+)#.*')
#             topicid = int(re.findall(patt,topic_url)[0])

#             topic_r = requests.get(topic_url, headers=headers, timeout=60*4)
#             topic_c = topic_r.content
#             topic_b = BeautifulSoup(topic_c)
#             ## 帖子不一定有内容
#             tc = topic_b.select('.topic_content')
#             topic_content = u''
#             if tc:
#                 for i in topic_b.select('.topic_content'):
#                     topic_content = topic_content + i.text

#             topic_info2 = topic_b.select('small.gray')[0].text.split(u'\xb7')
#             topic_created = topic_info2[1].replace(' ','')
#             topic_clicks = topic_info2[2].replace(' ','').replace(u'\u6b21\u70b9\u51fb', '')
#             topic_clicks = int(topic_clicks)
#             member = session.query(Users).filter(Users.username=username).first()
#             node = session.query(Nodes).filter(Nodes.name=topic_node_name).first()
#             Topics(topicid=topicid, title=title, url=topic_url, content=topic_content,
#                 repies=repies_count, member=member, node=node, topic_created=topic_created)


# @celery.task
# def user_replies(username):


@celery.task(max_retries=3)
def users_tasks_fun(proxies_key, uid, url, proxies):
    ### race condition
    with rd.pipeline() as pipe:
        while 1:
            try:
                pipe.watch(proxies_key)
                count = int(rd.hget(proxies_key, 'num'))
                if count<150:
                    pipe.multi()
                    pipe.hincrby(proxies_key, 'num', 1)
                    pipe.execute()
                    break
                else:
                    logger.debug('proxies=%s is used out!!' % proxies['http'])
                    pipe.unwatch()
                    return [uid, False]
            except WatchError:
                continue

    # count = int(rd.hget(proxies_key, 'num'))
    # if count >= 150:
    #     logger.debug('proxies=%s is used out!!' % proxies['http'])
    #     return [uid, False]
    # else:
    #     rd.hincrby(proxies_key, 'num', 1)
    ###
    try:
        r = requests.get(url, proxies=proxies, timeout=60)
        print 'success'
    except Exception as exc :
        raise users_tasks_fun.retry(countdown=1, exc=exc)
    try:
        item = json.loads(r.content)
    except:
        return [uid, False]
    if item['status'] == 'error':
        logger.debug('proxies=%s is used out.url=%s' % (proxies['http'], url))
        return [uid, False]
    if not('created' in item):
        return [uid, False]

    usertime = datetime.datetime.fromtimestamp(item['created'])
    useritem = session.query(Users).filter_by(userid=item['id']).first()
    if not useritem:
        user = Users(userid=item['id'], status=item['status'], url=item['url'],
                     username=item['username'], website=item[
                         'website'], twitter=item['twitter'],
                     psn=item['psn'], github=item['github'], btc=item['btc'],
                     location=item['location'], tagline=item[
                         'tagline'], bio=item['bio'],
                     avatar_normal=item['avatar_normal'], user_created=usertime)
        session.add(user)
        session.commit()
        print item['username']
        
    return [uid, True]


@celery.task
def users_tasks():
    # http://v2ex.com/api/members/show.json?id=79988
    proxies_num = int(rd.get('proxies:count'))
    ### get the userid list to handle
    last = session.query(Users).order_by('-userid')[0].userid
    all_userid = [i.id for i in session.query(Users)]
    all_id = [i.userid for i in session.query(Users)]
    c = list(set(all_userid).difference(set(all_id)))
    if len(c)<proxies_num*100:
        ccc = proxies_num*100 - len(c)
        final_get_userids = c + range(1+last,ccc+last+1)
    else:
        final_get_userids = c

    logger.debug('now final_get_userids first is %s' % final_get_userids[0])

    for xx in range(1, proxies_num+1):
        group_list = []
        for uid in final_get_userids[0:99]:
            ip_port = rd.hget('proxies:%s' % xx, 'ip_port')
            print 'userid=%s' % uid
            url = 'http://v2ex.com/api/members/show.json?id=%s' % uid
            if uid > 84113:
                logger.debug('all is done')
                return
            proxies = {'http': ip_port}
            group_list.append(users_tasks_fun.s('proxies:%s' % xx, uid, url, proxies))
        if group_list:
            g1 = group(group_list)
            g = g1().get()
            print g
        final_get_userids = final_get_userids[100:]
        print len(final_get_userids)
        logger.debug('final_get_userids=%s' % len(final_get_userids))
        logger.debug('xx=%s' % xx)

        


@celery.task
def nodes_tasks():
    url = 'http://v2ex.com/api/nodes/all.json'
    r = requests.get(url)
    j = json.loads(r.content)
    for item in j:
        nodetime = datetime.datetime.fromtimestamp(item['created'])
        nodeitem = session.query(Nodes).filter_by(nodeid=item['id']).first()
        if not nodeitem:
            node = Nodes(nodeid=item['id'], name=item['name'], url=item['url'], title=item['title'],
                         title_alternative=item[
                             'title_alternative'], topics=item['topics'],
                         header=item['header'], footer=item['footer'], node_created=nodetime)
            session.add(node)
            print item['name']
    session.commit()


@celery.task
def topics_tasks():
    pass


@celery.task
def replies_tasks():
    pass


@celery.task
def proxy_tasks():
    pass


def getport(resultstring):
    exec('port = %s' % resultstring)
    port = eval('port')
    return port

@celery.task
def testproxy(ip_port):
    mysession = requests.Session()
    url = 'http://v2ex.com/api/nodes/all.json'
    proxies = {'http': ip_port}
    try:
        r = mysession.get(url, proxies=proxies, timeout=20)
        nowcount = rd.incr('proxies:count')
        rd.hset('proxies:%s' % nowcount,'ip_port', ip_port)
        rd.hincrby('proxies:%s' % nowcount, 'num', 1)
        return True
    except:
        return False


@celery.task
def proxy_task():
    # delete all proxies and proxies:count
    ip_keys = rd.keys('proxies:*')
    rd.delete(*ip_keys)
    # get the proxies
    proxyurl = 'http://pachong.org'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'pachong.org',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.101 Safari/537.36'
    }
    proxysession = requests.Session()
    try:
        r = proxysession.get(proxyurl, timeout=60)
    except:
        print 'I can not get the date of pachong.org'
    if r.status_code != 200:
        print 'the status is not good. status_code is %s' % r.status_code
        return
    ht = BeautifulSoup(r.content)
    animals = str(ht.head.find_all('script')[-1].text)
    for item in animals.split(';'):
        exec(item.replace('var', '').strip())

    table = ht.find_all('tbody')
    if not table:
        return
    table = table[0]
    # trs = table.find_all('tr', attrs={'data-type': 'anonymous'})
    trs = table.find_all('tr')
    group_list = []
    for tr in trs:
        idlestring = tr.find_all('td')[5].text
        idlestring = idlestring.replace('\n', '').replace(' ', '')
        if idlestring == u'空闲':
            ip = tr.find_all('td')[1].text
            portstring = tr.find_all('td')[2].text
            patt = re.compile(u'document.write\((.*?)\);')
            if re.findall(patt, portstring):
                resultstring = re.findall(patt, portstring)[0]
            else:
                continue
            exec('port = %s' % resultstring)
            port = eval('port')
            ip_port = '%s:%s' % (ip, port)
            print 'ip_port is %s. next we test it.' % ip_port
            group_list.append(testproxy.s(ip_port))
    g1 = group(group_list)
    g = g1().get()
    print 'it is done'



# {u'status': u'error', u'message': u'Rate Limit Exceeded', u'rate_limit': {u'hourly_remaining': 0, u'used': 120, u'hourly_quota': 120}}
# celery -A tasks worker -l info -c 100 -P gevent


# session = ConnectDB()
# a=[i.id for i in session.query(Users)]
# b = [i.userid for i in session.query(Users)]
# c = list(set(a).difference(set(b)))

@celery.task
def users_chain():
    c = chain(proxy_task.si(), users_tasks.si())
    c()

