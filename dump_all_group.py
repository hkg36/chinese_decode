#-*-coding:utf-8-*-
import sqlite3
if __name__ == '__main__':
    sqlcon=sqlite3.connect('data/group.db')
    sqlc=sqlcon.cursor()
    sqlc.execute('select word,parent_group from groupword')

    groups=set()
    for word,parent_group in sqlc:
        if parent_group:
            parent_group=parent_group.split(u',')
            groups.update(parent_group)

    groups=list(groups)
    groups.sort()
    print len(groups)
    for one in groups:
        print one