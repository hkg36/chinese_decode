#-*-coding:utf-8-*-
import bsddb3
import os
import pickle
import scipy
import scipy.linalg
"""
s = '-1 2;2 2;4 -2'
A = scipy.mat(s)
U, s, Vh=scipy.linalg.svd(A,True)
print U
print s
print Vh

U, s, Vh=scipy.linalg.svd(A,False)
print U
print s
print Vh"""
import pymongo
import sqlite3
import json

con=pymongo.Connection('218.241.207.46',27017)
weibo_list=con.weibolist
weibo_l_w=weibo_list.weibo
weibo_l_u=weibo_list.user

print weibo_l_w.count()
sql_move=sqlite3.connect('GeoData/weibo_word_base.db')
sc=sql_move.cursor()
sc.execute('select weibo_id,uid,word,lat,lng,time from weibo_text')
for weibo_id,uid,word,lat,lng,time in sc:
    data={"weibo_id":int(weibo_id),"uid":int(uid),"pos":{"lat":float(lat),"lng":float(lng)},"time":int(time),"word":word}
    weibo_l_w.update({"weibo_id":int(weibo_id)},data,upsert=True)

print weibo_l_w.count()
sc.execute('select info,is_full_info,time from weibo_user_info')
for info,is_full_info,time in sc:
    data=json.loads(info)
    data['is_full_info']=int(is_full_info)
    data['time']=int(time)
    data['id']=int(data['id'])
    weibo_l_u.update({'id':data['id']},data,upsert=True)