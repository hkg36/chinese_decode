#-*-coding:utf-8-*-
import sqlite3
import codecs
import json
import decoder

if __name__ == '__main__':
    dbtext=sqlite3.connect("../fetch_hudongbaike/data/sina_news.db")

    dc=dbtext.cursor()
    dc.execute('select content from sina_news where content is not null')

    word_dic={}
    word_dict_root=decoder.LoadDefaultWordDic()
    for content, in dc:
        spliter=decoder.LineSpliter(word_dict_root)
        spliter.SplitLine(content)
        for word in spliter.found_word:
            if word.is_no_cn:
                continue
            word_dic[word.word]=word_dic.get(word.word,0)+1

    fp=codecs.open('data/dictbase/word_freq.txt','w+','utf-8')
    json.dump(word_dic,fp,ensure_ascii=False)
    fp.close()