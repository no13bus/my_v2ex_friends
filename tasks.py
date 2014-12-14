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
from redis.exceptions import WatchError
from sqlalchemy import distinct


celery = Celery('v2ex', broker='redis://localhost:6379/0', backend='redis://localhost')
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


### 现在问题是在函数执行的过程中 代理ip的使用次数是慢慢逐个的涨的，如果执行一次执行时间过长，那么可能这
### 一回合在半小时的时候完成，那么在下一次的过程中，可能这个ip的使用间隔没有超过1个小时或者等于1个小时
### 现在采取的就是吧间隔的时间变长 变成1个小时加15分钟
@celery.task(max_retries=3)
def users_tasks_fun(proxies_key, xid, url, proxies, datatype):
    ### race condition
    with rd.pipeline() as pipe:
        while 1:
            try:
                pipe.watch(proxies_key)
                print 'proxies_key===%s' % proxies_key
                count = int(rd.hget(proxies_key, 'num'))
                if count<150:
                    pipe.multi()
                    pipe.hincrby(proxies_key, 'num', 1)
                    pipe.execute()
                    break
                else:
                    logger.debug('proxies=%s is used out!!' % proxies['http'])
                    pipe.unwatch()
                    return [xid, False, 0]
            except WatchError:
                continue
            except Exception as ex0:
                print ex0
                return [xid, False, 1]


    # count = int(rd.hget(proxies_key, 'num'))
    # if count >= 150:
    #     logger.debug('proxies=%s is used out!!' % proxies['http'])
    #     return [uid, False]
    # else:
    #     rd.hincrby(proxies_key, 'num', 1)
    ###
    try:
        r = requests.get(url, proxies=proxies, timeout=60)
        print 'requests is ok'
    except Exception as exc :
        raise users_tasks_fun.retry(countdown=1, exc=exc)
    try:
        item = json.loads(r.content)
    except:
        print 'json is error'
        return [xid, False, 2]

    if datatype=='topics' and type(item)==list and len(item)>0:
        item = item[0]
    if type(item)==dict and 'status' in item and item['status'] == 'error':
        logger.debug('proxies=%s is used out.url=%s' % (proxies['http'], url))
        return [xid, False]
    if datatype!='replies':
        if not('created' in item):
            return [xid, False, 3]
        

    if datatype=='users':
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
            print 'user is ok'
            print item['username']
    elif datatype=='topics':
        topic_time = datetime.datetime.fromtimestamp(item['created'])
        topic_item = session.query(Topics).filter_by(topicid=item['id']).first()
        if not topic_item:
            node = session.query(Nodes).filter_by(nodeid=item['node']['id']).first()
            member = session.query(Users).filter_by(userid=item['member']['id']).first()
            if not member:
                return
            if not node:
                return
            topic = Topics(topicid=item['id'], title=item['title'], url=item['url'],
                         content=item['content'], content_rendered=item['content_rendered'],
                         replies=item['replies'], node=item['node']['id'],
                         member=item['member']['id'], topic_created=topic_time)
            session.add(topic)
            session.commit()
            print 'topics are ok'
            print item['url']
    elif datatype == 'replies':
        if not item:
            return [xid,False, 4]
        topic = session.query(Topics.topicid).filter_by(topicid=xid).first()
        if not topic:
            logger.debug('topic %s is not existed' % xid)
            return [xid, False, 5]
        for itemx in item:
            member = session.query(Users.userid).filter_by(userid=itemx['member']['id']).first()
            if not member:
                return
            reply_time = datetime.datetime.fromtimestamp(itemx['created'])
            reply_item = session.query(Replies).filter_by(replyid=itemx['id']).first()
            if not reply_item:
                reply = Replies(replyid=itemx['id'], content=itemx['content'], content_rendered=itemx['content_rendered'],
                                thanks=itemx['thanks'], member=itemx['member']['id'], topic=xid, reply_created=reply_time)
                session.add(reply)
                session.commit()
                print 'replies are ok'
                print itemx['id']
    return [xid, True]


@celery.task
def users_tasks():
    user_total = 86660
    proxies_num = int(rd.get('proxies:count'))
    last1 = session.query(Users.userid).order_by('-userid')
    if last1.count():
        last = last1[0].userid
        if last >= user_total and last1.count()>=user_total:
            logger.debug('user_total---all is done')
            return
        all_userid = [i.userid for i in session.query(Users.userid)]
        all_id = range(1, last+1)
        c = list(set(all_id).difference(set(all_userid)))
        c.sort()
        if not c:
            clen = 0
            cmax = last
        else:
            clen = len(c)
            cmax = max(c)
        if clen<proxies_num*100:
            tmp = cmax + proxies_num*100 - clen
            if tmp > user_total:
                final_get_userids = c + range(1+cmax,user_total+1)
            else:
                ccc = proxies_num*100 - clen
                final_get_userids = c + range(1+last,ccc+last+1)
        else:
            final_get_userids = c

    else:
        final_get_userids = range(1,proxies_num*100+1)


    # user_total = 86660
    # # http://v2ex.com/api/members/show.json?id=79988
    # proxies_num = int(rd.get('proxies:count'))
    # ### get the userid list to handle
    # last = session.query(Users).order_by('-userid')[0].userid
    # all_userid = [i.id for i in session.query(Users)]
    # all_id = [i.userid for i in session.query(Users)]
    # c = list(set(all_userid).difference(set(all_id)))
    # if not c:
    #     logger.debug('all is done')
    #     return
    # if len(c)<proxies_num*100:
    #     tmp = max(c) + proxies_num*100 - len(c)
    #     if tmp > user_total:
    #         final_get_userids = c + range(1+max(c),user_total+1)
    #     else:
    #         ccc = proxies_num*100 - len(c)
    #         final_get_userids = c + range(1+last,ccc+last+1)
    # else:
    #     final_get_userids = c

    logger.debug('now final_get_userids first is %s' % final_get_userids[0])


    for xx in range(1, proxies_num+1):
        for uid in final_get_userids[0:99]:
            ip_port = rd.hget('proxies:%s' % xx, 'ip_port')
            print 'userid=%s' % uid
            url = 'http://v2ex.com/api/members/show.json?id=%s' % uid
            proxies = {'http': ip_port}
            users_tasks_fun.delay('proxies:%s' % xx, uid, url, proxies, 'users')
        if final_get_userids[100:]:
            final_get_userids = final_get_userids[100:]
        else:
            logger.debug('all is done')
            return

        ll = len(final_get_userids)
        logger.debug('final_get_userids=%s' % ll)
        logger.debug('xx=%s' % xx)

@celery.task
def replies_tasks():
    # replies_total = 1576974
    topics_total = 148993
    proxies_num = int(rd.get('proxies:count'))
    last1 = session.query(Replies.topic).order_by('-topic')
    if last1.count():
        last = last1[0].topic
        if last >= topics_total and last1.count()>=topics_total:
            logger.debug('replies_total---all is done')
            return
        #### notice!!! all_topicid = [i[0] for i in session.query(Replies.topic)] is easily be killed when data is big. So 
        #### Replies.topic should be distinct..
        all_topicid = [i[0] for i in session.query(distinct(Replies.topic))]
        all_id = [i.topicid for i in session.query(Topics.topicid).filter('replies>0')]
        c = list(set(all_id).difference(set(all_topicid)))
        c.sort()
        if not c:
            clen = 0
            cmax = last
        else:
            clen = len(c)
            cmax = max(c)
        if clen<proxies_num*100:
            tmp = cmax + proxies_num*100 - clen
            if tmp > topics_total:
                final_get_topicids = c + range(1+cmax,topics_total+1)
            else:
                ccc = proxies_num*100 - clen
                final_get_topicids = c + range(1+last,ccc+last+1)
        else:
            final_get_topicids = c

    else:
        final_get_topicids = range(1,proxies_num*100+1)



    logger.debug('reply-task::now final_get_topicids first is %s' % final_get_topicids[0])

    for xx in range(1, proxies_num+1):
        for tid in final_get_topicids[0:99]:
            ip_port = rd.hget('proxies:%s' % xx, 'ip_port')
            print 'topicid=%s' % tid
            url = 'http://v2ex.com/api/replies/show.json?topic_id=%s' % tid
            proxies = {'http': ip_port}
            users_tasks_fun.delay('proxies:%s' % xx, tid, url, proxies, 'replies')
        if final_get_topicids[100:]:
            final_get_topicids = final_get_topicids[100:]
        else:
            logger.debug('all is done')
            return

        logger.debug('reply-task::final_get_topicids=%s' % len(final_get_topicids))
        logger.debug('xx=%s' % xx)


@celery.task
def topics_tasks():
    topics_total = 148993
    proxies_num = int(rd.get('proxies:count'))
    last1 = session.query(Topics.topicid).order_by('-topicid')
    if last1.count():
        last = last1[0].topicid
        if last >= topics_total and last1.count()>=topics_total:
            logger.debug('topics_total---all is done')
            return
        all_topicid = [i.topicid for i in session.query(Topics.topicid)]
        # all_topicid = session.query(Topics.topicid).all()
        all_id = range(1, last+1)
        c = list(set(all_id).difference(set(all_topicid)))
        c.sort()
        if not c:
            clen = 0
            cmax = last
        else:
            clen = len(c)
            cmax = max(c)
        if clen<proxies_num*100:
            tmp = cmax + proxies_num*100 - clen
            if tmp > topics_total:
                final_get_topicids = c + range(1+cmax,topics_total+1)
            else:
                ccc = proxies_num*100 - clen
                final_get_topicids = c + range(1+last,ccc+last+1)
        else:
            final_get_topicids = c

    else:
        final_get_topicids = range(1,proxies_num*100+1)



    logger.debug('now final_get_topicids first is %s' % final_get_topicids[0])

    for xx in range(1, proxies_num+1):
        for tid in final_get_topicids[0:99]:
            ip_port = rd.hget('proxies:%s' % xx, 'ip_port')
            print 'userid=%s' % tid
            url = 'http://v2ex.com/api/topics/show.json?id=%s' % tid
            proxies = {'http': ip_port}
            users_tasks_fun.delay('proxies:%s' % xx, tid, url, proxies, 'topics')
        if final_get_topicids[100:]:
            final_get_topicids = final_get_topicids[100:]
        else:
            logger.debug('all is done')
            return

        logger.debug('final_get_topicids=%s' % len(final_get_topicids))
        logger.debug('xx=%s' % xx)

@celery.task
def nodes_tasks():
    ip_port = rd.hget('proxies:11', 'ip_port')
    url = 'http://v2ex.com/api/nodes/all.json'
    proxies = {'http':ip_port}
    try:
        r = requests.get(url, proxies=proxies, timeout=60)
        print 'success'
    except Exception as exc :
        raise users_tasks_fun.retry(countdown=1, exc=exc)
    try:
        j = json.loads(r.content)
    except:
        return False

    # r = requests.get(url)
    # j = json.loads(r.content)
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
    if ip_keys:
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

    url = 'http://www.xici.net.co/nn'
    try:
        r = requests.get(url, timeout=60)
    except:
        print 'over'
        return
    try:
        b = BeautifulSoup(r.content)
    except:
        print 'over'
        return
    trs = b.select('tr')[1:]
    for tr in trs:
        httporhttps = tr.select('td')[6].string
        if httporhttps == 'HTTP':
            ip_port = '%s:%s' % (tr.select('td')[2].string, tr.select('td')[3].string)
            print 'ip_port is %s. next we test it.' % ip_port
            group_list.append(testproxy.s(ip_port))

    # url = 'http://www.proxy360.cn/default.aspx'
    # try:
    #     r = requests.get(url, timeout=60)
    # except:
    #     print 'over'
    #     return
    # try:
    #     b = BeautifulSoup(r.content)
    # except:
    #     print 'over'
    #     return
    # trs = b.select('.proxylistitem')
    # for tr in trs:
    #     htype = tr.select('div')[0].select('span')[2].text
    #     htype = htype.replace(' ', '').replace('\r\n', '')

    #     if htype == u'高匿':
    #         h1 = tr.select('div')[0].select('span')[0].text
    #         h1 = h1.replace(' ', '').replace('\r\n', '')
    #         h2 = tr.select('div')[0].select('span')[1].text
    #         h2 = h2.replace(' ', '').replace('\r\n', '')

    #         ip_port = '%s:%s' % (h1, h2)
    #         print 'ip_port is %s. next we test it.' % ip_port
    #         group_list.append(testproxy.s(ip_port))
    trs = []
    with open('proxy.txt', 'rb') as f1:
        trs = f1.readlines()
    for tr in trs:
        ip_port = tr.replace('\r\n','') 
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

