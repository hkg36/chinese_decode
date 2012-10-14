#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import time
from datetime import datetime
import urllib2
import os
import pymongo
import weibo_api
import random
import math
try:
    import ujson as json
except:
    import json


if __name__ == '__main__':
    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://livep.sinaapp.com/mobile/weibo2/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'

    con=pymongo.Connection('218.241.207.46',27017)
    weibo_list=con.weibolist
    weibo_l_w=weibo_list.weibo
    weibo_l_u=weibo_list.user

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
            elif this_span>60*60:
                go_check=True
            elif last_checkspan==0:
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

        client = weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
        userslist={}
        weiboslist={}
        for pos in pos_to_record:
            last_weibo_id=pos['last_weibo_id']

            readtime=time.time()
            total_number=0
            max_id=0
            has_req_error=False
            page=1
            while page < 11:
                try:
                    place_res=client.place__nearby_timeline(lat= pos['lat'],long=pos['lng'],range=5000,count=50,page=page,offset=1)
                    print 'read_page',page
                    page+=1
                except urllib2.HTTPError,e:
                    print e
                    if e.code==403:
                        has_req_error=True
                    break
                except weibo_api.APIError,e:
                    print e
                    if e.error_code==10022:
                        has_req_error=True
                        break
                    continue
                except Exception,e:
                    print e
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
                    if not 'user' in line:
                        continue
                    user=line['user']
                    geo=line['geo']
                    if geo==None:
                        continue
                    if geo['type']=="Point":
                        lat=geo['coordinates'][0]
                        lng=geo['coordinates'][1]
                    else:
                        continue
                    id=int(line['id'])
                    max_id=max(max_id,id)
                    text=line['text']
                    uid=user['id']
                    created_at=line['created_at']
                    #Tue Dec 07 21:18:14 +0800 2010
                    c_time=datetime.strptime(created_at,"%a %b %d %H:%M:%S +0800 %Y")
                    u_time=time.mktime(c_time.timetuple())
                    u_time-=8*3600
                    if id<last_weibo_id:
                        not_go_next_page=True
                    else:
                        total_number+=1
                    data={"weibo_id":int(id),"uid":int(uid),"pos":{"lat":float(lat),"lng":float(lng)},"time":int(u_time),"word":text}
                    if 'thumbnail_pic' in line:
                        data["thumbnail_pic"]=line['thumbnail_pic']
                    if "bmiddle_pic" in line:
                        data["bmiddle_pic"]=line['bmiddle_pic']
                    if "original_pic" in line:
                        data["original_pic"]=line['original_pic']
                    #weibo_l_w.update({"weibo_id":int(id)},data,upsert=True)
                    weiboslist[data['weibo_id']]=data

                    data=user
                    data['is_full_info']=0
                    data['time']=readtime
                    data['id']=int(data['id'])
                    #weibo_l_u.insert(data)
                    userslist[data['id']]=data
                if not_go_next_page:
                    break
            print 'id:%d linecount:%d'%(pos['id'],total_number)
            if len(weiboslist)>0:
                try:
                    weibo_l_w.insert(weiboslist.values())
                except Exception,e:
                    print 'insert fail',e

            if len(userslist):
                try:
                    weibo_l_u.insert(userslist.values())
                except Exception,e:
                    print 'insert fail',e

            if has_req_error==False:
                if total_number>0:
                    pos_db.execute('update GeoWeiboPoint set last_checktime=?,last_checkcount=?,last_checkweiboid=?,last_checkspan=? where id=?',
                        (readtime,total_number,max_id,readtime-pos['last_checktime'],pos['id']))
                else:
                    pos_db.execute('update GeoWeiboPoint set last_checktime=?,last_checkcount=?,last_checkspan=? where id=?',
                        (readtime,total_number,readtime-pos['last_checktime'],pos['id']))
                pos_db.commit()
            else:
                time.sleep(20)