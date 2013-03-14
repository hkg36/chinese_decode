#-*-coding:utf-8-*-
import weibo_tools
import codecs
import re
import weibo_bot
import decoder
import multiprocessing

word_dict_root=None
grouptree=None
def proc_init():
    global word_dict_root
    global grouptree

    grouptree=decoder.GroupFinder()
    grouptree.BuildTree()
    word_dict_root=decoder.LoadDefaultWordDic()
def lineproc(id,text):
    global word_dict_root
    global grouptree

    grouptree.StartCountGroup()
    line=weibo_bot.RemoveWeiboRubbish(text)
    if len(line)==0:
        return None
    spliter=decoder.LineSpliter(word_dict_root)
    spliter.SplitLine(line)
    spliter.AfterProcess()
    words=spliter.found_word
    grouptree.ProcessOneLine(words)
    return grouptree.group_count

if __name__ == '__main__':
    """
    测试用户的所有微薄，猜测用户的兴趣
    """
    checkwords=[]
    with codecs.open('data/groupcount_proced.txt','r','utf8') as groupf:
        for line in groupf:
            line=line.strip()
            checkwords.append(line)

    client=weibo_tools.DefaultWeiboClient()
    wordgroup_allcount={}
    def lineres(res):
        if res is None:
            return
        for one in res:
            wordgroup_allcount[one]=wordgroup_allcount.get(one,0)+res[one]

    pool=multiprocessing.Pool(initializer=proc_init)
    textlist={}
    proced_ids=set()
    for page in xrange(1,20):
        res=client.statuses__user_timeline(uid=1824785034,count=100,page=page)
        print 'page %d read'%page
        if res:
            status=res.get('statuses')
            if status:
                if len(status)==0:
                    break
                for line in status:
                    id=line['id']
                    text=line['text']
                    if id not in proced_ids:
                        proced_ids.add(id)
                        pool.apply_async(lineproc,(id,text),callback=lineres)
                    retw=line.get('retweeted_status')
                    if retw:
                        id=retw['id']
                        text=line['text']
                        if id not in proced_ids:
                            proced_ids.add(id)
                            pool.apply_async(lineproc,(id,text),callback=lineres)
    pool.close()
    pool.join()

    groupread=[]
    for wc in checkwords:
        count=wordgroup_allcount.get(wc)
        if count is not None:
            groupread.append((wc,count))
    groupread.sort(lambda x,y:-cmp(x[1],y[1]))
    resgroup=groupread[0:30]
    for g in resgroup:
        print g[0],g[1]
    pass
