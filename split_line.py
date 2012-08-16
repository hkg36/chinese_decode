#-*-coding:utf-8-*-
from ZODB import DB,FileStorage
from persistent import Persistent
import transaction
from decoder import *


class Host(Persistent):
    def __init__(self, hostname, ip, interfaces):
        self.hostname = hostname
        self.ip = ip
        self.interfaces = interfaces

storage = FileStorage.FileStorage('data/drawing.fs')
db = DB(storage)
connection = db.open()
root = connection.root()
host1 = Host('www.example.com', '192.168.7.2', ['eth0', 'eth1'])
root['www.example.com'] = host1
transaction.commit()
db.close()