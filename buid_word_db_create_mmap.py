#-*-coding:utf-8-*-
import worddict
import bsddb3
db_env_flag=bsddb3.db.DB_CREATE | bsddb3.db.DB_INIT_MPOOL| bsddb3.db.DB_INIT_TXN | bsddb3.db.DB_INIT_LOCK | bsddb3.db.DB_RECOVER
worddict.buildDict('/app_data/chinese_decode/dictdb','/app_data/chinese_decode/dbindex',db_env_flag)