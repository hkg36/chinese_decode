#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import codecs
import random
import time

def loadAccounts():
    accounts={}
    f=codecs.open('weibo_accounts/beijing_account.csv','r','utf-8')
    for line in f:
        line=line.strip()
        if len(line)>0:
            data=line.strip().split(',')
            accounts[data[0]]=data[1]
    f.close()
    return accounts
def loadWords():
    words=[]
    f=codecs.open('weibo_accounts/weibo_res.txt','r','utf-8')
    for line in f:
        line=line.strip()
        if len(line)>0:
            words.append(line)
    f.close()
    return words
if __name__ == '__main__':
    accounts=loadAccounts()
    accounts=accounts.items()

    APP_KEY = '1369839428'
    APP_SECRET = '98cc3112eaa11163de98b840939960dc'
    CALLBACK_URL = 'http://s.haomeiniu.com/Shop/sinaCallBack.html'

    target=1749247700
    words=loadWords()

    while True:
        try:
            weiboclient=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,accounts[0][0],accounts[0][1])
            weibores = weiboclient.statuses__user_timeline(uid=target,count=20)
        except Exception,e:
            print e
            time.sleep(20)
            continue
        statuses=weibores['statuses']
        for line in statuses:
            now_time=time.localtime()
            if now_time.tm_hour<2 or now_time.tm_hour>8:
                try:
                    word=words[random.randint(0,len(words)-1)]
                    account=accounts[random.randint(0,len(accounts)-1)]
                    weiboclient=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,account[0],account[1])
                    res=weiboclient.post.statuses__repost(id=line['id'],status=word,is_comment=0)
                    print res
                except Exception,e:
                    print e
            time.sleep(random.randint(3*60,6*60))