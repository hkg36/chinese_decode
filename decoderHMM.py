#coding:utf8
import decoder
import codecs
import re

class MapCell(object):
    def __init__(self,word=None,index=None,last=None):
        self.word=word
        self.index=index
        self.last=last
class MapHead(MapCell):
    pass
def BuildWordMap(wordlist):
    startpoint=[]
    head=MapHead()
    head.next=startpoint
    for i in xrange(len(wordlist)):
        o=wordlist[i]
        if o.pos==0:
            startpoint.append(MapCell(o,i,head))
    def FindNext(startpoint,wordlist):
        for sp in startpoint:
            nextpoint = []
            sp.next=nextpoint
            nextstart=wordlist[sp.index].pos+len(wordlist[sp.index].word)
            for i in xrange(sp.index+1,len(wordlist)):
                o=wordlist[i]
                if o.pos==nextstart:
                    nextpoint.append(MapCell(o,i,sp))
            FindNext(nextpoint,wordlist)
    FindNext(startpoint,wordlist)
    return head
if __name__ == '__main__':
    word_dict_root=decoder.LoadDefaultWordDic()

    fp=codecs.open('testdata.txt','r','utf-8')
    full_text=fp.read()
    fp.close()
    #full_text=u"张悟本神话"
    text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]+",full_text)
    text_list=[]
    for tp in text_pice:
        tp=tp.strip()
        if len(tp)>0:
            text_list.append(tp)

    for tp in text_list:
        print tp
        spliter=decoder.LineSpliter(word_dict_root)
        spliter.SplitLine(tp)
        BuildWordMap(spliter.found_word)