#-*-coding:utf-8-*-
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
import QueueClient
import json
import uuid

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

Queue_User='spider'
Queue_PassWord='spider'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/spider'

if __name__ == '__main__':
    test_mod=False
    if len(sys.argv)>=2:
        test_mod=sys.argv[1]=='test'
    if test_mod==False:
        queue=redis.Redis(host='xcj.server3',port=6379)
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
    wordgroup_replycount={}
    def lineres(res):
        if res is None:
            return
        for one in res:
            wordgroup_allcount[one]=wordgroup_allcount.get(one,0)+res[one]

    pool=multiprocessing.Pool(processes=2,initializer=proc_init)
    result_queue_name="test_user_tag_result-"+str(uuid.uuid4())
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
        wordgroup_replycount={}

        client=QueueClient.WeiboQueueClient(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'weibo_request',True,result_queue_name)
        textlist={}
        proced_ids=set()
        result_list=[]
        print "page read "
        for page in xrange(1,20):
            try:
                client.AddTask({'function':'statuses__user_timeline','params':{'uid':str(weibo_uid),'count':100,'page':page}})
                header,body=client.WaitResult()
                body=json.loads(body)
            except Exception,e:
                print e
                break

            print 'read page %d'%page
            if body:
                status=body.get('statuses')
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
        client.Close()

        groupread=[]
        for wc in checkwords:
            count=wordgroup_allcount.get(wc)
            if count is not None:
                groupread.append((wc,count))
        groupread.sort(lambda x,y:-cmp(x[1],y[1]))
        resgroup=groupread[0:100]

        print "%d tags"%len(resgroup)

        if test_mod:
            break

        group_name=[one[0] for one in resgroup]
        group_count=[one[1] for one in resgroup]

        mongodb.weibousers.user.update({'id':weibo_uid},{'$set':{'tag_test_time':time.time()}})
        mongodb.user_tag.tag.update({'id':weibo_uid},{'$set':{'t':group_name,'c':group_count}},upsert=True)

    pool.close()
    pool.join()
