#-*-coding:utf-8-*-
import sqlite3
import codecs
import ujson as json

if __name__ == '__main__':
    dbtext=sqlite3.connect("data/fulltext.db")

    dc=dbtext.cursor()
    dc.execute('select word,sum(times) from all_word group by word')

    fp=codecs.open('data/word_freq.txt','w+','utf-8')
    word_dic={}
    for line in dc:
        word_dic[line[0]]=line[1]
    json.dump(word_dic,fp)
    fp.close()