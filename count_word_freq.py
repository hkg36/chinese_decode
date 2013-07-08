#-*-coding:utf-8-*-
import sqlite3
import codecs
import json
import decoder
import gzip

if __name__ == '__main__':
    """
    使用新浪新闻来测试词频 上一步是 fetch_hudongbaike/fetch_sina_news.py
    """
    dbtext=sqlite3.connect("../fetch_hudongbaike/data/sina_news.db")

    dc=dbtext.cursor()
    dc.execute('select content from sina_news where content is not null')

    word_dic={}
    word_dict_root=decoder.LoadDefaultWordDic()
    for content, in dc:
        spliter=decoder.LineSpliter(word_dict_root)
        spliter.SplitLine(content)
        spliter.CheckCantantPre()
        spliter.CheckTail()
        for word in spliter.found_word:
            if word.is_no_cn:
                continue
            word_dic[word.word]=word_dic.get(word.word,0)+1

    fp=gzip.open('data/dictbase/word_freq.txt.gz','w')
    json.dump(word_dic,fp)
    fp.close()