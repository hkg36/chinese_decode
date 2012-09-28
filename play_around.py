#-*-coding:utf-8-*-
import bsddb3
import os
import pickle
import scipy
import scipy.linalg
import decoder
import weibo_bot
import sqlite3

if __name__ == '__main__':
    word_dict_root=decoder.LoadDefaultWordDic()

    db=sqlite3.connect("data/dbforsearch.db")
    dbc=db.cursor()

    word=u"回复@刘君鹏丶:[偷笑][偷笑]等你比我成熟点再叫我小屁孩.你可不见得比我成熟[做鬼脸]"
    word=weibo_bot.RemoveWeiboRubbish(word)
    word_record=weibo_bot.FindWordCount(word_dict_root,word)

    word2_list={}
    for key in word_record:
        dbc.execute("select word,weibo_id,times from all_word where weibo_id in (select weibo_id from all_word where word=?)",(key,))
        for word,weibo_id,time in dbc:
            if word in word2_list:
                w2_l=word2_list[word]
            else:
                w2_l=[]
                word2_list[word]=w2_l
            w2_l.append((weibo_id,time))
    print len(word2_list)