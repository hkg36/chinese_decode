#-*-coding:utf-8-*-
import weibo_tools
import sqlite3
import time
if __name__ == '__main__':
    client = weibo_tools.DefaultWeiboClient()
    dbcon=sqlite3.connect('data/public_time_line.sqlite')
    dbcon.execute('create table if not exists pubweibo(id unsigned long PRIMARY KEY,txt varchar(1024))')
    while True:
        res_list=client.statuses__public_timeline(count=200)
        if res_list:
            statuses=res_list.get('statuses')
            if statuses:
                for line in statuses:
                    id=line['id']
                    text=line['text']
                    dbcon.execute('insert or ignore into pubweibo(id,txt) values(?,?)',(id,text))
        dbcon.commit()

        time.sleep(30)