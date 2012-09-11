#-*-coding:utf-8-*-
import weibo_tools
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
    word=re.sub(u"转发微博","",word,0,re.I)
    word=word.strip()
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
        dbc.execute("select weibo_id,times from all_word where word=?",(key,))
        for resline in dbc:
            if resline[0] in weibo_id_count:
                weibo_id_count[resline[0]]+=resline[1];
            else:
                weibo_id_count[resline[0]]=resline[1];

    max_count=0
    for id in weibo_id_count:
        count=weibo_id_count[id]
        if max_count<count:
            max_count=count
    max_weibo_id=[]
    for id in weibo_id_count:
        count=weibo_id_count[id]
        if count==max_count:
            max_weibo_id.append(id)
    if len(max_weibo_id)>0:
        for weibo_id in max_weibo_id:
            dbc.execute('select word from all_weibo where weibo_id=?',(weibo_id,))
            for resrow in dbc:
                print "==",resrow[0]
            dbc.execute("select word from all_weibo where reply_id=?",(weibo_id,))
            for resrow in dbc:
                word=RemoveWeiboRubbish(resrow[0])
                if len(word)>0:
                    weibo_reply_list.append(word)

    return weibo_reply_list

if __name__ == '__main__':
    debug_mode=0
    word_dict_root=LoadDefaultWordDic()

    APP_KEY = '2117816058'
    APP_SECRET = '80f6fac494eed2f4e8a54acb85683aea'
    CALLBACK_URL = 'http://ljnh.sinaapp.com/controller/callback.php'
    """APP_KEY = '685427335'
    APP_SECRET = '1d735fa8f18fa94d87cd9196867edfb6'
    CALLBACK_URL = 'http://www.hkg36.tk/weibo/authorization'"""
    user_name = '878260705@qq.com'
    user_psw = 'xianchangjia'

    sub_users=[('xjc11112@qq.com','xianchangjia'),#我是小猪猪0319
        ('xcj11113@qq.com','xianchangjia'), #请叫我宝儿1
        ('xcj11114@qq.com','xianchangjia')]#谁是现场2

    bot_id_set=set()

    db=sqlite3.connect("data/weibo_word_base.db")
    dbc=db.cursor()
    dbc.execute("select weibo_id from weibo_oauth group by weibo_id")
    for line in dbc:
        bot_id_set.add(string.atoi(line[0]))
    dbc.close()
    db.close()

    client=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
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
        if line['user']['id'] in bot_id_set:
            continue
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
                    sub_user=sub_users[random.randint(0,len(sub_users)-1)]
                    #sub_client=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,sub_user[0],sub_user[1])
                    wbres=client.post.comments__reply(id=status['id'],cid=line['id'],comment=weibo_reply)
                pass
            except Exception,e:
                print e
    exit()
    for sub_user in sub_users:
        dbc=dbbot.cursor()
        sub_client=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,sub_user[0],sub_user[1])
        comment_since_id=0
        dbc=dbbot.cursor()
        dbc.execute("select last_comment from last_proc_comment where user_name=?",(sub_user[0],))
        resrow=dbc.fetchone()
        if resrow!=None:
            comment_since_id=resrow[0]
        if debug_mode==1:
            comment_since_id=0
        wres=sub_client.comments__to_me(count=80,since_id=comment_since_id)

        if wres.has_key('comments'):
            comments=wres['comments']
            if len(comments)>0:
                last_comment=comments[0]
                if debug_mode==0:
                    dbc=dbbot.cursor()
                    dbc.execute("replace into last_proc_comment(user_name,last_comment) values(?,?)",(sub_user[0],last_comment['id']))
                    dbbot.commit()
        else:
            comments=[]

        for line in comments:
            if line['user']['id'] in bot_id_set:
                continue
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
                        wbres=sub_client.post.comments__reply(id=status['id'],cid=line['id'],comment=weibo_reply)
                    pass
                except Exception,e:
                    print e