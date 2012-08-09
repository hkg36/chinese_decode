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

    try:
        public_time_line=client.statuses__user_timeline(uid=uid,since_id=since_id,count=200)
    except Exception,e:
        print e
        return

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
        dbc.execute("insert or ignore into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(one['id'],0))
        if comments_count>0:
            dbc.execute("select last_comment_id from weibo_commentlast where weibo_id=?",(one['id'],))
            dbrow=dbc.fetchone()
            since_id=0
            if dbrow!=None:
                since_id=dbrow[0]

            try:
                weibores=client.comments__show(id=one['id'],since_id=since_id,count=200)
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
            except Exception,e:
                print e
        else:
            dbc.execute("replace into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(one['id'],0))
        db.commit()
    db.commit()
    db.close()

def RecheckComment(client):
    #befor_time=time.time()-60*60*2
    #timestr=time.strftime("%Y-%m-%d %X",time.gmtime(time.time()))
    #print timestr
    db=sqlite3.connect("data/weibo_word_base.db")
    dbc=db.cursor()
    #dbc.execute("select weibo_id,last_comment_id from weibo_commentlast where CreatedTime<?",(befor_time,))
    dbc.execute("select weibo_id,last_comment_id,CreatedTime from weibo_commentlast")
    processed_count=0
    for resrow in dbc:
        res_time=time.mktime(time.strptime(resrow[2],"%Y-%m-%d %X"))
        if processed_count>100:
            break
        if time.time()-res_time>60*60*48:
            continue
        if time.time()-res_time>3*60:
            weibo_id=resrow[0]
            last_comment_id=resrow[1]

            try:
                processed_count+=1
                weibores=client.comments__show(id=weibo_id,since_id=last_comment_id)
                if weibores.has_key('comments'):
                    comments=weibores['comments']
                else:
                    comments=[]
                if len(comments)>0:
                    last_one_comment=comments[0]
                    dbc.execute("replace into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(weibo_id,last_one_comment['id']))
                else:
                    dbc.execute("update weibo_commentlast set CreatedTime=CURRENT_TIMESTAMP where weibo_id=?",(weibo_id,))
                for onec in comments:
                    print onec['text']
                    print onec['id']
                    dbc.execute("insert into weibo_comment(weibo_id,comment_weibo_id,word) values(?,?,?)",(onec['id'],weibo_id,onec['text']))
            except Exception,e:
                print e
                db.commit()
                return
    db.commit()

if __name__ == '__main__':

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

    uid=[2766066821,2778063742,2787229190,2203797085,2143649153,2482527830,1693658273,1712334485,2706392963,1462615901]
    for one in uid:
        ReadUserWeibo(one,client)

    RecheckComment(client)
