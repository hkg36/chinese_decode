#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import time
from decoder import *
import random

def FindWordCount(word_dict_root,word):
    """
    分解句子并统计词语出现次数
    """
    text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·.]",word)
    text_list=[]
    for tp in text_pice:
        tp=tp.strip()
        if len(tp)>0:
            text_list.append(tp)

    word_record={}
    for tp in text_list:
        spliter=LineSpliter(word_dict_root)
        words=spliter.ProcessLine(tp)
        for word in words:
            if word.word in word_record:
                word_record[word.word]=word_record[word.word]+1
            else:
                word_record[word.word]=1
    return word_record
def RemoveWeiboRubbish(word):
    word=re.sub(u"(?i)\/*((@[^\s:]*)|(回复@[^\s:]*:))[:\s\/]*","",word)
    word=re.sub(u"(?i)\w{0,4}://[\w\d./]*","",word)
    word=re.sub(u"转发微博","",word)
    word=re.sub(u"\[[^\]]*\]","",word)
    word=word.strip()
    return word
def DoubleAve(l):
    all=0
    for o in l:
        all+=o*o
    return math.sqrt(all/len(l))

def FindReplyForSentence(word_dict_root,word):
    dbsearch=sqlite3.connect('data/dbforsearch.db')
    dbc=dbsearch.cursor()
    word_record=FindWordCount(word_dict_root,word)

    main_weight=0
    for key in word_record:
        word_info=word_dict_root.getwordinfo(key)
        if word_info:
            weight=word_info.get('weight',0)
            main_weight+=weight*word_record[key]

    """if main_weight<100:
        return []"""
    weibo_id_count={}
    for key in word_record:
        dbc.execute("select weibo_id,times from all_word where word=?",(key,))
        word_info=word_dict_root.getwordinfo(key)
        if word_info==None:
            continue
        weight=word_info.get('weight',0 )
        for weibo_id,times in dbc:
            if weibo_id in weibo_id_count:
                weibo_id_count[weibo_id]+=min(2,times)*weight;
            else:
                weibo_id_count[weibo_id]=min(2,times)*weight;

    if len(weibo_id_count)==0:
        return []
    close_weight=1e4
    for one_weight in weibo_id_count.values():
        if abs(close_weight-main_weight)>abs(one_weight-main_weight):
            close_weight=one_weight
    max_weibo_id=[]
    for id in weibo_id_count:
        count=weibo_id_count[id]
        if count==close_weight:
            max_weibo_id.append(id)

    maybe_replyids=[]
    if len(max_weibo_id)>0:
        for weibo_id in max_weibo_id:
            dbc.execute("select weibo_id,word_count from all_weibo where reply_id=?",(weibo_id,))
            for weibo_id2,word_count2 in dbc:
                if word_count2 is None:
                    continue
                maybe_replyids.append((weibo_id2,abs(len(word_record)-word_count2)))
    maybe_replyids.sort(lambda a,b:cmp(a[1],b[1]))
    maybe_replyids=maybe_replyids[0:10]

    dbc.execute('select word,weibo_id,times from all_word where weibo_id in (%s)'%(','.join(map(str,[a[0] for a in maybe_replyids]))))
    asw_wights={}
    for word,weibo_id,times in dbc:
        word_info=word_dict_root.getwordinfo(word)
        if word_info==None:
            continue
        weight=word_info.get('weight',0 )
        if weibo_id in asw_wights:
            asw_wights[weibo_id]+=min(2,times)*weight
        else:
            asw_wights[weibo_id]=min(2,times)*weight
    if len(asw_wights)==0:
        return []
    asw_ave_weight=DoubleAve(asw_wights.values())

    asw_weights=[(key,asw_wights[key]) for key in asw_wights]
    asw_weights.sort(lambda a,b:cmp(abs(asw_ave_weight-a[1]),abs(asw_ave_weight-b[1])))
    asw_weights=asw_weights[0:20]

    weibo_reply_list=[]
    for weibo_id,weight in asw_weights:
        dbc.execute('select word,word_count from all_weibo where weibo_id=?',(weibo_id,))
        for word,word_count in dbc:
            if float(abs(word_count-len(word_record)))/len(word_record)<.8:
                weibo_reply_list.append(RemoveWeiboRubbish(word))
    return weibo_reply_list

if __name__ == '__main__':
    debug_mode=1
    word_dict_root=LoadDefaultWordDic()

    APP_KEY = '2117816058'
    APP_SECRET = '80f6fac494eed2f4e8a54acb85683aea'
    CALLBACK_URL = 'http://www.haomeiniu.com/controller/callback.php'
    user_name = '878260705@qq.com'
    user_psw = 'xianchangjia'

    bot_id_set=set()

    client=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
    dbbot=sqlite3.connect("data/weibo_bot.db")

    dbc=dbbot.cursor()
    try:
        dbc.execute("create table last_proc_comment(user_name varchar(32) not null PRIMARY KEY,last_comment int not null)")
    except Exception,e:
        print e

    comment_since_id=0
    dbc=dbbot.cursor()
    dbc.execute("select last_comment from last_proc_comment where user_name=?",(user_name,))
    resrow=dbc.fetchone()
    if resrow!=None:
        comment_since_id=resrow[0]
    if debug_mode==1:
        comment_since_id=0
    wres=client.comments__to_me(count=80,since_id=comment_since_id)

    if wres.has_key('comments'):
        comments=wres['comments']
        if len(comments)>0:
            last_comment=comments[0]
            if debug_mode==0:
                dbc=dbbot.cursor()
                dbc.execute("replace into last_proc_comment(user_name,last_comment) values(?,?)",(user_name,last_comment['id']))
                dbbot.commit()
    else:
        comments=[]

    for line in comments:
        if line['user']['id'] in bot_id_set:
            continue
        status=line['status'];
        weibo_word=line['text']

        weibo_word=RemoveWeiboRubbish(weibo_word)
        if len(weibo_word)==0:
            continue
        print '------------------------------------------------------------'
        print 'src:',weibo_word
        weibo_reply_list=FindReplyForSentence(word_dict_root,weibo_word)

        if len(weibo_reply_list)>0:
            if debug_mode==0:
                weibo_reply=weibo_reply_list[0]
                weibo_reply=RemoveWeiboRubbish(weibo_reply)
                print 'asw:',weibo_reply
            else:
                for wr in weibo_reply_list:
                    wr=RemoveWeiboRubbish(wr)
                    print 'asw:',wr
            try:
                if debug_mode==0:
                    wbres=client.post.comments__reply(id=status['id'],cid=line['id'],comment=weibo_reply)
            except Exception,e:
                print e