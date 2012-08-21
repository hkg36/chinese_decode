#-*-coding:utf-8-*-
from weibo_autooauth import *
import sqlite3
import time
from STTrans import STTrans

fetch_time=0
def ReadUserWeibo(uid,client):
    global fetch_time

    db=sqlite3.connect("data/weibo_word_base.db")
    dbc=db.cursor()
    dbc.execute("select last_weibo_id from weibo_lastweibo where user_id=?",(uid,))
    dbrow=dbc.fetchone()
    since_id=0
    if dbrow!=None:
        since_id=dbrow[0]
    if fetch_time%200==0:
        since_id=0

    all_time_line_statuses=[]
    try:
        for page in range(1,10):
            public_time_line=client.statuses__home_timeline(page=page,since_id=since_id,count=200,filter_by_author=1)
            if public_time_line.has_key('statuses'):
                statuses=public_time_line['statuses']
                if len(statuses)>0:
                    all_time_line_statuses.extend(statuses)
                else:
                    break
            else:
                break
    except Exception,e:
        print e
        return


    if len(all_time_line_statuses)>0:
        last_one = all_time_line_statuses[0]
        dbc=db.cursor()
        dbc.execute("replace into weibo_lastweibo(user_id,last_weibo_id) values(?,?)",(uid,last_one['id']))
        db.commit()

    dbc=db.cursor()
    for one in all_time_line_statuses:
        user=one['user']
        if user['id']==uid:
            continue
        print "}}}",one['text']
        text=STTrans.getInstanse().TransT2S(one['text'])
        dbc.execute("insert or ignore into weibo_text(weibo_id,uid,word) values(?,?,?)",(one['id'],user['id'],text))
        dbc.execute("insert or ignore into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(one['id'],0))

    db.commit()
    db.close()

    fetch_time+=1

def RecheckComment(client):
    #befor_time=time.time()-60*60*2
    #timestr=time.strftime("%Y-%m-%d %X",time.gmtime(time.time()))
    #print timestr
    db=sqlite3.connect("data/weibo_word_base.db")
    dbc=db.cursor()
    dbc.execute("select weibo_id,last_comment_id,checktime,CreatedTime from weibo_commentlast order by checktime desc")

    all_line=dbc.fetchall()
    for resrow in all_line:
        now=time.time()
        res_time=resrow[2]
        createtime=time.mktime(time.strptime(resrow[3],"%Y-%m-%d %X"))
        if now-createtime>60*60*24*10:
            continue
        if now-res_time>60*60:
            weibo_id=resrow[0]
            last_comment_id=resrow[1]

            try:
                weibores=client.comments__show(id=weibo_id,since_id=last_comment_id,count=200)
                if weibores.has_key('comments'):
                    comments=weibores['comments']
                else:
                    comments=[]
                if len(comments)>0:
                    last_one_comment=comments[0]
                    dbc.execute("replace into weibo_commentlast(weibo_id,last_comment_id,checktime) values(?,?,?)",(weibo_id,last_one_comment['id'],now))
                else:
                    print 'not comment'
                    dbc.execute("update weibo_commentlast set checktime=? where weibo_id=?",(now,weibo_id))
                for onec in comments:
                    print onec['text']
                    user=onec['user']
                    reply_comment_id=0
                    if 'reply_comment' in onec:
                        reply_comment_id=onec['reply_comment']['id']
                    text=STTrans.getInstanse().TransT2S(onec['text'])
                    dbc.execute("replace into weibo_comment(weibo_id,comment_weibo_id,uid,reply_id,word) values(?,?,?,?,?)",(onec['id'],weibo_id,user['id'],reply_comment_id,text))
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
        db.execute("create table weibo_commentlast(weibo_id int not null PRIMARY KEY,last_comment_id int not null,CreatedTime TimeStamp NOT NULL DEFAULT CURRENT_TIMESTAMP,checktime int default 0)")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_lastweibo(user_id int not null PRIMARY KEY,last_weibo_id int not null,CreatedTime TimeStamp NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_text(weibo_id int not null PRIMARY KEY,uid int not null,word varchar(1024) not null)")
    except Exception,e:
        print e
    try:
        db.execute("create table weibo_comment(weibo_id int not null PRIMARY KEY,uid int not null,comment_weibo_id int not null references weibo_text(weibo_id) on update cascade,reply_id int,word varchar(1024) not null)")
    except Exception,e:
        print e
    try:
        db.execute("create view all_weibo as select weibo_id,uid,comment_weibo_id as reply_id,word from weibo_comment where reply_id=0 union select weibo_id,uid,reply_id,word from weibo_comment where reply_id!=0 union select weibo_id,uid,0 as reply_id,word from weibo_text")
    except Exception,e:
        print e
    db.commit()
    db.close()

    while True:
        db=sqlite3.connect("data/weibo_word_base.db")
        client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
        dbc=db.cursor()
        dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and user_name=? and expires_time>?",(APP_KEY,user_name,time.time()+3600))
        dbrow=dbc.fetchone()
        if dbrow!=None:
            client.set_access_token(dbrow[1],dbrow[2])
            my_weibo_id=dbrow[0]
        else:
            oauth=GetWeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
            dbc=db.cursor()
            dbc.execute("replace into weibo_oauth(app_key,user_name,weibo_id,key,expires_time) values(?,?,?,?,?)",(APP_KEY,user_name,oauth['uid'],oauth['access_token'],oauth['expires_in']))
            db.commit()
            client.set_access_token(oauth['access_token'], oauth['expires_in'])
            my_weibo_id=oauth['uid']
        db.close()

        ReadUserWeibo(my_weibo_id,client)

        RecheckComment(client)
        print 'go sleep'
        time.sleep(60*30)
