#-*-coding:utf-8-*-
import pymongo
import weibo_tools
import time
import tools
import env_data
import mongo_autoreconnect
import json

if __name__ == '__main__':
    weibo_tools.UseRandomLocalAddress()
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_list=con.weibolist
    weibo_l_u=weibo_list.user

    start_work_time=time.time()
    FullInfoVersion=2
    while True:
        if time.time()-start_work_time>60*60:
            tools.RestartSelf()
        cur=weibo_l_u.find({'$and':[{"is_full_info":{'$lt':FullInfoVersion}}
            ,{"is_full_info":{'$ne':-1}}]},{'id':1,'_id':0}).limit(50)
        client = weibo_tools.DefaultWeiboClient()
        users=[]
        for data in cur:
            users.append(data)
        cur.close()

        if len(users)==0:
            time.sleep(60*60)
            continue
        for data in users:
            try:
                newdata=client.users__show(uid=data['id'])
                print data['id']
                if newdata.has_key('status'):
                    status=newdata.pop('status')
                tags=client.tags(uid=data['id'],count=200)
                newdata['tags']=tags
                newdata["is_full_info"]=FullInfoVersion
                newdata['full_info_time']=time.time()
                friend_res=client.friendships__friends__ids(uid=data['id'],count=5000)
                if 'ids' in friend_res:
                    ids=friend_res['ids']
                    newdata['friend_list']=ids
                weibo_l_u.update({'id':data['id']},{'$set':newdata})
            except weibo_tools.WeiboRequestFail,e:
                if e.httpcode==400:
                    if e.error_data.get('error_code',0)==20003:
                        data['is_full_info']=-1
                        weibo_l_u.update({'id':data['id']},{'$set':{'is_full_info':-1}})
                elif e.httpcode==403:
                    time.sleep(50)
                print e,data['id']
            except Exception,e:
                print e
                time.sleep(1)