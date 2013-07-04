import weibo_tools
import time
import env_data
import pymongo
import read_geo_weibo
import mongo_autoreconnect
import tools

if __name__ == '__main__':
    weibo_tools.UseRandomLocalAddress()
    con_bak=pymongo.Connection(env_data.mongo_connect_str_backup,read_preference=pymongo.ReadPreference.PRIMARY)

    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_l_w=con.weibolist.weibo
    weibo_l_u=con.weibousers.user

    start_work_time=time.time()
    while True:
        client = weibo_tools.DefaultWeiboClient()

        before_time=time.time()-60*60*24
        user_to_check=[]
        cur=weibo_l_u.find({'last_geo_check':{'$exists':False}},{'id':1,'last_geo_check_id':1,'last_geo_check':1}).limit(500)
        for line in cur:
            user_to_check.append(line)
        cur.close()
        if len(user_to_check)==0:
            cur=weibo_l_u.find({'last_geo_check':{'$lt':before_time}},{'id':1,'last_geo_check_id':1,'last_geo_check':1}).sort([('last_geo_check',1)]).limit(50)
            for line in cur:
                user_to_check.append(line)
        cur.close()

        for weibo_user in user_to_check:
            last_geo_check_id=weibo_user.get('last_geo_check_id',0)
            page=1

            max_id=0
            weibo_count=0
            weiboslist={}
            userslist={}
            while True:
                start_check_time=time.time()
                try:
                    w_res=client.place__user_timeline(uid=weibo_user['id'],since_id=last_geo_check_id,count=50,page=page)
                except weibo_tools.WeiboRequestFail,e:
                    if e.httpcode==403:
                        print e
                        break
                    elif e.httpcode==503:
                        continue
                    break
                except weibo_tools.APIError,e:
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

                    retweeted_status=line.get('retweeted_status')
                    if retweeted_status==None:
                        continue
                    line_info=read_geo_weibo.SplitWeiboInfo(retweeted_status)
                    if line_info==None:
                        continue
                    data,user=line_info
                    weiboslist[data['weibo_id']]=data
                    userslist[user['id']]=user

                page+=1
            #if len(weiboslist)>0:
                #weibo_l_w.insert(weiboslist.values())
            weiboslist=weiboslist.values()
            userslist=userslist.values()

            for data in weiboslist:
                weibo_l_w.insert(data)
                con_bak.weibolist.weibo.insert(data)
            for data in userslist:
                weibo_l_u.insert(data)

            if max_id>0:
                weibo_l_u.update({'id':weibo_user['id']},{'$set':{'last_geo_check':start_check_time,'last_geo_check_id':max_id}})
                print '%d read success (%d) from (%d)'%(weibo_user['id'],weibo_count,last_geo_check_id)
            else:
                weibo_l_u.update({'id':weibo_user['id']},{'$set':{'last_geo_check':start_check_time}})
                print '%d fail from (%d)'%(weibo_user['id'],last_geo_check_id)