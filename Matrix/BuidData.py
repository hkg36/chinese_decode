#-*-coding:utf-8-*-
import sqlite3
import os
import scipy
import scipy.linalg
import scipy.sparse

if __name__ == '__main__':
    db=sqlite3.connect('../data/dbforsearch.db')
    dbc=db.cursor()
    dbc.execute("select count(*) from all_weibo")
    weibo_count,=dbc.next()
    dbc.execute("select count(*) from all_word")
    word_count,=dbc.next()

    dbc.execute(u"select word,weibo_id,times from all_word where weibo_id in (select weibo_id from all_word where word=?)",(u'不要',))
    for word,weibo_id,time in dbc:
        print word,weibo_id,time
    dbc.close()