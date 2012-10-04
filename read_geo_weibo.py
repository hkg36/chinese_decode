#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import time
from datetime import datetime
import traceback
import sys
import os
from STTrans import STTrans
import pymongo
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
        db.execute("create table GeoWeiboPoint(id INTEGER PRIMARY KEY,lat float,lng float,last_checktime INT default 0)");
    except Exception,e:
        print e
    db.commit()
    db.close()

    run_start_time=0
    while True:
        if time.time()-run_start_time<2*60:
            time.sleep(2*60-(time.time()-run_start_time))
        run_start_time=time.time()

        client = weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)

        pos_db=sqlite3.connect("GeoData/GeoPointList.db")
        pos_to_record=[]
        pos_cursor=pos_db.cursor()
        pos_cursor.execute('select id,lat,lng,last_checktime from GeoWeiboPoint')
        for line in pos_cursor:
            pos_to_record.append({'id':line[0],'lat':line[1],'lng':line[2],'time':line[3]})
        pos_cursor.close()

        for pos in pos_to_record:
            starttime=pos['time']
            readtime=time.time()
            db=sqlite3.connect("GeoData/weibo_word_base.db")
            total_number=0
            max_id=0
            for page in range(1,11):
                try:
                    place_res=client.place__nearby_timeline(lat= pos['lat'],long=pos['lng'],range=5000,count=50,page=page,offset=1)
                except Exception,e:
                    print e
                    break

                if len(place_res)==0:
                    break
                #print json.dumps(place_res)
                total_number=place_res['total_number']
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
                    if id<max_id:
                        not_go_next_page=True
                    data={"weibo_id":int(id),"uid":int(uid),"pos":{"lat":float(lat),"lng":float(lng)},"time":int(u_time),"word":text}
                    if 'thumbnail_pic' in line:
                        data["thumbnail_pic"]=line['thumbnail_pic']
                    if "bmiddle_pic" in line:
                        data["bmiddle_pic"]=line['bmiddle_pic']
                    if "original_pic" in line:
                        data["original_pic"]=line['original_pic']
                    weibo_l_w.update({"weibo_id":int(id)},data,upsert=True)

                    data=user
                    data['is_full_info']=0
                    data['time']=readtime
                    data['id']=int(data['id'])
                    weibo_l_u.insert(data)
                if not_go_next_page:
                    break
            print 'id:%d linecount:%d'%(pos['id'],total_number)

            if max_id!=0:
                pos_db.execute('update GeoWeiboPoint set last_checktime=? where id=?',(max_id,pos['id']))
                pos_db.commit()