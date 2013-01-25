#-*-coding:utf-8-*-
import bsddb3
import os
import pickle
import scipy
import scipy.linalg
import numpy
import decoder
import weibo_bot
import sqlite3
import math

#用词语权重法收集接近的句子
def Step1(word_dict_root,word_record):
    db=sqlite3.connect("data/dbforsearch.db")
    dbc=db.cursor()

    weibo_id_count={}
    for key in word_record:
        word_info=word_dict_root.getwordinfo(key)
        if word_info!=None:
            if 'weight' in word_info:
                d_weight=1e4/word_info['weight']

                dbc.execute("select weibo_id,times from all_word where word=?",(key,))
                for weibo_id,times in dbc:
                    weibo_id_count[weibo_id]=weibo_id_count.get(weibo_id,0)+min(times,3)*d_weight;

    for weibo_id in weibo_id_count.keys():
        dbc.execute("select word_count from all_weibo where weibo_id=?",(weibo_id,))
        word_count,=dbc.next()
        if float(abs(word_count-len(word_record)))/len(word_record)>0.2:
            weibo_id_count.pop(weibo_id)

    word2_list={}
    for id in weibo_id_count:
        dbc.execute("select weibo_id,word,times from all_word where weibo_id=?",(id,))
        for weibo_id,word,time in dbc:
            if word in word2_list:
                w2_l=word2_list[word]
            else:
                w2_l=dict()
                word2_list[word]=w2_l
            w2_l[weibo_id]=time
    dbc.close()
    db.close()
    return word2_list
def FindResponse(word_dict_root,word):
    word=weibo_bot.RemoveWeiboRubbish(word)
    word_record=weibo_bot.FindWordCount(word_dict_root,word)
    word2_list=Step1(word_dict_root,word_record)
    word_index=word2_list.keys()
    weibo_index=set()
    for key in word2_list:
        l2=word2_list[key]
        weibo_index.update(l2.keys())
    if len(weibo_index)>2 and len(word_index)>2:
        weibo_index=list(weibo_index)
        weibo_id_index=dict()
        for i in xrange(0,len(weibo_index)):
            weibo_id_index[weibo_index[i]]=i

        A=numpy.zeros((len(word_index),len(weibo_index)+1))

        for i in xrange(0,len(word_index)):
            word=word_index[i]
            word_info=word_dict_root.getwordinfo(word)
            if word_info!=None:
                if 'weight' in word_info:
                    d_weight=1e4/word_info['weight']
                    ls=word2_list[word]
                    for wb_i in ls:
                        j=weibo_id_index[wb_i]
                        A[i,j]=ls[wb_i]*d_weight
        for word in word_record:
            if word in word_index:
                word_info=word_dict_root.getwordinfo(word)
                if word_info!=None:
                    if 'weight' in word_info:
                        d_weight=1e4/word_info['weight']
                        i=word_index.index(word)
                        A[i,len(weibo_index)]=word_record[word]*d_weight

        A=scipy.matrix(A,copy=False)
        L,a,R=scipy.linalg.svd(A,0)

        weibo_pos=[]
        weibo_x=R[1]
        weibo_y=R[2]

        weibo_pos_last=(weibo_x[len(weibo_index)],weibo_y[len(weibo_index)])
        for i in xrange(0,len(weibo_index)):
            weibo_pos.append((weibo_x[i],weibo_y[i]))

        weibo_dis=[]
        for i in xrange(0,len(weibo_pos)):
            weibo_dis.append((weibo_index[i],math.sqrt( (weibo_pos_last[0]-weibo_pos[i][0])**2+ (weibo_pos_last[1]-weibo_pos[i][1])**2 )))
        weibo_dis.sort(lambda a,b:cmp(a[1],b[1]))

        db=sqlite3.connect("data/dbforsearch.db")
        dbc=db.cursor()
        res_wordlist=[]
        for one in weibo_dis[0:10]:
            dbc.execute("select word from all_weibo where weibo_id=?",(one[0],))
            word,=dbc.next()
            res_wordlist.append(word)
    else:
        db=sqlite3.connect("data/dbforsearch.db")
        dbc=db.cursor()
        res_wordlist=[]
        for one in weibo_index:
            dbc.execute("select word from all_weibo where weibo_id=?",(one,))
            word,=dbc.next()
            res_wordlist.append(word)
    return res_wordlist
if __name__ == '__main__':
    word_dict_root=decoder.LoadDefaultWordDic()

    word=u"今天运动会一跑起来完全没有形象可言了,虽然本来就没有什么形象[泪]反正是最后一次噢耶"
    res=FindResponse(word_dict_root,word)
    for i in res:
        print i