import time
import env_data
import pymongo
import read_geo_weibo
import mongo_autoreconnect
import tools
import QueueClient
from cStringIO import StringIO
import gzip
import json

Queue_User='spider'
Queue_PassWord='spider'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/spider'

class UserWeiboWork(QueueClient.Task):
    def __init__(self,uid,last_geo_check_id):
        QueueClient.Task.__init__(self)
        self.uid=uid
        self.last_geo_check_id=last_geo_check_id
        self.page_num=1
        self.max_id=0
        self.weibo_count=0
        self.weiboslist={}
        self.userslist={}
        self.start_check_time=time.time()
        self.request_headers={'function':'place__user_timeline','params':{'uid':str(self.uid),'since_id':str(self.last_geo_check_id),'count':50,'page':self.page_num}}
    def StepFinish(self,taskqueueclient):
        print 'read id %d page %d'%(self.uid,self.page_num)
        if self.result_headers.get('zip'):
                buf = StringIO(self.result_body)
                f = gzip.GzipFile(fileobj=buf)
                self.result_body = f.read()
        if self.result_headers.get('error')==1:
                if self.result_headers.get('httpcode',0)==400 and self.result_headers.get('weiboerror',0)==20003:
                    self.start_check_time=time.time()+2000000
                    self.max_id=0
                    self.Finish()
                    print 'user %d NE'%self.uid
                    return
        w_res=json.loads(self.result_body)
        if 'statuses' not in w_res:
            self.Finish()
            return
        statuses=w_res['statuses']
        if len(statuses)==0:
            self.Finish()
            return
        for line in statuses:
            line_info=read_geo_weibo.SplitWeiboInfo(line)
            if line_info==None:
                continue
            data,user=line_info
            self.max_id=max(self.max_id,data["weibo_id"])
            self.weibo_count+=1

            self.weiboslist[data['weibo_id']]=data

            retweeted_status=line.get('retweeted_status')
            if retweeted_status==None:
                continue
            line_info=read_geo_weibo.SplitWeiboInfo(retweeted_status)
            if line_info==None:
                continue
            data,user=line_info
            self.weiboslist[data['weibo_id']]=data
            self.userslist[user['id']]=user
        if len(statuses)<50:
            self.Finish()
            return
        self.page_num+=1
        self.request_headers={'function':'place__user_timeline','params':{'uid':str(self.uid),'since_id':str(self.last_geo_check_id),'count':50,'page':self.page_num}}
        taskqueueclient.AddTask(self)
    def Finish(self):
        weiboslist=self.weiboslist.values()
        userslist=self.userslist.values()

        for data in weiboslist:
            weibo_l_w.insert(data)
        for data in userslist:
            weibo_l_u.insert(data)

        if self.max_id>0:
            weibo_l_u.update({'id':self.uid},{'$set':{'last_geo_check':self.start_check_time,'last_geo_check_id':self.max_id}})
            print '%d read success (%d) from (%d)'%(self.uid,self.weibo_count,self.last_geo_check_id)
        else:
            weibo_l_u.update({'id':self.uid},{'$set':{'last_geo_check':self.start_check_time}})
            print '%d fail from (%d)'%(self.uid,self.last_geo_check_id)
if __name__ == '__main__':
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_l_w=con.weibolist.weibo
    weibo_l_u=con.weibousers.user

    start_work_time=time.time()
    while True:
        before_time=time.time()-60*60*24
        user_to_check=[]
        cur=weibo_l_u.find({'last_geo_check':{'$exists':False}},{'id':1,'last_geo_check_id':1,'last_geo_check':1}).limit(50)
        for line in cur:
            user_to_check.append(line)
        cur.close()
        if len(user_to_check)==0:
            cur=weibo_l_u.find({'last_geo_check':{'$lt':before_time}},{'id':1,'last_geo_check_id':1,'last_geo_check':1}).sort([('last_geo_check',1)]).limit(50)
            for line in cur:
                user_to_check.append(line)
        cur.close()

        try:
            taskqueue=QueueClient.TaskQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,
                                                  'weibo_request',True)
            for weibo_user in user_to_check:
                task=UserWeiboWork(weibo_user['id'],weibo_user.get('last_geo_check_id',0))
                taskqueue.AddTask(task)
            taskqueue.WaitResult()
            taskqueue.Close()
        except Exception,e:
            print e