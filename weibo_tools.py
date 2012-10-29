#-*-coding:utf-8-*-
import weibo_api
import sqlite3
import time
import urllib2
import urllib
import re
import pycurl
from cStringIO import StringIO
try:
    import ujson as json
except :
    import json

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
    reqheader=[
        'Accept-encoding:gzip',
        'User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64; rv:13.0) Gecko/20100101 Firefox/13.0.1)',
        'Referer:'+url_1,
        'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language:zh-cn,en-us;q=0.7,en;q=0.3',
        ]
    curl=pycurl.Curl()
    curl.setopt(pycurl.URL,url)
    curl.setopt(pycurl.TIMEOUT, 20)
    curl.setopt(pycurl.HTTPHEADER,reqheader)
    curl.setopt(pycurl.POSTFIELDS,reqstring)

    b = StringIO()
    h = StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, b.write)
    curl.setopt(pycurl.HEADERFUNCTION, h.write)
    curl.setopt(pycurl.FOLLOWLOCATION, 0)
    curl.setopt(pycurl.MAXREDIRS, 5)
    curl.perform()
    b.seek(0)

    oauth_code=None
    if curl.getinfo(pycurl.HTTP_CODE)==302:
        res_head=parseHeaders(h)
        new_location=res_head.get('location')
        if new_location:
            re_res = re.search('\?code=(?P<code>\w*)', new_location, re.IGNORECASE)
            if re_res != None:
                oauth_code = re_res.group('code')

    client=None
    if oauth_code!=None:
        client = weibo_api.APIClient(app_key=APP_KEY, app_secret=APP_SECRET,redirect_uri=CALLBACK_URL)
        r = client.request_access_token(oauth_code)
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
if __name__ == '__main__':
    APP_KEY = '2824743419'
    APP_SECRET = '9c152c876ec980df305d54196539773f'
    CALLBACK_URL = 'http://livep.sinaapp.com/mobile/weibo2/callback.php'
    user_name = '496642325@qq.com'
    user_psw = 'xianchangjia'

    oauth=GetWeiboOauth(APP_KEY,APP_SECRET,CALLBACK_URL,user_name,user_psw)
    print json.dumps(oauth)