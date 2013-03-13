#-*-coding:utf-8-*-
import sqlite3
import decoder
import weibo_bot
import codecs
if __name__ == '__main__':
    grouptree=decoder.GroupFinder()
    grouptree.BuildTree()
    grouptree.StartCountGroup()
    word_dict_root=decoder.LoadDefaultWordDic()

    dbcon=sqlite3.connect('data/public_time_line.sqlite')
    dbc=dbcon.cursor()
    dbc.execute('select txt from pubweibo')
    for txt, in dbc:
        txt=weibo_bot.RemoveWeiboRubbish(txt)
        if len(txt)==0:
            continue
        spliter=decoder.LineSpliter(word_dict_root)
        spliter.SplitLine(txt)
        spliter.AfterProcess()
        words=spliter.found_word
        grouptree.ProcessOneLine(words)
    #grouptree.EndCountGroup()
    itemlist=grouptree.group_count.items()
    itemlist.sort(lambda a,b:-cmp(a[1],b[1]))
    outf=codecs.open('data/groupcount.txt','w','utf8')
    for i in xrange(len(itemlist)):
        print >>outf,itemlist[i][0],itemlist[i][1]
    outf.close()