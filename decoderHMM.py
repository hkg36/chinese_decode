#coding:utf8
import decoder
import codecs
import re
import json
import math

class MapCell(object):
    def __init__(self,word=None,index=None,last=None):
        self.word=word
        self.index=index
        self.last=last
    def __str__(self):
        if self.word:
            return self.word.word
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
class HMM(object):
    def __init__(self):
        file=open("hmm/countdata_norm.txt")
        data=json.load(file)
        file.close()
        self.typecount=data["typecount"]
        self.typetranscount=data['typetranscount_pre']
        self.headtype=data['starttype']
    def SignWordType(self,found_word):
        for one in found_word:
            if "type" in one.info:
                types=one.info["type"]
            elif one.is_no_cn and one.is_num:
                types=["m"]
            else:
                types=["n"]
            one.types=types
class TypeMapCell(object):
    def __init__(self,type=None,word=None):
        self.type=type
        self.word=word
        self.typesel=[]
    def __str__(self):
        if self.word:
            return self.word.word.word

MAX_SELECT=10
def BuildTypeMap(wordmap,hmm):
    tail=list()
    typeh=TypeMapCell()
    typeh.posible=0
    def doBuild(tmap,map,tail):
        typesel=[]
        for type in map.word.types:
            tc=TypeMapCell(type,map)
            tc.last=tmap
            wordlongadd=(len(tc.word.word.word)-1)*0.9
            if tmap==typeh:
                tc.posible=hmm.headtype[tc.type]+hmm.typecount[tc.type]+wordlongadd
            else:
                ttrans=tmap.type+">"+tc.type
                translist=hmm.typetranscount[tmap.type]
                if ttrans in translist:
                    tc.posible=tmap.posible+translist[ttrans]+hmm.typecount[tc.type]+wordlongadd
                else:
                    return
            if len(tail)>=MAX_SELECT:
                if tc.posible<tail[0].posible:
                    return
            typesel.append(tc)
            if map.next:
                for nw in map.next:
                    doBuild(tc, nw,tail)
            else:
                if len(tail)>=MAX_SELECT:
                    tail.sort(key=lambda one: one.posible)
                    if tc.posible>tail[0].posible:
                        tail.pop(0)
                        tail.append(tc)
                else:
                    tail.append(tc)

        tmap.typesel.extend(typesel)
    for w in wordmap.next:
        doBuild(typeh,w,tail)

    return typeh,tail

def PrintMapPath(typecell):
    if hasattr(typecell,"last"):
        PrintMapPath(typecell.last)
    if typecell.word:
        print typecell.word.word.word,typecell.type,"/",
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

    hmm=HMM()
    for tp in text_list:
        print tp
        spliter=decoder.LineSpliter(word_dict_root)
        spliter.SplitLine(tp)
        hmm.SignWordType(spliter.found_word)
        wordmap=BuildWordMap(spliter.found_word)
        typemap,tails=BuildTypeMap(wordmap,hmm)
        #CountTypeMap(typemap,hmm)

        tails=[one for one in tails if hasattr(one,"posible")]
        tails.sort(key=lambda one:one.posible,reverse=True)
        for i in xrange(len(tails)):
            PrintMapPath(tails[i])
            print tails[i].posible,"\n"
        pass