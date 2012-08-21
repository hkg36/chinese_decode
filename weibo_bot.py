#-*-coding:utf-8-*-
from weibo_autooauth import *
import sqlite3
import time
from decoder import *
import random

try:
    import ujson as json
except :
    import json
def FindWordCount(word_dict_root,word):
    """
    分解句子并统计词语出现次数
    """
    text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]",word)
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
            if word.word in word_dict_root.word_type:
                word_type=word_dict_root.word_type[word.word]
                if word.word in word_record:
                    word_record[word.word]=word_record[word.word]+1
                else:
                    word_record[word.word]=1
    return word_record
def RemoveWeiboRubbish(word):
    word=re.sub(u"\/*((@[^\s:]*)|(回复@[^\s:]*:))[:\s\/]*","",word)
    word=re.sub(u"\w{0,4}://[\w\d./]*","",word,0,re.I)
    return word

def FindReplyForSentence(word_dict_root,dbsearch,word):
    dbc=dbsearch.cursor()
    word_record=FindWordCount(word_dict_root,word)

    main_weight=0
    for key in word_record:
        if key in word_dict_root.word_weight:
            main_weight+=1.0/word_dict_root.word_weight[key]

    weibo_reply_list=[]
    #回帖中的对话
    weibo_id_count={}
    for key in word_record:
        if key in word_dict_root.word_weight:
            weight=1.0/word_dict_root.word_weight[key]
        else:
            continue
        dbc.execute("select weibo_id,times from all_word where word=?",(key,))
        for resline in dbc:
            if resline[0] in weibo_id_count:
                weibo_id_count[resline[0]]+=resline[1]*weight;
            else:
                weibo_id_count[resline[0]]=resline[1]*weight;

    if len(weibo_id_count)>0:
        weibo_id_count_list=[]
        for key in weibo_id_count:
            weibo_id_count_list.append({'k':key,'v':weibo_id_count[key]})
        weibo_id_count_list.sort(lambda a,b:-cmp(a['v'],b['v']))

        max_weight=0
        weibo_id_count_list_maxs=[]
        for one_pair in weibo_id_count_list:
            if max_weight!=0 and max_weight>one_pair['v']:
                break
            max_weight=one_pair['v']
            weibo_id_count_list_maxs.append(one_pair)
        weibo_id_count_list=weibo_id_count_list_maxs

        selected_weibo_weight=[]
        for one_pair in weibo_id_count_list:
            dbc.execute("select word,times from all_word where weibo_id=?",(one_pair['k'],))
            one_weight=0
            for resrow in dbc:
                if resrow[0] in word_dict_root.word_weight:
                    one_weight+=1.0/word_dict_root.word_weight[resrow[0]]
                else:
                    continue
            selected_weibo_weight.append({'id':one_pair['k'],'weight':one_weight})

        selected_weibo_weight.sort(lambda a,b:cmp(abs(a['weight']-main_weight),abs(b['weight']-main_weight)))

        selected_weight=0
        selected_weibo_ids=[]
        for one_pair in selected_weibo_weight:
            if selected_weight!=0 and one_pair['weight']!=selected_weight:
                break
            selected_weibo_ids.append(one_pair['id'])

        for weibo_id in selected_weibo_ids:
            dbc.execute("select word from all_weibo where reply_id=?",(weibo_id,))
            for resrow in dbc:
                weibo_reply_list.append(RemoveWeiboRubbish(resrow[0]))

    return weibo_reply_list

if __name__ == '__main__':
    debug_mode=0
    word_dict_root=WordTree()
    fp=open('chinese_data.txt','r') ##网友整理
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    fp=open('word3.txt','r')## 来自国家语言委员会
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    fp=open('SogouLabDic.dic','r') ##来自搜狗互联网数据库
    all_line=fp.readlines()
    fp.close()
    word_dict_root.LoadSogouData(all_line)

    APP_KEY = '685427335'
    APP_SECRET = '1d735fa8f18fa94d87cd9196867edfb6'
    CALLBACK_URL = 'http://www.hkg36.tk/weibo/authorization'
    user_name = '878260705@qq.com'
    user_psw = 'xianchangjia'

    db=sqlite3.connect("data/weibo_word_base.db")
    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
    dbc=db.cursor()
    dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and user_name=? and expires_time>?",(APP_KEY,user_name,time.time()-3600))
    dbrow=dbc.fetchone()
    if dbrow!=None:
        client.set_access_token(dbrow[1],dbrow[2])
    else:
        oauth=GetWeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
        dbc=db.cursor()
        dbc.execute("replace into weibo_oauth(app_key,user_name,weibo_id,key,expires_time) values(?,?,?,?,?)",(APP_KEY,user_name,oauth['uid'],oauth['access_token'],oauth['expires_in']))
        db.commit()
        client.set_access_token(oauth['access_token'], oauth['expires_in'])
    db.close()

    dbbot=sqlite3.connect("data/weibo_bot.db")
    dbc=dbbot.cursor()
    try:
        dbc.execute("create table last_proc_comment(user_name varchar(32) not null PRIMARY KEY,last_comment int not null)")
    except Exception,e:
        print e

    searchdb=sqlite3.connect("data/dbforsearch.db")

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
        status=line['status'];
        weibo_word=line['text']

        weibo_word=re.sub(u"\/*((回复)?@[^\s:]*)[:\s\/]*","",weibo_word)
        weibo_word=re.sub(u"\[[^\]]*\]","",weibo_word)
        if len(weibo_word)==0:
            continue
        if re.search(u"\w{0,5}://[\w\d./]*",weibo_word,re.I):
            continue
        if re.search(u"转发",weibo_word,re.I):
            continue
        weibo_reply_list=FindReplyForSentence(word_dict_root,searchdb,weibo_word)

        if len(weibo_reply_list)>0:
            print weibo_word
            if debug_mode==0:
                weibo_reply=weibo_reply_list[random.randint(0,len(weibo_reply_list)-1)]
                print '>>',weibo_reply
            else:
                for wr in weibo_reply_list:
                    print '>>',wr
            try:
                if debug_mode==0:
                    wbres=client.post.comments__reply(id=status['id'],cid=line['id'],comment=weibo_reply)
                pass
            except Exception,e:
                print e
