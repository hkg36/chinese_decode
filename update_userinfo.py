#-*-coding:utf-8-*-
import pymongo
import weibo_tools
import time
import tools
import env_data

if __name__ == '__main__':
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)
    weibo_list=con.weibolist
    weibo_l_u=weibo_list.user

    start_work_time=time.time()
    FullInfoVersion=2
    while True:
        if time.time()-start_work_time>60*60:
            tools.RestartSelf()
        cur=weibo_l_u.find({'$and':[{"is_full_info":{'$lt':FullInfoVersion}}
            ,{"is_full_info":{'$ne':-1}}]},{'id':1}).limit(50)
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
                status=newdata.pop('status')
                tags=client.tags(uid=data['id'],count=200)
                newdata['tags']=tags
                newdata["is_full_info"]=FullInfoVersion
                friend_res=client.friendships__friends__ids(uid=data['id'],count=5000)
                if 'ids' in friend_res:
                    ids=friend_res['ids']
                    newdata['friend_list']=ids
                weibo_l_u.update({'_id':data['_id']},{'$set':newdata})
            except weibo_tools.WeiboRequestFail,e:
                if e.httpcode==400:
                    data['is_full_info']=-1
                    weibo_l_u.update({'_id':data['_id']},{'$set':{'is_full_info':-1}})
                print e,data['id']
            except Exception,e:
                time.sleep(1)