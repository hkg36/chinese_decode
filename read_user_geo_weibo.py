import weibo_tools
import time
import urllib2
from datetime import datetime
import pymongo
import weibo_api
import re
import random
if __name__ == '__main__':
    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://livep.sinaapp.com/mobile/weibo2/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'

    con=pymongo.Connection('mongodb://xcj.server4,xcj.server2/')
    weibo_list=con.weibolist
    weibo_l_w=weibo_list.weibo
    weibo_l_u=weibo_list.user

    while True:
        client = weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)

        before_time=time.time()-60*60*24
        cur=weibo_l_u.find({'$or':[{'last_geo_check':None},{'last_geo_check':{'$lt':before_time}}]}).sort([('last_geo_check',1)]).limit(50)
        for weibo_user in cur:
            last_geo_check_id=0
            if 'last_geo_check_id' in weibo_user:
                last_geo_check_id=weibo_user['last_geo_check_id']
            page=1

            max_id=0
            weiboslist={}
            while True:
                start_check_time=time.time()
                try:
                    w_res=client.place__user_timeline(uid=weibo_user['id'],since_id=last_geo_check_id,count=50,page=page)
                except urllib2.HTTPError,e:
                    print e
                    if e.code==403:
                        print e
                        time.sleep(5)
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
                if 'statuses' not in w_res:
                    break
                statuses=w_res['statuses']
                if len(statuses)==0:
                    break
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
                    source=line.get('source')
                    if source:
                        source=re.sub(r'</?\w+[^>]*>','',source)
                    created_at=line['created_at']
                    #Tue Dec 07 21:18:14 +0800 2010
                    c_time=datetime.strptime(created_at,"%a %b %d %H:%M:%S +0800 %Y")
                    u_time=time.mktime(c_time.timetuple())
                    u_time-=8*3600
                    data={"weibo_id":int(id),"uid":int(uid),"pos":{"lat":float(lat),"lng":float(lng)},"time":int(u_time),"word":text}
                    if 'thumbnail_pic' in line:
                        data["thumbnail_pic"]=line['thumbnail_pic']
                    if "bmiddle_pic" in line:
                        data["bmiddle_pic"]=line['bmiddle_pic']
                    if "original_pic" in line:
                        data["original_pic"]=line['original_pic']
                    if source:
                        data['source']=source
                    #weibo_l_w.update({"weibo_id":int(id)},data,upsert=True)
                    weiboslist[data['weibo_id']]=data
                page+=1
            if len(weiboslist)>0:
                weibo_l_w.insert(weiboslist.values())
            if max_id>0:
                weibo_l_u.update({'id':weibo_user['id']},{'$set':{'last_geo_check':start_check_time,'last_geo_check_id':max_id}})
                print '%d read success (%d) from (%d)'%(weibo_user['id'],len(weiboslist),last_geo_check_id)
            else:
                weibo_l_u.update({'id':weibo_user['id']},{'$set':{'last_geo_check':start_check_time}})
                print weibo_user['id'],'read fail'