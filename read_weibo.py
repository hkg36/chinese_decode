#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import time
import traceback
from STTrans import STTrans
import mongo_autoreconnect
import QueueClient
import json

word_base_db_file="/app_data/chinese_decode/weibo_word_base.db"
def RepairDb(client,db):
    try:
        client.AddTask({'function':'friendships__friends__ids','params':
                {'uid':str(client.user_id)}})
        headers,body=client.WaitResult()
        res=json.loads(body)

        ids=res.get('ids')
        db.execute('create table if not exists follow_ids(user_id int not null PRIMARY KEY)')
        db.execute('delete from follow_ids')
        dbc=db.cursor()
        for id in ids:
            dbc.execute('replace into follow_ids(user_id) values(?)',(id,))
        db.commit()
        dbc.close()
        db.execute('delete from weibo_text where uid not in(select user_id from follow_ids)')
    except Exception,e:
        print e
fetch_time=0
def ReadUserWeibo(client):
    global fetch_time

    db=sqlite3.connect(word_base_db_file)
    dbc=db.cursor()
    dbc.execute("select last_weibo_id from weibo_lastweibo where user_id=?",(client.user_id,))
    dbrow=dbc.fetchone()
    since_id=0
    if dbrow!=None:
        since_id=dbrow[0]
    if fetch_time%200==0:
        RepairDb(client,db)
        since_id=0

    all_time_line_statuses=[]
    try:
        for page in xrange(1,10):
            client.AddTask({'function':'statuses__home_timeline','params':
                {'page':page,'since_id':str(since_id),'count':200,'filter_by_author':1,'trim_user':1}})
            headers,body=client.WaitResult()
            public_time_line=json.loads(body)
            if public_time_line.has_key('statuses'):
                statuses=public_time_line['statuses']
                if len(statuses)>0:
                    all_time_line_statuses.extend(statuses)
                else:
                    break
            else:
                break
    except Exception,e:
        print traceback.format_exc()
        return

    if len(all_time_line_statuses)>0:
        last_one = all_time_line_statuses[0]
        dbc=db.cursor()
        dbc.execute("replace into weibo_lastweibo(user_id,last_weibo_id) values(?,?)",(client.user_id,last_one['id']))
        db.commit()

    dbc=db.cursor()
    count=0
    for one in all_time_line_statuses:
        if 'uid' not in one or one['uid']==client.user_id:
            continue
        count+=1
        text=STTrans.getInstanse().TransT2S(one['text'])
        dbc.execute("insert or ignore into weibo_text(weibo_id,uid,word) values(?,?,?)",(one['id'],one['uid'],text))
        dbc.execute("insert or ignore into weibo_commentlast(weibo_id,last_comment_id) values(?,?)",(one['id'],0))

    db.commit()
    db.close()

    print 'read new weibo :%d'%len(all_time_line_statuses)

    fetch_time+=1
def CheckComment(client,dbc,weibo_id,last_comment_id=0):
    now=time.time()
    count=0
    total_number=0
    for page in xrange(1,100):
        client.AddTask({'function':'comments__show','params':
                {'id':str(weibo_id),'since_id':str(last_comment_id),'count':200,'trim_user':1,'page':page}})
        headers,body=client.WaitResult()
        weibores=json.loads(body)
        comments=weibores.get('comments')
        total_number=weibores.get('total_number',0)
        if comments is None or len(comments)==0:
            dbc.execute("update weibo_commentlast set checktime=? where weibo_id=?",(now,weibo_id))
            print "%d comments for weibo %d"%(count,weibo_id)
            return

        last_one_comment=comments[0]
        dbc.execute("replace into weibo_commentlast(weibo_id,last_comment_id,checktime) values(?,?,?)",(weibo_id,last_one_comment['id'],now))

        for onec in comments:
            reply_comment_id=0
            if 'reply_comment' in onec:
                reply_comment_id=onec['reply_comment']['id']
            text=STTrans.getInstanse().TransT2S(onec['text'])
            dbc.execute("replace into weibo_comment(weibo_id,comment_weibo_id,uid,reply_id,word) values(?,?,?,?,?)",(onec['id'],weibo_id,onec['uid'],reply_comment_id,text))
        count+=len(comments)

        if count>=total_number:
            dbc.execute("update weibo_commentlast set checktime=? where weibo_id=?",(now,weibo_id))
            print "%d comments for weibo %d (page end)"%(count,weibo_id)
            return

def RecheckComment(client):
    befor_time=time.time()-60*60*24*5
    timestr=time.strftime("%Y-%m-%d %X",time.gmtime(time.time()))

    db=sqlite3.connect(word_base_db_file)
    dbc=db.cursor()
    dbc.execute("select weibo_id,last_comment_id,checktime from weibo_commentlast where checktime=0 and CreatedTime<? limit 500",(timestr,))

    all_line=dbc.fetchall()
    for resrow in all_line:
        weibo_id=resrow[0]
        last_comment_id=resrow[1]
        try:
            CheckComment(client,dbc,weibo_id,last_comment_id)
        except Exception,e:
            print traceback.format_exc()
            db.commit()
            return
    db.commit()

if __name__ == '__main__':
    Queue_User='spider'
    Queue_PassWord='spider'
    Queue_Server='127.0.0.1'
    Queue_Port=None
    Queue_Path='/spider'

    db=sqlite3.connect(word_base_db_file)
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
        APP_KEY = '2824743419'
        APP_SECRET = '9c152c876ec980df305d54196539773f'
        CALLBACK_URL = 'http://1.livep.sinaapp.com/api/weibo_manager_impl/sina_weibo/callback.php'
        user_name = '990631337@qq.com'
        user_psw = 'mnbvcxz'


        try:
            w_client=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
            client=QueueClient.WeiboQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,
                                                'weibo_request',True)
            client.SetWeiboConfig(APP_KEY,APP_SECRET,w_client.access_token)

            client.AddTask({'function':'account__get_uid'})
            header,body=client.WaitResult()
            body=json.loads(body)
            uid=body['uid']
            client.user_id=uid
            """client.AddTask({'function':'users__show','params':
                {'uid':str(uid)}})
            header,body=client.WaitResult()
            body=json.loads(body)
            print body['screen_name']"""

            ReadUserWeibo(client)
            RecheckComment(client)
            client.Close()
        except Exception,e:
            print e
        print 'go sleep'
        print time.strftime("%Y-%m-%d %X",time.gmtime(time.time()))
        time.sleep(60*50)
