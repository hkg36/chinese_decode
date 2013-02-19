#-*-coding:utf-8-*-
import web
import string
import json
import weibo_bot
import decoder
#import FindResponse

urls = (
    '/bot', 'Bot',
    )
word_dict_root=decoder.LoadDefaultWordDic()


class Bot:
    def GET(self):
        inputs=web.input()
        req=inputs.get('req')
        if isinstance(req,unicode)==False:
            return json.dumps({'error':1,'message':'request error'})
        ver=int(inputs.get('ver',0))
        json_result={'error':0}
        if ver==0:
            res=weibo_bot.FindReplyForSentence(word_dict_root,req)
        elif ver==1:
            res=FindResponse.FindResponse(word_dict_root,req)
        if len(res)>0:
            json_result['res']=res
        else:
            json_result['error']=1
            json_result['res']=['不懂你说什么阿']

        web.header('Content-Type', 'text/html; charset=utf-8')
        return json.dumps(json_result,ensure_ascii=False)

if __name__ == '__main__' :
    webapp=web.application(urls, globals())
    webapp.run()