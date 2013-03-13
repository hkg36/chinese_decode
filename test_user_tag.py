#-*-coding:utf-8-*-
import weibo_tools
import codecs
import re
import weibo_bot
import decoder
if __name__ == '__main__':
    """
    测试用户的所有微薄，猜测用户的兴趣
    """
    checkwords=[]
    with codecs.open('data/groupcount.txt','r','utf8') as groupf:
        for line in groupf:
            rm=re.match('(?P<word>[^\s]*)\s+(?P<count>\d*)',line)
            if rm:
                word=rm.group('word')
                count=int(rm.group('count'))
                if count<400:
                    break
                elif count<15000:
                    checkwords.append(word)

    client=weibo_tools.DefaultWeiboClient()

    grouptree=decoder.GroupFinder()
    grouptree.BuildTree()
    word_dict_root=decoder.LoadDefaultWordDic()

    #####################init above########################
    textlist={}
    for page in xrange(1,5):
        res=client.statuses__user_timeline(uid=1766737945,count=100,page=page)
        print 'page %d read'%page
        if res:
            status=res.get('statuses')
            if status:
                if len(status)==0:
                    break
                for line in status:
                    id=line['id']
                    text=line['text']
                    textlist[id]=text
                    retw=line.get('retweeted_status')
                    if retw:
                        id=retw['id']
                        text=line['text']
                        textlist[id]=text

    grouptree.StartCountGroup()
    for line in textlist.values():
        line=weibo_bot.RemoveWeiboRubbish(line)
        if len(line)==0:
            continue
        spliter=decoder.LineSpliter(word_dict_root)
        spliter.SplitLine(line)
        spliter.AfterProcess()
        words=spliter.found_word
        grouptree.ProcessOneLine(words)

    itemlist=grouptree.group_count
    groupread=[]
    for wc in checkwords:
        count=itemlist.get(wc)
        if count is not None:
            groupread.append((wc,count))
    groupread.sort(lambda x,y:-cmp(x[1],y[1]))
    resgroup=groupread[0:30]
    for g in resgroup:
        print g[0],g[1]
    pass
