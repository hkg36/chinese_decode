#-*-coding:utf-8-*-
import redis
import mongo_autoreconnect
import pymongo
import env_data
import time
if __name__ == '__main__':
    queue=redis.Redis(host='218.241.207.45',port=6379)
    mongodb=pymongo.Connection(env_data.mongo_connect_str)
    """
    分析用户tag普通队列
    """

    added_users=[]
    while True:
        new_user_set=set()
        res=mongodb.weibousers.user.find({'tag_test_time':{"$exists":False}},{'_id':0,'id':1}).limit(200)
        for one in res:
            new_user_set.add(one['id'])
        if len(new_user_set)==0:
            res=mongodb.weibousers.user.find({},{'_id':0,'id':1}).sort([('tag_test_time',1)]).limit(200)
            for one in res:
                new_user_set.add(one['id'])

        for old in added_users:
            new_user_set-=old
        added_users.append(new_user_set)
        if len(added_users)>10:
            added_users.pop(0)
        for one in new_user_set:
            while queue.llen('test_user_tag')>2:
                time.sleep(3)
            queue.rpush('test_user_tag',one)
    pass