#-*-coding:utf-8-*-
import bsddb3
import os
import pickle

class TestData:
    id=0
    name=None
def getName(priKey, PriData):
    obj=pickle.loads(PriData)
    if obj!=None:
        return [obj.name]
    return None

if __name__ == '__main__':
    home_dir='data/bdbtest'
    try:
        os.mkdir(home_dir)
    except Exception,e:
        print e
    dbenv = bsddb3.db.DBEnv()
    dbenv.open(home_dir, bsddb3.db.DB_CREATE | bsddb3.db.DB_INIT_MPOOL |
                         bsddb3.db.DB_INIT_LOCK | bsddb3.db.DB_THREAD |bsddb3.db.DB_INIT_TXN)
    txn=dbenv.txn_begin()
    d = bsddb3.db.DB(dbenv)
    d.open('maindb.db','main',bsddb3.db.DB_BTREE,bsddb3.db.DB_CREATE, 0666,txn)

    dindex=bsddb3.db.DB(dbenv)
    dindex.set_flags(bsddb3.db.DB_DUP)
    dindex.open('maindb.db','index',bsddb3.db.DB_BTREE,bsddb3.db.DB_CREATE, 0666,txn)

    txn.commit()

    d.associate(dindex,getName)
    """data=TestData()
    data.id=5
    data.name="陈新"
    pd=pickle.dumps(data,pickle.HIGHEST_PROTOCOL)
    d.put('test5',pd)"""
    """pd= d.get('test5')
    data=pickle.loads(pd)"""
    print dindex.pget("陈新")

    d.close()
    dbenv.close()