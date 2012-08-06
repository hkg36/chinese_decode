import gzip
import zlib
import urllib2
import string
from StringIO import StringIO

def ReadHttpBody(response):
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
    elif response.info().get('Content-Encoding') == 'deflate':
        content = zlib.decompress(content)
    return content
