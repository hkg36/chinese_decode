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

class UpdateUserWork(QueueClient.Task):
    def __init__(self,data):
        QueueClient.Task.__init__(self)
        self.fulldata=data
        self.uid=data['id']
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
            if self.result_headers.get('error',0)==1:
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
            if self.result_headers.get('error',0)==0:
                tags=json.loads(self.result_body)
                self.result['tags']=tags
            self.request_headers={'function':'friendships__friends__ids','params':{'uid':str(self.uid),'count':5000}}
            taskqueueclient.AddTask(self)
        elif self.step==2:
            if self.result_headers.get('error',0)==0:
                friend_res=json.loads(self.result_body)
                if 'ids' in friend_res:
                    ids=friend_res['ids']
                    self.result['friend_list']=ids
            self.result["is_full_info"]=FullInfoVersion
            self.result['full_info_time']=time.time()
            self.AllFinish()
        self.step+=1
    def AllFinish(self):
        if self.result['is_full_info']==-1:
            print self.uid,'NE'
            weibo_l_u.update({'id':self.uid},{'$set':{'is_full_info':-1}})
        else:
            print self.uid
            self.fulldata.update(self.result)
            weibo_l_u.update({'id':self.uid},self.fulldata)
if __name__ == '__main__':
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_l_u=con.weibousers.user

    taskqueue=QueueClient.TaskQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,
                                                  'weibo_request',True)
    while True:
        users=[]
        with weibo_l_u.find({'$and':[{"is_full_info":{'$lt':FullInfoVersion}}
            ,{"is_full_info":{'$ne':-1}}]},{'_id':0}).limit(50) as cur:
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
            for data in users:
                task=UpdateUserWork(data)
                taskqueue.AddTask(task)
            taskqueue.WaitResult()
        except Exception,e:
            print e
        taskqueue.Close()
