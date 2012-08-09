#-*-coding:utf-8-*-
from weibo_autooauth import *
import sqlite3
import time
from decoder import *

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

    APP_KEY = '685427335'
    APP_SECRET = '1d735fa8f18fa94d87cd9196867edfb6'
    CALLBACK_URL = 'http://www.hkg36.tk/weibo/authorization'
    user_name = '878260705@qq.com'
    user_psw = 'xianchangjia'

    db=sqlite3.connect("data/weibo_word_base.db")
    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
    dbc=db.cursor()
    dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and user_name=? and expires_time>?",(APP_KEY,user_name,time.time()+3600))
    dbrow=dbc.fetchone()
    if dbrow!=None:
        client.set_access_token(dbrow[1],dbrow[2])
    else:
        oauth=GetWeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
        dbc=db.cursor()
        dbc.execute("replace into weibo_oauth(app_key,user_name,weibo_id,key,expires_time) values(?,?,?,?,?)",(APP_KEY,user_name,oauth['uid'],oauth['access_token'],oauth['expires_in']))
        db.commit()
        client.set_access_token(oauth['access_token'], oauth['expires_in'])
    db.close()

    db=sqlite3.connect("data/weibo_bot.db")
    dbc=db.cursor()
    try:
        dbc.execute("create table last_proc_comment(weibo_id int not null PRIMARY KEY,last_comment int not null)")
    except Exception,e:
        print e
    wres=client.comments__to_me(count=100)
    print json.dumps(wres)
    comments=wres['comments']

    for line in comments:
        weibo_word=line['text']
        if line.has_key('reply_comment'):
            reply_comment=line['reply_comment'];

        weibo_word=re.sub(u"\/*((回复)?@[^\s:]*)[:\s\/]*","",weibo_word)
        weibo_word=re.sub(u"\[[^\]]*\]","",weibo_word)
        if len(weibo_word)==0:
            continue
        if re.search(u"\w{0,5}://[\w\d./]*",weibo_word,re.I):
            continue
        if re.search(u"转发",weibo_word,re.I):
            continue
        print weibo_word
        text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]",weibo_word)
        text_list=[]
        for tp in text_pice:
            tp=tp.strip()
            if len(tp)>0:
                text_list.append(tp)

        word_record={}
        for tp in text_list:
            spliter=LineSpliter(word_dict_root)
            words=spliter.ProcessLine(tp)
            for word in words:
                if word.word in word_dict_root.word_type:
                    word_type=word_dict_root.word_type[word.word]
                    if u'N' in word_type or u'V' in word_type:
                        if word.word in word_record:
                            word_record[word.word]=word_record[word.word]+1
                        else:
                            word_record[word.word]=1

