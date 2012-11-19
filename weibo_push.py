# -*- coding: utf-8 -*-
import weibo_tools
import time
import random
if __name__ == '__main__':
    APP_KEY = '1369839428'
    APP_SECRET = '98cc3112eaa11163de98b840939960dc'
    CALLBACK_URL = 'http://www.hkg36.com/ok'
    user_name = ['xjc11112@qq.com','xcj11113@qq.com','xcj11114@qq.com']
    user_psw = 'xianchangjia'
    weibo_accouts=[
        ['xjc11112@qq.com','xianchangjia'],
        ['xcj11113@qq.com','xianchangjia'],
        ['xcj11114@qq.com','xianchangjia'],
        ['414961260@qq.com','6581101'],
        ['ellvv2012@126.com','xianchangjia'],
        ['xxggood2005@163.com','76119443%a'],
        ['496642325@qq.com','xianchangjia']
    ]

    postword=[
        u'盒子里的火锅，好有爱哦',
        u'这和火锅没关系呀，女的太漂亮啦都',
        u'去MIX，拿铁前必吃的泡妹火锅，',
        u'工体美女都原来这样漂亮的',
        u'三里屯数百美女同时聚集，我都进不去',
        u'旁边竟然是那英 +麒麟锦庭火锅道微博链接',
        u'发现去三里屯夜店的美女们都会先来这里',
        u'靠家人你可以当上公主，靠老公你可以当上王妃，靠！靠自己才能当上女王']
    post_append=u'@麒麟锦庭火锅道 @好美妞 http://www.haomeiniu.com/vote.php'

    weiboclient=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,weibo_accouts[0][0],weibo_accouts[0][1])
#39.929593 116.440913
    now_user=0
    while True:
        try:
            tl=weiboclient.place__nearby_timeline(count=50,lat=39.929593,long=116.440913,range=5000,offset=1)
            statuses=tl.get('statuses')
            if statuses:
                users=set()
                for line in statuses:
                    user=line.get('user')
                    if user:
                        text=line['text']
                        text=text[0:5]+'...'
                        to_post_word=postword[random.randint(0,len(postword)-1)]+text+post_append
                        weiboclient=weibo_tools.WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,weibo_accouts[now_user][0],weibo_accouts[now_user][1])
                        try:
                            print weiboclient.post.comments__create(comment=to_post_word,id=line['id'])
                        except Exception,e:
                            print e
                            print weibo_accouts[now_user]
                        time.sleep(90)
                        now_user=(now_user+1)%len(weibo_accouts)
        except Exception,e:
            print e
            time.sleep(30)
