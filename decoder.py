#-*-coding:utf-8-*-
import re
import copy
import json
import pickle
import string
import codecs
import math

class WordCell(dict):
    word_ref=None
    word_pre=None
    freq=0

class WordTree(WordCell):
    word_type={}
    word_weight={}
    def BuildFindTree(self,all_line):
        for line in all_line:
            line=line.strip()
            line_text=line.decode('utf-8')
            self.AddWordToTree(line_text)

    def AddWordToTree(self,line_text):
        startcell=None
        if self.has_key(line_text[0]):
            startcell=self[line_text[0]]
        else:
            startcell=WordCell()
            self[line_text[0]]=startcell
        for word in line_text[1:]:
            thiscell=None
            if startcell.has_key(word):
                thiscell=startcell[word]
            else:
                thiscell=WordCell()
                thiscell.word_pre=startcell
                startcell[word]=thiscell
            startcell=thiscell
        startcell.word_ref=line_text
        return startcell

    def LoadSogouData(self,all_line):
        line_reader=re.compile("^([^\s]*)\s+(\d*)\s+(.*)",re.IGNORECASE)
        for line in all_line:
            line=line.decode('utf-8')
            re_res=line_reader.match(line)
            word=re_res.group(1)
            freq=string.atoi(re_res.group(2))

            word_type=[]
            word_typelist=re_res.group(3).split(',')
            for one in word_typelist:
                one=one.strip()
                if len(one)>0:
                    word_type.append(one)

            addedCell=self.AddWordToTree(word)
            addedCell.freq=freq
            self.word_type[word]=word_type
            self.word_weight[word]=freq**(1.0/2)
    def LoadTextFreqBase(self,all_line):
        line_reader=re.compile("^(?P<word>[^\s]*)\s+(?P<freq>\d*)\s+(?P<type>[^\s]*)",re.IGNORECASE)
        for line in all_line:
            re_res=line_reader.match(line)
            word=re_res.group("word")
            freq=string.atoi(re_res.group('freq'))
            type=re_res.group('type')
            addedCell=self.AddWordToTree(word)
            addedCell.freq=freq
            self.word_type[word]=type
            self.word_weight[word]=freq**(1.0/2)

class FoundWord:
    def __init__(self,str,pos,treepos):
        self.word=str
        self.pos=pos
        self.tree_pos=treepos
    def __str__(self):
        return self.word
class SearchWork:
    def __init__(self,startpos,searchroot):
        self.startpos=startpos
        self.searchroot=searchroot
class LineSpliter:
    def __init__(self,search_root):
        self.number_set=set()
        for char in u"0123456789%.一二三四五六七八九十百千万亿几某多单双":
            self.number_set.add(char)
        self.no_cn=''
        self.no_cn_start_pos=-1
        self.process_work=[]
        self.found_word=[]
        self.search_root=search_root

    def CheckProcessCell(self,one_proc):
        if one_proc.searchroot.word_ref!=None:
            return one_proc
        else: #无法找到词语的时候，回溯比当前位置短的最长词语
            while one_proc.searchroot.word_pre!=None:
                one_proc.searchroot=one_proc.searchroot.word_pre
                if one_proc.searchroot.word_ref!=None:
                    return one_proc
        return None

    def ProcessCellDie(self,one_proc):
        one_proc=self.CheckProcessCell(one_proc)
        if one_proc!=None:
            self.found_word.append(FoundWord(one_proc.searchroot.word_ref,one_proc.startpos,one_proc.searchroot))

    def CheckNoCnFound(self):
        if self.no_cn_fin:
            if len(self.no_cn)>0:
                found_word=FoundWord(self.no_cn,self.no_cn_start_pos,None)
                found_word.is_no_cn=True
                self.found_word.append(found_word)
            self.no_cn=''
            self.no_cn_start_pos=-1

    def ProcessLine(self,line):
        for index in range(len(line)):
            self.no_cn_fin=False
            char=line[index]
            if char in self.number_set or re.match("[a-zA-Z]",char):
                if self.no_cn_start_pos==-1:
                    self.no_cn_start_pos=index
                self.no_cn=self.no_cn+char
            else:
                self.no_cn_fin=True

            if len(self.process_work)==0:
                self.process_work.append(SearchWork(index,self.search_root))
            next_round_process_word=[]
            need_create_new_process=False
            has_one_success=False
            for one_proc in self.process_work:
                if one_proc.searchroot.has_key(char): #检查下一个字
                    has_one_success=True
                    next=one_proc.searchroot[char]
                    one_proc.searchroot=next
                    next_round_process_word.append(one_proc)
                    if next.word_ref!=None:
                        #print next.word_ref
                        need_create_new_process=True
                else:
                    self.ProcessCellDie(one_proc)
                self.CheckNoCnFound()

            if has_one_success==False:
                if self.search_root.has_key(char):
                    need_create_new_process=False
                    next_round_process_word.append(SearchWork(index,self.search_root[char]))
            if need_create_new_process:
                next_round_process_word.append(SearchWork(index+1,self.search_root))

            self.process_work=next_round_process_word

        self.CheckNoCnFound()
        for one_proc in self.process_work:
            self.ProcessCellDie(one_proc)

        self.CheckDoubleOverlap()
        self.CheckCantantPre()
        self.CheckTail()
        self.CheckAfterOverlap()
        self.found_word.sort(lambda a,b:cmp(a.pos,b.pos))
        self.CheckCantantPre()
        self.CheckTail()

        return self.found_word

    def CheckDoubleOverlap(self):
        #检查当前词语刚好前半部分是前一个词后半部分是后一个词 当前词删除
        start_pos=len(self.found_word)-2;
        while True:
            gorecheck=False
            if len(self.found_word)>=3:
                for index in range(start_pos,0,-1):
                    pre_word=self.found_word[index-1]
                    #if len(pre_word.word)==1:
                    #    continue
                    aft_word=self.found_word[index+1]
                    if len(aft_word.word)==1:
                        continue
                    now_word=self.found_word[index]

                    for i2 in range(1,len(now_word.word)):
                        if pre_word.word.endswith(now_word.word[0:i2]):
                            if aft_word.word.startswith(now_word.word[i2:]):
                                start_pos=min(start_pos+1,len(self.found_word)-3)
                                gorecheck=True
                                del self.found_word[index]
                                break
                    if gorecheck:
                        break
            if gorecheck==False:
                break

    def CheckCantantPre(self):
        #检查前一个词语是当前词语的一部分 全文索引不需要这个
        if len(self.found_word)>=2:
            for index in range(len(self.found_word)-1,0,-1):
                word=self.found_word[index]
                pre_word=self.found_word[index-1]
                if word.word.find(pre_word.word)>=0:
                    del self.found_word[index-1]

    def CheckAfterOverlap(self):
        #后词包含前词的结尾的时候，重叠部分归出现概率大的词
        for index in range(len(self.found_word)-1,0,-1):
            aft_word=self.found_word[index]
            now_word=self.found_word[index-1]
            if now_word.pos+len(now_word.word)<=aft_word.pos:
                continue
            while True:
                recheck=False
                for i2 in range(1,len(aft_word.word)):
                    word_pice=aft_word.word[0:i2]
                    if now_word.word.endswith(word_pice):
                        if aft_word.tree_pos==None or now_word.tree_pos==None or now_word.tree_pos.freq==0 or \
                            aft_word.tree_pos.freq/now_word.tree_pos.freq>2:
                            #字归后词 裁剪前词
                            new_word=now_word.word
                            new_word=new_word[0:len(new_word)-i2]
                            now_word.word=new_word
                        else:
                            new_word=aft_word.word[i2:]
                            aft_word.word=new_word

                if recheck==False:
                    break

    def CheckTail(self):
        #检查下一个词语是当前词语的后半部分 全文索引不需要这个
        if len(self.found_word)>=2:
            res_found_word=[]
            last_word=self.found_word[len(self.found_word)-1]
            index=0
            while index<(len(self.found_word)-1):
                word=self.found_word[index]
                word_aft=self.found_word[index+1]
                if word.pos<=word_aft.pos and (word.pos+len(word.word))>=(word_aft.pos+len(word_aft.word)):
                    del self.found_word[index+1]
                else:
                    index+=1
def LoadDefaultWordDic():
    word_dict_root=WordTree()
    fp=open('dict/chinese_data.txt','r') ##网友整理
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    """fp=open('word3.txt','r')## 来自国家语言委员会
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)"""
    """fp=open('dict/SogouLabDic.dic','r') ##来自搜狗互联网数据库
    all_line=fp.readlines()
    fp.close()
    word_dict_root.LoadSogouData(all_line)"""
    fp=codecs.open('dict/text_freq_base.txt','r','utf-8')
    all_line=fp.readlines()
    fp.close()
    word_dict_root.LoadTextFreqBase(all_line)
    print 'dict loaded'
    return word_dict_root

if __name__ == '__main__':
    word_dict_root=LoadDefaultWordDic()

    fp=codecs.open('testdata.txt','r','utf-8')
    full_text=fp.read()
    fp.close()
    #full_text=u"质量和服务"
    text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]",full_text)
    text_list=[]
    for tp in text_pice:
        tp=tp.strip()
        if len(tp)>0:
            text_list.append(tp)

    for tp in text_list:
        print tp
        spliter=LineSpliter(word_dict_root)
        words=spliter.ProcessLine(tp)
        for word in words:
            if word_dict_root.word_type.has_key(word.word):
                types=word_dict_root.word_type[word.word]
            else:
                types=None
            print u">>%s %s"%(word.word,str(types))
