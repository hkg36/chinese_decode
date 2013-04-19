#-*-coding:utf-8-*-
import worddict
import bsddb3
import os,sys
db_env_flag=bsddb3.db.DB_CREATE | bsddb3.db.DB_INIT_MPOOL| bsddb3.db.DB_INIT_TXN | bsddb3.db.DB_INIT_LOCK | bsddb3.db.DB_RECOVER
print db_env_flag
path=sys.path[0]
path=os.path.join(path,'data/dictdb')
worddict.buildDict(path,'data/outdata','data/outindex',db_env_flag)