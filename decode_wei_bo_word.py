#-*-coding:utf-8-*-
from decoder import *
import sqlite3
try:
    import ujson as json
except :
    import json
import string
import weibo_bot
import os

def ProcessOneWord(word_dict_root,weibo_id,weibo_word):
    weibo_word=weibo_bot.RemoveWeiboRubbish(weibo_word)

    text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·.]+",weibo_word)
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
            if word.info!=None:
            #if word.info!=None and 'type' in word.info:
                #word_type=word.info['type']
                #if u'N' in word_type or u'V' in word_type:
                word_record[word.word]=word_record.get(word.word,0)+1

    return word_record

if __name__ == '__main__':
    #ignorewords=set((u'嘻嘻',u'哈哈',u'恩',u'嘿嘿',u'为什么',u'哦',u'噗',u'肿么办',u'怎么办'))
    word_dict_root=LoadDefaultWordDic()

    db=sqlite3.connect("data/weibo_word_base.db")

    #dump db
    if os.path.isfile("data/dbforsearch.db"):
        os.remove("data/dbforsearch.db")

    dbforsearch=sqlite3.connect("data/dbforsearch.db")
    try:
        dbforsearch.execute("create table all_word(word varchar(32) not null,weibo_id int not null,times int,PRIMARY KEY(word,weibo_id))")
    except Exception,e:
        print e

    dbc=db.cursor()
    dbtc=dbforsearch.cursor()
    dbc.execute("select weibo_id,word from weibo_text union select weibo_id,word from weibo_comment")
    for weibo_id,weibo_word in dbc:
        word_recorded=ProcessOneWord(word_dict_root,weibo_id,weibo_word)
        for word in word_recorded:
            count=word_recorded[word]
            dbtc.execute('replace into all_word(word,weibo_id,times) values(?,?,?)',(word,weibo_id,count))
    dbforsearch.commit()

    dbforsearch.execute("create table all_weibo(weibo_id int not null PRIMARY KEY,uid int not null,word varchar(1024) not null,reply_id int,word_count int)")
    dbforsearch.execute("ATTACH DATABASE 'data/weibo_word_base.db' as weibo_base")

    sqlstr="""insert into all_weibo(weibo_id,uid,word,reply_id,word_count) select weibo_base.all_weibo.weibo_id,uid,word,reply_id,b.word_count from weibo_base.all_weibo
        left join (select weibo_id,count(*) as word_count from all_word group by weibo_id) b on b.weibo_id=weibo_base.all_weibo.weibo_id"""
    dbforsearch.execute(sqlstr)

    dbforsearch.commit()
    dbforsearch.close()