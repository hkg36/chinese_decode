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

import Tkinter

#用词语权重法收集接近的句子
def Step1(word_record):
    db=sqlite3.connect("data/dbforsearch.db")
    dbc=db.cursor()

    main_weight=0
    for key in word_record:
        word_info=word_dict_root.getwordinfo(key)
        if word_info!=None:
            if 'weight' in word_info:
                main_weight+=1e4/word_info['weight']

    weibo_id_count={}
    for key in word_record:
        word_info=word_dict_root.getwordinfo(key)
        if word_info!=None:
            if 'weight' in word_info:
                d_weight=1e4/word_info['weight']

                dbc.execute("select weibo_id,times from all_word where word=?",(key,))
                for resline in dbc:
                    if resline[0] in weibo_id_count:
                        weibo_id_count[resline[0]]+=resline[1]*d_weight;
                    else:
                        weibo_id_count[resline[0]]=resline[1]*d_weight;

    w_id_count=[]
    for id in weibo_id_count:
        w_id_count.append((id,weibo_id_count[id]))
    w_id_count.sort(lambda a,b:cmp(abs(a[1]-main_weight),abs(b[1]-main_weight)))

    word2_list={}
    for i in xrange(0,min(800,len(w_id_count))):
        dbc.execute("select weibo_id,word,times from all_word where weibo_id=?",(w_id_count[i][0],))
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
if __name__ == '__main__':
    word_dict_root=decoder.LoadDefaultWordDic()

    word=u"今天运动会一跑起来完全没有形象可言了,虽然本来就没有什么形象[泪]反正是最后一次噢耶"
    word=weibo_bot.RemoveWeiboRubbish(word)
    word_record=weibo_bot.FindWordCount(word_dict_root,word)
    word2_list=Step1(word_record)

    word_index=word2_list.keys()
    weibo_index=set()
    for key in word2_list:
        l2=word2_list[key]
        weibo_index.update(l2.keys())
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
    for i in xrange(0,len(weibo_index)):
        weibo_pos.append((weibo_x[i],weibo_y[i]))

    weibo_pos_last=(R[1][len(weibo_index)],R[2][len(weibo_index)])
    weibo_dis=[]
    for i in xrange(0,len(weibo_pos)):
        weibo_dis.append((weibo_index[i],math.sqrt( (weibo_pos_last[0]-weibo_pos[i][0])**2+ (weibo_pos_last[1]-weibo_pos[i][1])**2 )))
    weibo_dis.sort(lambda a,b:cmp(a[1],b[1]))

    db=sqlite3.connect("data/dbforsearch.db")
    dbc=db.cursor()
    for one in weibo_dis:
        dbc.execute("select word from all_weibo where weibo_id=?",(one[0],))
        word,=dbc.next()
        print word
