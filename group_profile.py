#-*-coding:utf-8-*-
import decoder
import codecs
import re
child_count={}

proced_obj=set()
def findparent(info):
    proced_obj.add(info)
    for pname in info.parent_group:
        child_count[pname]=child_count.get(pname,0)+1
    for pinfo in info.parent_obj:
        if pinfo in proced_obj:
            continue
        findparent(pinfo)
if __name__ == '__main__':
    grouptree=decoder.GroupTree()
    grouptree.LoadTree()

    for key in grouptree.group_dic:
        info=grouptree.group_dic[key]
        proced_obj=set()
        child_count[key]=child_count.get(key,0)+1
        findparent(info)

    child_list=[(key,child_count[key]) for key in child_count]
    child_list.sort(lambda a,b:cmp(a[1],b[1]))

    useable_word=set()
    for one in child_list:
        if one[1]>=200:
            break
        useable_word.add(one[0])

    #=================================================================================
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
        if float(addcount)/allcount>0.3:
            print checkwords[index][0],index
            break
    checkwords=checkwords[index+1:]

    with codecs.open('data/groupcount_proced.txt','w','utf8') as groupf:
        for one in checkwords:
            if one[0] in useable_word:
                print >>groupf,one[0]