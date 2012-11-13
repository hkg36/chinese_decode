import weibo_tools
import time
import urllib2
import mongo_autoreconnect
import pymongo
import weibo_api
import re
import read_geo_weibo
import objgraph
if __name__ == '__main__':
    con=pymongo.Connection('mongodb://xcj.server4,xcj.server2/')
    weibo_list=con.weibolist
    weibo_l_w=weibo_list.weibo
    weibo_l_u=weibo_list.user

    while True:
        objgraph.show_growth(limit=20)
        print '-------------------------------------------------------------------------'
        client = weibo_tools.DefaultWeiboClient()

        before_time=time.time()-60*60*24
        user_to_check=[]
        cur=weibo_l_u.find({'last_geo_check':{'$exists':False}},{'id':1,'last_geo_check_id':1,'last_geo_check':1}).limit(200)
        for line in cur:
            user_to_check.append(line)
        if len(user_to_check)==0:
            cur=weibo_l_u.find({'last_geo_check':{'$lt':before_time}},{'id':1,'last_geo_check_id':1,'last_geo_check':1}).sort([('last_geo_check',1)]).limit(200)
            for line in cur:
                user_to_check.append(line)

        for weibo_user in user_to_check:
            last_geo_check_id=weibo_user.get('last_geo_check_id',0)
            page=1

            max_id=0
            weibo_count=0
            weiboslist={}
            while True:
                start_check_time=time.time()
                try:
                    w_res=client.place__user_timeline(uid=weibo_user['id'],since_id=last_geo_check_id,count=50,page=page)
                except urllib2.HTTPError,e:
                    print e
                    if e.code==403:
                        #print e
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
                    line_info=read_geo_weibo.SplitWeiboInfo(line)
                    if line_info==None:
                        continue
                    data,user=line_info
                    max_id=max(max_id,data["weibo_id"])
                    weibo_count+=1

                    weiboslist[data['weibo_id']]=data
                page+=1
            #if len(weiboslist)>0:
                #weibo_l_w.insert(weiboslist.values())
            for data in weiboslist.values():
                weibo_l_w.insert(data)
            if max_id>0:
                weibo_l_u.update({'id':weibo_user['id']},{'$set':{'last_geo_check':start_check_time,'last_geo_check_id':max_id}})
                #print '%d read success (%d) from (%d)'%(weibo_user['id'],weibo_count,last_geo_check_id)
            else:
                weibo_l_u.update({'id':weibo_user['id']},{'$set':{'last_geo_check':start_check_time}})
                #print '%d fail from (%d)'%(weibo_user['id'],last_geo_check_id)