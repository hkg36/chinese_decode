import sys
import subprocess
import html5lib
import pycurl
from cStringIO import StringIO

def RestartSelf():
    params=['python']
    params[1:]=sys.argv
    subprocess.Popen(params)
    exit()

def GetHtmlByCurl(url):
    b=GetHttpByCurl(url)
    if b==None:
        return None

    try:
        parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("lxml"), namespaceHTMLElements=False)
        doc=parser.parse(b)
    except Exception,e:
        return None
    return doc
def GetHttpByCurl(url):
    curl=pycurl.Curl()
    curl.setopt(pycurl.URL,url)
    curl.setopt(pycurl.ENCODING,'gzip')
    curl.setopt(pycurl.TIMEOUT, 20)
    b = StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, b.write)
    try:
        curl.perform()
    except Exception,e:
        print e
        return None
    if curl.getinfo(pycurl.HTTP_CODE)!=200:
        return None
    b.seek(0)
    return b

if __name__ == '__main__':
    RestartSelf()
