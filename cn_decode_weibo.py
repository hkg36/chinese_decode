#-*-coding:utf-8-*-
from decoder import *
from weibo_autooauth import *
import sqlite3
import string
import time

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

    APP_KEY = '685427335'
    APP_SECRET = '1d735fa8f18fa94d87cd9196867edfb6'
    CALLBACK_URL = 'http://www.hkg36.tk/weibo/authorization'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'

    db=sqlite3.connect("data/weibo_word_base.db")
    try:
        db.execute("create table weibo_oauth(app_key varchar(32),user_name varchar(32),weibo_id int,key varchar(30) not null,expires_time int not null,PRIMARY KEY(app_key,user_name))")
    except Exception,e:
        print e

    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
    dbc=db.cursor()
    dbc.execute("select weibo_id,key from weibo_oauth where app_key=? and user_name=? and expires_time>?",(APP_KEY,user_name,time.time()+3600))
    if dbc.rowcount>=1:
        dbrow=dbc.fetchone()
        client.set_access_token()
    oauth=GetWeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
    expires_time=time.time()+oauth['expires_in']
    dbc=db.cursor()
    dbc.execute("replace into weibo_oauth(app_key,user_name,weibo_id,key,expires_time) values(?,?,?,?,?)",(APP_KEY,user_name,oauth['uid'],oauth['access_token'],expires_time))
    db.commit()

    client.set_access_token(oauth['access_token'], oauth['expires_in'])
    public_time_line=client.statuses__public_timeline()

    statuses=public_time_line['statuses']
    for one in statuses:
        text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]",one['text'])
        text_list=[]
        for tp in text_pice:
            tp=tp.strip()
            if len(tp)>0:
                text_list.append(tp)

        for tp in text_list:
            print tp
            spliter=LineSpliter(word_dict_root)
            words=spliter.ProcessLine(tp)
            for word in words:
                if word_dict_root.word_type.has_key(word.word):
                    types=word_dict_root.word_type[word.word]
                else:
                    types=None
                print u"%s%s %s"%(u"》"*word.pos,word.word,str(types))

    db.close()