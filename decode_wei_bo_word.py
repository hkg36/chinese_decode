#-*-coding:utf-8-*-
from decoder import *
import sqlite3
try:
    import ujson as json
except :
    import json
import string

def ProcessOneWord(word_dict_root,weibo_id,weibo_word,word_dict):
    weibo_word=re.sub(u"\/*((@[^\s:]*)|(回复@[^\s:]*:))[:\s\/]*","",weibo_word)
    weibo_word=re.sub(u"\w{0,4}://[\w\d./]*","",weibo_word,0,re.I)

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
                #if u'N' in word_type or u'V' in word_type:
                if word.word in word_record:
                    word_record[word.word]=word_record[word.word]+1
                else:
                    word_record[word.word]=1
    for word in word_record:
        if word in word_dict:
            info=word_dict[word]
        else:
            info={}
            word_dict[word]=info

        if weibo_id not in info:
            info[weibo_id]=word_record[word]
        else:
            info[weibo_id]=info[weibo_id]+word_record[word]

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

    db=sqlite3.connect("data/weibo_word_base.db")
    dbc=db.cursor()
    dbc.execute("select weibo_id,word from weibo_text")

    dbtext=sqlite3.connect("data/fulltext.db")
    try:
        dbtext.execute("create table weibo_word(word varchar(32) not null,weibo_id int not null,times int,PRIMARY KEY(word,weibo_id))")
    except Exception,e:
        print e
    try:
        dbtext.execute("create table weibo_comment_word(word varchar(32) not null,weibo_id int not null,times int,PRIMARY KEY(word,weibo_id))")
    except Exception,e:
        print e

    word_dict={}
    for resrow in dbc:
        weibo_word=resrow[1]
        weibo_id=resrow[0]
        ProcessOneWord(word_dict_root,weibo_id,weibo_word,word_dict)

    dbc=dbtext.cursor()
    for word in word_dict:
        add_info=word_dict[word]
        for weibo_id in add_info:
            dbc.execute('replace into weibo_word(word,weibo_id,times) values(?,?,?)',(word,weibo_id,add_info[weibo_id]))
    dbtext.commit()

    #=============================================================
    dbc=db.cursor()
    dbc.execute("select weibo_id,word from weibo_comment where weibo_id in (select reply_id from weibo_comment)")
    word_dict={}
    for resrow in dbc:
        weibo_id=resrow[0]
        weibo_word=resrow[1]
        ProcessOneWord(word_dict_root,weibo_id,weibo_word,word_dict)

    dbc=dbtext.cursor()
    for word in word_dict:
        add_info=word_dict[word]
        for weibo_id in add_info:
            dbc.execute('replace into weibo_comment_word(word,weibo_id,times) values(?,?,?)',(word,weibo_id,add_info[weibo_id]))
    dbtext.commit()


