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

class UpdateUserWork(QueueClient.Task):
    def __init__(self,uid):
        QueueClient.Task.__init__(self)
        self.uid=uid
        self.request_headers={'function':'users__show','params':{"uid":str(self.uid)}}
        self.step=0
        self.result=None
    def StepFinish(self,taskqueueclient):
        if self.result_headers.get('zip'):
                buf = StringIO(self.result_body)
                f = gzip.GzipFile(fileobj=buf)
                self.result_body = f.read()
        print '---------uid %d step %d'%(self.uid,self.step)
        if self.step==0:
            if self.result_headers.get('error')==1:
                if self.result_headers.get('httpcode',0)==400 and self.result_headers.get('weiboerror',0)==20003:
                    self.result={'is_full_info':-1}
                    self.AllFinish()
                    return
            self.result=json.loads(self.result_body)
            if self.result.has_key('status'):
                status=self.result.pop('status')
            self.request_headers={'function':'tags','params':{'uid':str(self.uid),'count':200}}
            taskqueueclient.AddTask(self)
        elif self.step==1:
            tags=json.loads(self.result_body)
            self.result['tags']=tags
            self.result["is_full_info"]=FullInfoVersion
            self.result['full_info_time']=time.time()
            self.request_headers={'function':'friendships__friends__ids','params':{'uid':str(self.uid),'count':5000}}
            taskqueueclient.AddTask(self)
        elif self.step==2:
            friend_res=json.loads(self.result_body)
            if 'ids' in friend_res:
                ids=friend_res['ids']
                self.result['friend_list']=ids
            self.AllFinish()
        self.step+=1
    def AllFinish(self):
        if self.result['is_full_info']==-1:
            print self.uid,'NE'
            weibo_l_u.update({'id':self.uid},{'$set':{'is_full_info':-1}})
        else:
            print self.uid
            weibo_l_u.update({'id':self.uid},self.result)
if __name__ == '__main__':
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_l_u=con.weibousers.user

    #workpool=multithread.WorkManager(4,thread_init_fun=ThreadInit)
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
        try:
            taskqueue=QueueClient.TaskQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'weibo_request',True)
            for data in users:
                task=UpdateUserWork(data['id'])
                taskqueue.AddTask(task)
            taskqueue.WaitResult()
            taskqueue.Close()
        except Exception,e:
            print e
    """     for data in users:
            workpool.add_job(ProcWork,data,ProcResult)
        workpool.wait_allworkcomplete()
    workpool.wait_allthreadcomplete()"""
