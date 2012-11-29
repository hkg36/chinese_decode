#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import time
from datetime import datetime
import urllib2
import os
import pymongo
import re
import tools
import env_data
import read_geo_weibo

if __name__ == '__main__':
    topics=['Bistro ivi']

    weiboclient=weibo_tools.DefaultWeiboClient()
    con=pymongo.Connection(env_data.mongo_connect_str,read_preference=pymongo.ReadPreference.PRIMARY)

    for topic in topics:
        userslist={}
        weiboslist={}
        for page in xrange(1,5):
            try:
                res=weiboclient.search__topics(q=topic,count=50,page=page)
            except Exception,e:
                print e
                break
            statues=res.get('statuses')
            if statues==None:
                break
            for line in statues:
                line_info=read_geo_weibo.SplitWeiboInfo(line)
                if line_info==None:
                    continue
                data,user=line_info

                weiboslist[data['weibo_id']]=data
                userslist[user['id']]=user

        print "%s (wc:%d uc:%d)"%(topic,len(weiboslist),len(userslist))

        for data in weiboslist.values():
            con.weibolist.weibo.insert(data)
        for data in userslist.values():
            con.weibolist.user.insert(data)

