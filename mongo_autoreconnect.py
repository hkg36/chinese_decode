import pymongo
from time import sleep

def reconnect(f):
    def f_retry(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except pymongo.errors.AutoReconnect, e:
                print('Fail to execute %s [%s]' % (f.__name__, e))
                sleep(0.1)
            except Exception,e:
                print('Fail(2) to execute %s [%s]' % (f.__name__, e))
                sleep(20)
    return f_retry
pymongo.cursor.Cursor._Cursor__send_message =\
reconnect(pymongo.cursor.Cursor._Cursor__send_message)
pymongo.connection.Connection._send_message =\
reconnect(pymongo.connection.Connection._send_message)
pymongo.connection.Connection._send_message_with_response =\
reconnect(pymongo.connection.Connection._send_message_with_response)
