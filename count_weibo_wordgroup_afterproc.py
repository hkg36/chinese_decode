#-*-coding:utf-8-*-
import codecs
import re
if __name__ == '__main__':
    checkwords=[]
    with codecs.open('data/groupcount.txt','r','utf8') as groupf:
        for line in groupf:
            rm=re.match('(?P<word>[^\s]*)\s+(?P<count>\d*)',line)
            if rm:
                word=rm.group('word')
                count=int(rm.group('count'))
                checkwords.append((word,count))
    allcount=0
    for one in checkwords:
        allcount+=one[1]
    addcount=0
    for index in xrange(len(checkwords)):
        addcount+=checkwords[index][1]
        if float(addcount)/allcount>0.35:
            print checkwords[index][0],index
            break
    checkwords=checkwords[index+1:]

    with codecs.open('data/groupcount_proced.txt','w','utf8') as groupf:
        for one in checkwords:
            print >>groupf,one[0]