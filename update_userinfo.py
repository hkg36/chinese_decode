#-*-coding:utf-8-*-
import pymongo
import sqlite3
import json
import weibo_tools
import weibo_api
import time

if __name__ == '__main__':
    con=pymongo.Connection('218.241.207.46',27017)
    weibo_list=con.weibolist
    weibo_l_u=weibo_list.user

    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://livep.sinaapp.com/mobile/weibo2/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'
    client = weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)

    while True:
        cur=weibo_l_u.find({"is_full_info":0}).limit(20)
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
                newdata['_id']=data['_id']
                newdata["is_full_info"]=1
                weibo_l_u.save(newdata)
            except Exception,e:
                if e.code==400:
                    data['is_full_info']=-1
                    weibo_l_u.save(data)
                print e,data['id']