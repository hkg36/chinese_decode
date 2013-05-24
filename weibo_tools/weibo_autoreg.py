#-*-coding:utf-8-*-
import sqlite3
import time
import urllib2
import urllib
import re
import httplib
#import pycurl
from cStringIO import StringIO
import json
import weibo_api
import gzip

def parseHeaders(header_file):
    header_file.seek(0)

    # Remove the status line from the beginning of the input
    unused_http_status_line = header_file.readline()
    lines = [line.strip() for line in header_file]

    # and the blank line from the end
    empty_line = lines.pop()
    if empty_line:
        raise urllib2.HTTPError("No blank line at end of headers: %r" % (line,))

    headers = {}
    for line in lines:
        try:
            name, value = line.split(':', 1)
        except ValueError:
            raise urllib2.HTTPError(
                "Malformed HTTP header line in response: %r" % (line,))

        value = value.strip()

        # HTTP headers are case-insensitive
        name = name.lower()
        headers[name] = value

    return headers

def GetWeiboOauth(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw):
    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url_1 = client.get_authorize_url()

    url = 'https://api.weibo.com/oauth2/authorize'

    reqdata = {
        'action': 'submit',
        'client_id': APP_KEY,
        'display': 'mobile',
        'passwd': user_psw,
        'redirect_uri': CALLBACK_URL,
        'response_type': 'code',
        'userId': user_name
        }
    reqstring=urllib.urlencode(reqdata)

    conn = httplib.HTTPSConnection("api.weibo.com",httplib.HTTPS_PORT)
    conn.request('POST', '/oauth2/authorize', headers = {"Host": "api.weibo.com",
                                    'Referer':url_1,
                                    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:13.0) Gecko/20100101 Firefox/21.0.1)",
                                    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                    "Accept-Language":"zh-cn,en-us;q=0.7,en;q=0.3",
                                    "Content-Type":"application/x-www-form-urlencoded",
                                    "Accept-Encoding":"gzip"}
                ,body=reqstring)
    res = conn.getresponse()
    resbody=res.read()
    if res.getheader('Content-Encoding')=='gzip':
        resbody=gzip.GzipFile(mode='rb',fileobj=StringIO(resbody)).read()

    oauth_code=None
    if res.status==302:
        new_location=res.getheader('location')
        if new_location:
            re_res = re.search('\?code=(?P<code>\w*)', new_location, re.IGNORECASE)
            if re_res != None:
                oauth_code = re_res.group('code')

    if oauth_code!=None:
        client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
        r = client.request_access_token(oauth_code)
        return r
    else:
        print '%s account fail'%user_name
        return None
def WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw):
    db=sqlite3.connect("data/weibo_oauths.db")
    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
    db.execute('CREATE TABLE IF NOT EXISTS weibo_oauth(app_key varchar(32) not null,user_name varchar(32) not null,user_psw varchar(64) not null,weibo_id varchar(32) not null,key varchar(30) not null,expires_time int not null,PRIMARY KEY(app_key,user_name))')
    dbc=db.cursor()
    dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and user_name=? and user_psw=? and expires_time>?",(APP_KEY,user_name,user_psw,time.time()-3600))
    dbrow=dbc.fetchone()
    if dbrow is not None:
        client.set_access_token(dbrow[1],dbrow[2])
        client.user_id=dbrow[0]
    else:
        oauth=GetWeiboOauth(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
        if oauth:
            dbc=db.cursor()
            dbc.execute("replace into weibo_oauth(app_key,user_name,user_psw,weibo_id,key,expires_time) values(?,?,?,?,?,?)",(APP_KEY,user_name,user_psw,oauth['uid'],oauth['access_token'],oauth['expires_in']))
            db.commit()
            client.set_access_token(oauth['access_token'], oauth['expires_in'])
            client.user_id=oauth['uid']
    dbc.close()
    db.close()
    return client
def GetUserOauth(APP_KEY,APP_SECRET,uid_or_name):
    db=sqlite3.connect("data/weibo_oauths.db")
    dbc=db.cursor()
    dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and (user_name=? or weibo_id=?) and expires_time>?",(APP_KEY,uid_or_name,uid_or_name,time.time()-3600))
    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET)
    dbrow=dbc.fetchone()
    if dbrow is not None:
        client.set_access_token(dbrow[1],dbrow[2])
        client.user_id=dbrow[0]
    dbc.close()
    dbc.close()
def RemoveWeiboOauth(APP_KEY,user_name):
    db=sqlite3.connect("data/weibo_oauths.db")
    db.execute("delete from weibo_oauth where app_key=? and user_name=?",(APP_KEY,user_name))
    db.close()

def DefaultWeiboClient():
    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://1.livep.sinaapp.com/api/weibo_manager_impl/sina_weibo/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia2'
    return WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
if __name__ == '__main__':
    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://1.livep.sinaapp.com/api/weibo_manager_impl/sina_weibo/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia2'

    oauth=GetWeiboOauth(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
    print json.dumps(oauth)