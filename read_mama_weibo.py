#-*-coding:utf-8-*-
import QueueClient
import json
import sqlite3
import time

Queue_User='spider'
Queue_PassWord='spider'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/spider'

database_path='/app_data/chinese_decode/mama_weibolist.sqlite'
if __name__ == '__main__':
    db=sqlite3.connect(database_path)
    db.execute('create table if not exists mama_list(uid int not null PRIMARY KEY,checktime int default 0,last_weibo_id int default 0)')
    db.execute("create table if not exists weibo_text(weibo_id int not null PRIMARY KEY,uid int not null,word varchar(1024) not null)")

    client=QueueClient.WeiboQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'weibo_request',True)
    def UpdateMamaList(client,db):
        client.AddTask({'function':'friendships__friends__ids','params':{'uid':'3699257447','count':5000}})
        headers,body=client.WaitResult()
        body=json.loads(body)
        ids=body.get('ids')
        if ids:
            for id in ids:
                db.execute('insert or ignore into mama_list(uid) values(?)',(id,))
        db.commit()
    UpdateMamaList(client,db)

    def ReadOneUserWeibo(uid,client,db,since_id=0):
        max_weibo_id=0
        for page in xrange(1,20):
            client.AddTask({'function':"statuses__user_timeline",'params':{'uid':str(uid),'since_id':str(since_id),'count':100,'page':page,'trim_user':1}})
            headers,body=client.WaitResult()
            body=json.loads(body)
            statuses=body.get('statuses')
            if statuses:
                for one in statuses:
                    max_weibo_id=max(one['id'],max_weibo_id)
                    db.execute('insert or ignore into weibo_text(weibo_id,uid,word) values(?,?,?)',(one['id'],uid,one['text']))
                    ret_one=one.get('retweeted_status')
                    if ret_one and ret_one.has_key('uid'):
                        db.execute('insert or ignore into weibo_text(weibo_id,uid,word) values(?,?,?)',(ret_one['id'],ret_one['uid'],ret_one['text']))
            else:
                break
        db.execute('update mama_list set checktime=?,last_weibo_id=? where uid=?',(time.time(),max_weibo_id,uid))
        db.commit()
        print '%d finish'%(uid,)
    dbc=db.cursor()
    dbc.execute('select uid,last_weibo_id from mama_list where checktime<?',(time.time()-24*60*60,))
    all_line=dbc.fetchall()
    for uid,last_weibo_id in all_line:
        ReadOneUserWeibo(uid,client,db,last_weibo_id)
    db.close()