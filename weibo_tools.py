#-*-coding:utf-8-*-
import weibo_api
import sqlite3
import time
import urllib2
import urllib
import re
try:
    import ujson as json
except :
    import json
def GetWeiboOauth(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw):
    class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            raise urllib2.HTTPError(req.get_full_url(),code,msg,headers,fp)
    opener = urllib2.build_opener(MyHTTPRedirectHandler)

    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url_1 = client.get_authorize_url()

    url = 'https://api.weibo.com/oauth2/authorize'

    reqdata = {
        'action': 'submit',
        'client_id': APP_KEY,
        'display': 'mobile',
        'offcialMobile': 'null',
        'passwd': user_psw,
        'redirect_uri': CALLBACK_URL,
        'response_type': 'code',
        'userId': user_name,
        'withOfficalFlag': 0,
        }
    reqheader={
        'Accept-encoding':'gzip',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:13.0) Gecko/20100101 Firefox/13.0.1)',
        'Referer':url_1,
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'zh-cn,en-us;q=0.7,en;q=0.3',
        }
    reqstring=urllib.urlencode(reqdata)
    request = urllib2.Request(url,reqstring,reqheader)
    res_location=None
    try:
        response = opener.open(request, timeout=20)
    except urllib2.HTTPError,redirError:
        res_location=redirError.hdrs['Location']
    if res_location!=None:
        re_res = re.search('\?code=(\w*)', res_location, re.IGNORECASE)
        if re_res != None:
            oauth_code = re_res.group(1)
        else:
            oauth_code = None

    client=None
    if oauth_code!=None:
        client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
        r = client.request_access_token(oauth_code)
        #client.set_access_token(r['access_token'], r['expires_in'])
        #uid=string.atoi(r['uid'])
    return r
def WeiboClient(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw):
    db=sqlite3.connect("data/weibo_word_base.db")
    client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
    dbc=db.cursor()
    dbc.execute("select weibo_id,key,expires_time from weibo_oauth where app_key=? and user_name=? and expires_time>?",(APP_KEY,user_name,time.time()-3600))
    dbrow=dbc.fetchone()
    if dbrow!=None:
        client.set_access_token(dbrow[1],dbrow[2])
        client.user_id=dbrow[0]
    else:
        oauth=GetWeiboOauth(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
        dbc=db.cursor()
        dbc.execute("replace into weibo_oauth(app_key,user_name,weibo_id,key,expires_time) values(?,?,?,?,?)",(APP_KEY,user_name,oauth['uid'],oauth['access_token'],oauth['expires_in']))
        db.commit()
        client.set_access_token(oauth['access_token'], oauth['expires_in'])
        client.user_id=oauth['uid']
    db.close()
    return client