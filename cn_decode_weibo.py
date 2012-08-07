#-*-coding:utf-8-*-
from decoder import *
from weibo_autooauth import *
import sqlite3
import string
import time

def ReadUserWeibo(uid,client):
    db=sqlite3.connect("data/weibo_word_base.db")
    dbc=db.cursor()
    dbc.execute("select last_weibo_id from weibo_lastweibo where user_id=?",(uid,))
    dbrow=dbc.fetchone()
    since_id=0
    if dbrow!=None:
        since_id=dbrow[0]

    public_time_line=client.statuses__user_timeline(uid=uid,since_id=since_id)

    if public_time_line.has_key('statuses'):
        statuses=public_time_line['statuses']
    else:
        statuses=[]
    if len(statuses)>0:
        last_one = statuses[0]
        dbc=db.cursor()
        dbc.execute("replace into weibo_lastweibo(user_id,last_weibo_id) values(?,?)",(uid,last_one['id']))

    dbc=db.cursor()
    for one in statuses:
        comments_count=one['comments_count']
        dbc.execute("insert into weibo_text(weibo_id,word) values(?,?)",(one['id'],one['text']))
        if comments_count>0:
            dbc.execute("select last_comment_id from weibo_commentlast where weibo_id=?",(one['id'],))
            dbrow=dbc.fetchone()
            since_id=0
            if dbrow!=None:
                since_id=dbrow[0]

            weibores=client.comments__show(id=one['id'],since_id=since_id)
            if weibores.has_key('comments'):
                comments=weibores['comments']
            else:
                comments=[]
            if len(comments)>0:
                last_one_comment=comments[0]
                dbc.execute("replace into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(one['id'],last_one_comment['id']))
            for onec in comments:
                print onec['text']
                print onec['id']
                dbc.execute("insert into weibo_comment(weibo_id,comment_weibo_id,word) values(?,?,?)",(onec['id'],one['id'],onec['text']))
        else:
            dbc.execute("replace into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(one['id'],0))
    db.commit()
    db.close()

if __name__ == '__main__':

    """word_dict_root=WordTree()
    fp=open('chinese_data.txt','r') ##网友整理
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    fp=open('word3.txt','r')## 来自国家语言委员会
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    fp=open('SogouLabDic.dic','r') ##来自搜狗互联网数据库
    all_line=fp.readlines()
    fp.close()
    word_dict_root.LoadSogouData(all_line)"""

    APP_KEY = '685427335'
    APP_SECRET = '1d735fa8f18fa94d87cd9196867edfb6'
    CALLBACK_URL = 'http://www.hkg36.tk/weibo/authorization'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'

    db=sqlite3.connect("data/weibo_word_base.db")
    try:
        db.execute("create table weibo_oauth(app_key varchar(32) not null,user_name varchar(32) not null,weibo_id varchar(32) not null,key varchar(30) not null,expires_time int not null,PRIMARY KEY(app_key,user_name))")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_commentlast(weibo_id int not null PRIMARY KEY,last_comment_id int not null,CreatedTime TimeStamp NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_lastweibo(user_id int not null PRIMARY KEY,last_weibo_id int not null,CreatedTime TimeStamp NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_text(weibo_id int not null PRIMARY KEY,word varchar(1024) not null)")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_comment(weibo_id int not null PRIMARY KEY,comment_weibo_id int not null references weibo_text(weibo_id) on update cascade,word varchar(1024) not null)")
    except Exception,e:
        print e

    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
    dbc=db.cursor()
    dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and user_name=? and expires_time>?",(APP_KEY,user_name,time.time()+3600))
    dbrow=dbc.fetchone()
    if dbrow!=None:
        client.set_access_token(dbrow[1],dbrow[2])
    else:
        oauth=GetWeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
        dbc=db.cursor()
        dbc.execute("replace into weibo_oauth(app_key,user_name,weibo_id,key,expires_time) values(?,?,?,?,?)",(APP_KEY,user_name,oauth['uid'],oauth['access_token'],oauth['expires_in']))
        db.commit()
        client.set_access_token(oauth['access_token'], oauth['expires_in'])
    db.close()

    uid=[1552348913,2679813811]
    for one in uid:
        ReadUserWeibo(one,client)
