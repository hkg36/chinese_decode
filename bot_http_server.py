#-*-coding:utf-8-*-
import web
import time
import json
import weibo_bot
import decoder
import sqlite3

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
        searchdb=sqlite3.connect("data/dbforsearch.db")
        res=weibo_bot.FindReplyForSentence(word_dict_root,searchdb,req)

        web.header('Content-Type', 'text/html; charset=utf-8')
        return json.dumps({'error':0,'res':res},ensure_ascii=False)

if __name__ == '__main__' :
    webapp=web.application(urls, globals())
    webapp.run()