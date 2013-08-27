#-*-coding:utf-8-*-
import QueueClient
import sqlite3
import time
from datetime import datetime
import urllib2
import os
import pymongo
import re
import tools
import env_data
import mongo_autoreconnect
import codecs
import multithread
import json
from cStringIO import StringIO
import gzip

def SplitWeiboInfo(line):
    if not 'user' in line:
        return None
    user=line['user']
    geo=line.get('geo')
    if geo==None:
        return None
    if geo['type']=="Point":
        lat=geo['coordinates'][0]
        lng=geo['coordinates'][1]
    else:
        return None

    text=line['text']
    uid=user['id']
    source=line.get('source')
    if source:
        source=re.sub(r'</?\w+[^>]*>','',source)
    created_at=line['created_at']
    #Tue Dec 07 21:18:14 +0800 2010
    c_time=datetime.strptime(created_at,"%a %b %d %H:%M:%S +0800 %Y")
    u_time=time.mktime(c_time.timetuple())
    u_time-=8*3600
    data={"weibo_id":int(line['id']),"uid":int(uid),"pos":{"lat":float(lat),"lng":float(lng)},"time":int(u_time),"word":text}
    if 'thumbnail_pic' in line:
        data["thumbnail_pic"]=line['thumbnail_pic']
    if "bmiddle_pic" in line:
        data["bmiddle_pic"]=line['bmiddle_pic']
    if "original_pic" in line:
        data["original_pic"]=line['original_pic']
    if source:
        data['source']=source
        #con.weibolist.weibo.update({"weibo_id":data['weibo_id'],data,upsert=True)
    #weiboslist[data['weibo_id']]=data
    data['rec_time']=time.time()

    user['is_full_info']=0
    user['time']=time.time()
    user['id']=int(user['id'])
    #con.weibolist.user.insert(data)
    #userslist[data['id']]=data
    return (data,user)

Queue_User='spider'
Queue_PassWord='spider'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/spider'

class ReadGeoTask(QueueClient.Task):
    def StartPrepare(self,taskinfo):
        self.taskinfo=taskinfo
        self.last_weibo_id=self.taskinfo['last_weibo_id']
        self.readtime=time.time()
        self.total_number=0
        self.max_id=0
        self.page=1
        self.userslist={}
        self.weiboslist={}
        self.PrepareFunction('place__nearby_timeline',lat=self.taskinfo['lat'],long=self.taskinfo['lng'],range=11000,count=50,page=self.page,offset=1)
    def PrepareFunction(self,function,**params):
        atl_params={}
        for key in params:
            atl_params[key]=str(params[key])
        self.request_headers={'function':function,'params':atl_params}
        self.request_body=''
    def StepFinish(self,taskqueueclient):
        if self.result_headers.get('zip'):
                buf = StringIO(self.result_body)
                f = gzip.GzipFile(fileobj=buf)
                self.result_body = f.read()
        place_res=json.loads(self.result_body)
        if len(place_res)==0:
            self.Finish()
            return
        #print json.dumps(place_res)
        if 'statuses' not in place_res:
            print place_res
            self.Finish()
            return
        statuses=place_res['statuses']
        if len(statuses)==0:
            self.Finish()
            return
        print "%d read page %d"%(self.taskinfo['id'],self.page)
        not_go_next_page=False
        for line in statuses:
            line_info=SplitWeiboInfo(line)
            if line_info==None:
                continue
            data,user=line_info
            self.max_id=max(self.max_id,data["weibo_id"])
            if data["weibo_id"]<self.last_weibo_id:
                not_go_next_page=True
            else:
                self.total_number+=1
            self.weiboslist[data['weibo_id']]=data
            self.userslist[user['id']]=user

            retweeted_status=line.get('retweeted_status')
            if retweeted_status==None:
                continue
            line_info=SplitWeiboInfo(retweeted_status)
            if line_info==None:
                continue
            data,user=line_info
            self.weiboslist[data['weibo_id']]=data
            self.userslist[user['id']]=user

        if not_go_next_page or self.page==20:
            self.Finish()
        else:
            self.page+=1
            self.PrepareFunction('place__nearby_timeline',lat=self.taskinfo['lat'],long=self.taskinfo['lng'],range=11000,count=50,page=self.page,offset=1)
            taskqueueclient.AddTask(self)
    def Finish(self):
        print 'id:%d linecount:%d'%(self.taskinfo['id'],self.total_number)
        for data in self.weiboslist.values():
            con.weibolist.weibo.insert(data)
            con_bk.weibolist.weibo.insert(data)
        for data in self.userslist.values():
            con.weibousers.user.insert(data)

        if self.total_number>0:
            pos_db.execute('update GeoWeiboPoint set last_checktime=?,last_checkcount=?,last_checkweiboid=?,last_checkspan=? where id=?',
                (self.readtime,self.total_number,self.max_id,self.readtime-self.taskinfo['last_checktime'],self.taskinfo['id']))
        else:
            pos_db.execute('update GeoWeiboPoint set last_checktime=?,last_checkcount=?,last_checkspan=? where id=?',
                (self.readtime,self.total_number,self.readtime-self.taskinfo['last_checktime'],self.taskinfo['id']))
        pos_db.commit()
if __name__ == '__main__':
    #ss=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(1348447055)))
    if not os.path.exists("GeoData"):
        os.mkdir("GeoData")
    db=sqlite3.connect("GeoData/GeoPointList.db")
    try:
        db.execute("alter table GeoWeiboPoint add column last_checkcount int default 50");
    except Exception,e:
        print e
    try:
        db.execute("alter table GeoWeiboPoint add column last_checkweiboid bigint default 0");
    except Exception,e:
        print e
    try:
        db.execute("alter table GeoWeiboPoint add column last_checktime int default 0");
    except Exception,e:
        print e
    try:
        db.execute("alter table GeoWeiboPoint add column last_checkspan int default 0");
    except Exception,e:
        print e
    db.commit()
    db.close()

    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    con_bk=pymongo.Connection(env_data.mongo_connect_str_backup)

    start_work_time=time.time()
    run_start_time=0
    while True:
        run_start_time=time.time()
        pos_db=sqlite3.connect("GeoData/GeoPointList.db")
        pos_to_record=[]
        pos_cursor=pos_db.cursor()
        pos_cursor.execute('select id,lat,lng,last_checktime,last_checkcount,last_checkweiboid,last_checkspan from GeoWeiboPoint')
        for id,lat,lng,last_checktime,last_checkcount,last_checkweiboid,last_checkspan in pos_cursor:
            this_span=run_start_time-last_checktime
            go_check=False
            if last_checkcount==0:
                if this_span>30*60:
                    go_check=True
            elif this_span>6*60*60:
                go_check=True
            elif last_checkspan==0:
                go_check=True
            elif last_checkspan>6*60*60:
                go_check=True
            else:
                this_may_read=float(last_checkcount)/last_checkspan*this_span
                if this_may_read>300:
                    go_check=True
            if go_check:
                pos_to_record.append({'id':id,'lat':lat,'lng':lng,'last_weibo_id':last_checkweiboid,'last_checktime':last_checktime})
        pos_cursor.close()

        if len(pos_to_record)==0:
            print 'sleep for not thing to update'
            time.sleep(20)
            continue

        try:
            taskqueue=QueueClient.TaskQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'weibo_request',True)
            PAGE_ONE_COUNT=3
            for i in range(0,len(pos_to_record),PAGE_ONE_COUNT):
                b=pos_to_record[i:i+PAGE_ONE_COUNT]
                for pos_t in b:
                    task=ReadGeoTask()
                    task.StartPrepare(pos_t)
                    taskqueue.AddTask(task)
                taskqueue.WaitResult()
            taskqueue.Close()
        except Exception,e:
            print e
