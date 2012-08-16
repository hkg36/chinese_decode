#! /usr/bin/env python
#coding=utf-8
import gzip
import zlib
try:
    import ujson as json
except :
    import json
import urllib2
import string
from StringIO import StringIO
import cStringIO

def json_request(url,body):
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    bodycontext=json.dumps(body)
    if len(bodycontext)>256:
        zipstr=cStringIO.StringIO()
        proczip=gzip.GzipFile(fileobj=zipstr,mode='wb')
        proczip.write(bodycontext)
        proczip.flush()
        proczip.close()
        bodycontext=zipstr.getvalue()
        request.add_header('Content-Type','gzip/json')
    else:
        request.add_header('Content-Type','application/json')
    response=urllib2.urlopen(request,bodycontext,timeout=100)

    cl = response.info().getheader('Content-length');
    if cl == None:
        cl = 0;
    else:
        cl = string.atoi(cl);
    if cl == 0:
        content = response.read();
    else:
        content = response.read(cl);
    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(content)
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()
    return json.loads(content)

if __name__ == '__main__':
    print json_request('http://livep.sinaapp.com/dataimport/basetest.php',{'data':'浙江广厦男篮'})