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

def InitFun(arg):
    return None

def FetchPosInfo(client,pos):
    last_weibo_id=pos['last_weibo_id']
    readtime=time.time()
    total_number=0
    max_id=0
    has_req_error=False
    page=1
    client=QueueClient.WeiboQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'weibo_request',True)
    userslist={}
    weiboslist={}
    while page <= 50:
        try:
            client.AddTask({'function':'place__nearby_timeline','params':{"lat":str(pos['lat']),"long":str(pos['lng']),"range":11000,"count":50,"page":page,"offset":1}})
            headers,body=client.WaitResult()
            place_res=json.loads(body)
            #place_res=client.place__nearby_timeline(lat= pos['lat'],long=pos['lng'],range=11000,count=50,page=page,offset=1)
            print 'read_page',page
            page+=1
        except Exception,e:
            print e,body
            break

        if len(place_res)==0:
            break
        #print json.dumps(place_res)
        if 'statuses' not in place_res:
            print place_res
            break
        statuses=place_res['statuses']
        if len(statuses)==0:
            break

        not_go_next_page=False
        for line in statuses:
            line_info=SplitWeiboInfo(line)
            if line_info==None:
                continue
            data,user=line_info
            max_id=max(max_id,data["weibo_id"])
            if data["weibo_id"]<last_weibo_id:
                not_go_next_page=True
            else:
                total_number+=1
            weiboslist[data['weibo_id']]=data
            userslist[user['id']]=user

            retweeted_status=line.get('retweeted_status')
            if retweeted_status==None:
                continue
            line_info=SplitWeiboInfo(retweeted_status)
            if line_info==None:
                continue
            data,user=line_info
            weiboslist[data['weibo_id']]=data
            userslist[user['id']]=user

        if not_go_next_page:
            break
    print 'id:%d linecount:%d'%(pos['id'],total_number)
    client.Close()
    return (pos,weiboslist.values(),userslist.values(),has_req_error,total_number,readtime,max_id)

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

    work_manage=multithread.WorkManager(3,InitFun)

    def FetchInfoFinish(res,error):
        if error is not None:
            print str(error)
            return
        if res is None:
            return
        pos,weiboslist,userslist,has_req_error,total_number,readtime,max_id=res
        for data in weiboslist:
            con.weibolist.weibo.insert(data)
            con_bk.weibolist.weibo.insert(data)
        for data in userslist:
            con.weibousers.user.insert(data)

        if has_req_error==False:
            if total_number>0:
                pos_db.execute('update GeoWeiboPoint set last_checktime=?,last_checkcount=?,last_checkweiboid=?,last_checkspan=? where id=?',
                    (readtime,total_number,max_id,readtime-pos['last_checktime'],pos['id']))
            else:
                pos_db.execute('update GeoWeiboPoint set last_checktime=?,last_checkcount=?,last_checkspan=? where id=?',
                    (readtime,total_number,readtime-pos['last_checktime'],pos['id']))
            pos_db.commit()

    start_work_time=time.time()
    run_start_time=0
    while True:
        """if time.time()-start_work_time>60*60:
            print 'self kill'
            break"""

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

        for pos in pos_to_record:
            work_manage.add_job(FetchPosInfo,pos,FetchInfoFinish)
        work_manage.wait_allworkcomplete()
    work_manage.wait_allthreadcomplete()
