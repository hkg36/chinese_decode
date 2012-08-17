#-*-coding:utf-8-*-

import sqlite3
import time
from decoder import *
import random
import urllib2
from weibo_bot import *
import json_connect

try:
    import ujson as json
except :
    import json

if __name__ == '__main__':
    word_dict_root=WordTree()
    fp=open('chinese_data.txt','r') ##网友整理
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    fp=open('word3.txt','r')## 来自国家语言委员会
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    fp=open('SogouLabDic.dic','r') ##来自搜狗互联网数据库
    all_line=fp.readlines()
    fp.close()
    word_dict_root.LoadSogouData(all_line)

    full_text_db=sqlite3.connect("data/fulltext.db")
    db=sqlite3.connect("data/weibo_word_base.db")

    while True:
        try:
            req = urllib2.Request('http://livep.sinaapp.com/dataimport/latestinvitetalk.php')
            response=urllib2.urlopen(req)
            res=json.load(response)

            bot_ids=[599966,600240,600477,600695,601539,\
            601931,602349,602537,603025,603352,\
            587951,603766,603993,604647,588416,\
            604891,588862,588926,589070,590546]


            if res['rescode']==0:
                ret=[]
                reslist=res['list']
                now=time.time()+8*3600
                for oneline in reslist:
                    user_word=oneline['user_word']
                    add_time=time.mktime(time.strptime(oneline['add_time'],"%Y-%m-%d %X"))
                    user_id=oneline['user_id']
                    invite_id=oneline['invite_id']

                    diff=now-add_time
                    if now-add_time<4*60:
                        print 'pass shorttime'
                        continue
                    if user_id in bot_ids:
                        print 'pass bot'
                        continue

                    weibo_reply_list=FindReplyForSentence(word_dict_root,full_text_db,db,user_word)

                    if len(weibo_reply_list)>0:
                        print user_word
                        weibo_reply=weibo_reply_list[random.randint(0,len(weibo_reply_list)-1)]
                        print '>>',weibo_reply

                        uid=bot_ids[random.randint(0,len(bot_ids)-1)]
                        ret.append({'user_id':uid,'invite_id':invite_id,'word':weibo_reply})
                if len(ret)>0:
                    httpres=json_connect.json_request('http://livep.sinaapp.com/dataimport/fakeaddinvitetalk.php',{'talklist':ret})
                    print httpres
        except Exception,e:
            print e
        time.sleep(60*5)