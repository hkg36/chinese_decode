#-*-coding:utf-8-*-
import QueueClient
import pymongo
import time
import tools
import env_data
import mongo_autoreconnect
import json
import multithread
import gzip
from cStringIO import StringIO

Queue_User='spider'
Queue_PassWord='spider'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/spider'

FullInfoVersion=2

def ThreadInit(args):
    return None
def ProcWork(client,data):
    try:
        client=QueueClient.WeiboQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'weibo_request',True)
        client.AddTask({'function':'users__show','params':{"uid":str(data['id'])}})
        headers,body=client.WaitResult()
        if headers.get('error')==1:
            if headers.get('httpcode',0)==400 and headers.get('weiboerror',0)==20003:
                client.Close()
                return (data['id'],{'is_full_info':-1})
        newdata=json.loads(body)

        if newdata.has_key('status'):
            status=newdata.pop('status')
        client.AddTask({'function':'tags','params':{'uid':str(data['id']),'count':200}})
        headers,body=client.WaitResult()
        tags=json.loads(body)
        newdata['tags']=tags
        newdata["is_full_info"]=FullInfoVersion
        newdata['full_info_time']=time.time()

        client.AddTask({'function':'friendships__friends__ids','params':{'uid':str(data['id']),'count':5000}})
        headers,body=client.WaitResult()
        friend_res=json.loads(body)
        if 'ids' in friend_res:
            ids=friend_res['ids']
            newdata['friend_list']=ids

        client.Close()
        return (data['id'],newdata)
    except Exception,e:
        print e

def ProcResult(result,errorinfo):
    if errorinfo is not None:
        print str(errorinfo)
        return
    if result is None:
        return
    id,newdata=result
    if newdata['is_full_info']==-1:
        print id,'NE'
        weibo_l_u.update({'id':id},{'$set':{'is_full_info':-1}})
    else:
        print id
        weibo_l_u.update({'id':id},newdata)

if __name__ == '__main__':
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_l_u=con.weibousers.user

    workpool=multithread.WorkManager(4,thread_init_fun=ThreadInit)
    start_work_time=time.time()
    while True:
        users=[]
        with weibo_l_u.find({'$and':[{"is_full_info":{'$lt':FullInfoVersion}}
            ,{"is_full_info":{'$ne':-1}}]},{'id':1,'_id':0}).limit(50) as cur:
            for data in cur:
                users.append(data)
        if len(users)==0:
            with weibo_l_u.find({"is_full_info":{'$ne':-1}},{'id':1,'_id':0}).sort({'full_info_time':1}).limit(50) as cur:
                for data in cur:
                    users.append(data)

        if len(users)==0:
            time.sleep(60*60)
            continue

        for data in users:
            workpool.add_job(ProcWork,data,ProcResult)
        workpool.wait_allworkcomplete()
    workpool.wait_allthreadcomplete()
