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

    S=scipy.sparse.dok_matrix((word_count,weibo_count),dtype=scipy.float32)
    dbc.execute("select word_ids.word_id,all_weibo.id,times from all_word left join word_ids on word_ids.word=all_word.word left join all_weibo on all_weibo.weibo_id=all_word.weibo_id")
    for word_id,weibo_id,time in dbc:
        print word_id,weibo_id,time
        S[word_id-1,weibo_id-1]=time
    dbc.close()

    U, s, Vh=scipy.linalg.svd(S,False)