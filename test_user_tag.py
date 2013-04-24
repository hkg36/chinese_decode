#-*-coding:utf-8-*-
import weibo_tools
import codecs
import weibo_bot
import decoder
import multiprocessing
import pymongo
import redis
import time
import env_data
import mongo_autoreconnect
import tools
import sys

word_dict_root=None
grouptree=None
signwordpos=None
def proc_init():
    global word_dict_root
    global grouptree
    global signwordpos

    grouptree=decoder.GroupFinder()
    grouptree.LoadTree()
    signwordpos=decoder.SignWordPos()
    signwordpos.LoadData()
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
    signwordpos.ProcessSentence(words)
    grouptree.ProcessOneLine(words)
    return grouptree.group_count

if __name__ == '__main__':
    test_mod=False
    if len(sys.argv)>=2:
        test_mod=sys.argv[1]=='test'
    if test_mod==False:
        queue=redis.Redis(host='218.241.207.45',port=6379)
        mongodb=pymongo.Connection(env_data.mongo_connect_str)
    """
    测试用户的所有微薄，猜测用户的兴趣 left is end
    """
    checkwords=[]
    with codecs.open('data/groupcount_proced.txt','r','utf8') as groupf:
        for line in groupf:
            line=line.strip()
            checkwords.append(line)


    wordgroup_allcount={}
    def lineres(res):
        if res is None:
            return
        for one in res:
            wordgroup_allcount[one]=wordgroup_allcount.get(one,0)+res[one]

    pool=multiprocessing.Pool(processes=2,initializer=proc_init)

    for run_time_count in xrange(1000):
        try:
            if test_mod==False:
                weibo_uid=queue.lpop('test_user_tag')
            else:
                weibo_uid=1785153462
        except KeyboardInterrupt,e:
            if pool:
                pool.terminate()
            break
        except Exception,e:
            print e
            weibo_uid=None
        if weibo_uid is None:
            time.sleep(3)
            continue
        try:
            weibo_uid=int(weibo_uid)
        except Exception,e:
            print e
            continue
        print 'start work weibo_id %d'%weibo_uid

        wordgroup_allcount={}

        client=weibo_tools.DefaultWeiboClient()
        textlist={}
        proced_ids=set()
        result_list=[]
        print "page read "
        for page in xrange(1,20):
            for i in xrange(10):
                try:
                    res=client.statuses__user_timeline(uid=weibo_uid,count=100,page=page)
                    break
                except Exception,e:
                    res=None
                    print e
            print '%d,'%page,
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
                            result_list.append(pool.apply_async(lineproc,(id,text),callback=lineres))
                        retw=line.get('retweeted_status')
                        if retw:
                            id=retw['id']
                            text=line['text']
                            if id not in proced_ids:
                                proced_ids.add(id)
                                result_list.append(pool.apply_async(lineproc,(id,text),callback=lineres))
        print ''
        for res1 in result_list:
            res1.wait()

        groupread=[]
        for wc in checkwords:
            count=wordgroup_allcount.get(wc)
            if count is not None:
                groupread.append((wc,count))
        groupread.sort(lambda x,y:-cmp(x[1],y[1]))
        resgroup=groupread[0:30]

        for line in resgroup:
            print "%s=>%d"%(line[0],line[1]),
        print ''

        if test_mod:
            break

        group_name=[one[0] for one in resgroup]
        group_count=[one[1] for one in resgroup]

        mongodb.weibousers.user.update({'id':weibo_uid},{'$set':{'tag_test_time':time.time()}})
        mongodb.user_tag.tag.update({'id':weibo_uid},{'$set':{'t':group_name,'c':group_count}},upsert=True)

    pool.close()
    pool.join()
