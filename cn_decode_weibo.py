#-*-coding:utf-8-*-
from decoder import *
from weibo_autooauth import *

if __name__ == '__main__':

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
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'

    client=GetWeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
    public_time_line=client.statuses__public_timeline()

    statuses=public_time_line['statuses']
    for one in statuses:
        text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]",one['text'])
        text_list=[]
        for tp in text_pice:
            tp=tp.strip()
            if len(tp)>0:
                text_list.append(tp)

        for tp in text_list:
            print tp
            spliter=LineSpliter(word_dict_root)
            words=spliter.ProcessLine(tp)
            for word in words:
                if word_dict_root.word_type.has_key(word.word):
                    types=word_dict_root.word_type[word.word]
                else:
                    types=None
                print u">>%s %s"%(word.word,str(types))
