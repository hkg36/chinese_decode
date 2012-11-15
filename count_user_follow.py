#-*-coding:utf-8-*-
import pymongo
import sqlite3
import os
if __name__ == '__main__':

    con=pymongo.Connection('mongodb://xcj.server4/',read_preference=pymongo.ReadPreference.SECONDARY)
    cur=con.weibolist.user.find({'friend_list':{'$exists':True}},{'id':1,'friend_list':1})

    user_follow={}
    for line in cur:
        friend_list=line['friend_list']
        for one in friend_list:
            user_follow[one]=user_follow.get(one,0)+1

    if os.path.isfile("data/dbforsearch.db"):
        os.remove("data/dbforsearch.db")
    sqlcon=sqlite3.connect('data/user_follow.db')
    sqlcon.execute('create table if not exists user_follow_count(weibo_id bigint,count int, PRIMARY KEY(weibo_id))')
    sqlc=sqlcon.cursor()
    for id,count in user_follow.items():
        sqlc.execute('insert into user_follow_count(weibo_id,count) values (?,?)',(id,count))
    sqlcon.commit()
    sqlc.close()
    sqlcon.close()
