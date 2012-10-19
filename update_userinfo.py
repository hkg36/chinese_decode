#-*-coding:utf-8-*-
import pymongo
import pymongo.errors
import weibo_tools
import time
import urllib2

if __name__ == '__main__':
    con=pymongo.Connection('mongodb://xcj.server4,xcj.server2/')
    weibo_list=con.weibolist
    weibo_l_u=weibo_list.user

    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://livep.sinaapp.com/mobile/weibo2/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'
    client = weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)

    FullInfoVersion=2
    while True:
        cur=weibo_l_u.find({'$and':[{"is_full_info":{'$lt':FullInfoVersion}}
            ,{"is_full_info":{'$ne':-1}}]},{'id':1}).limit(20)
        users=[]
        for data in cur:
            users.append(data)
        if len(users)==0:
            time.sleep(60*60)
            continue
        for data in users:
            try:
                newdata=client.users__show(uid=data['id'])
                print data['id']
                if 'status' in newdata:
                    del newdata['status']
                tags=client.tags(uid=data['id'],count=200)
                newdata['tags']=tags
                newdata["is_full_info"]=FullInfoVersion
                friend_res=client.friendships__friends__ids(uid=data['id'],count=5000)
                if 'ids' in friend_res:
                    ids=friend_res['ids']
                    newdata['friend_list']=ids
                while True:
                    try:
                        weibo_l_u.update({'_id':data['_id']},{'$set':newdata})
                        break
                    except pymongo.errors.AutoReconnect,e:
                        print 'wait reconnect'
                        time.sleep(5)
                        continue
            except urllib2.HTTPError,e:
                if e.code==400:
                    data['is_full_info']=-1
                    weibo_l_u.update({'_id':data['_id']},{'$set':{'is_full_info':-1}})
                print e,data['id']
            except Exception,e:
                time.sleep(300)