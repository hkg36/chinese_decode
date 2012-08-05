#-*-coding:utf-8-*-
import re
import copy
import ujson
import pickle

class WordCell(dict):
    word_ref=None
    word_pre=None
    def BuildFindTree(self,all_line):
        for line in all_line:
            line=line.strip()
            line_text=line.decode('utf-8')

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

word_dict_root=WordCell()

fp=open('chinese_data.txt','r')
all_line=fp.readlines()
fp.close()
word_dict_root.BuildFindTree(all_line)
fp=open('word3.txt','r')
all_line=fp.readlines()
fp.close()
word_dict_root.BuildFindTree(all_line)

class FoundWord:
    word=None
    pos=-1
    tree_pos=None
    def __init__(self,str,nowpos,treepos):
        self.word=str
        self.pos=nowpos-len(str)
        self.tree_pos=treepos

class LineSpliter:
    def __init__(self,search_root):
        self.number_set=set()
        for char in u"0123456789.一二三四五六七八九十百千万亿几某":
            self.number_set.add(char)
        self.number=''
        self.process_work=[]
        self.found_word=[]
        self.search_root=search_root

    def ProcessCellDie(self,one_proc):
        if one_proc.word_ref!=None:
            self.found_word.append(FoundWord(one_proc.word_ref,self.index,one_proc))
        else: #无法找到词语的时候，回溯比当前位置短的最长词语
            pre_index=0
            while one_proc.word_pre!=None:
                pre_index+=1
                one_proc=one_proc.word_pre
                if one_proc.word_ref!=None:
                    self.found_word.append(FoundWord(one_proc.word_ref,self.index-pre_index,one_proc))
                    break

    def ProcessLine(self,line):
        for self.index in range(len(line)):
            char=line[self.index]
            if char in self.number_set:#检查数词的存在
                for one_proc in self.process_work:
                    self.ProcessCellDie(one_proc)
                self.process_work=[]
                self.number=self.number+char
            else:
                read_number=self.number
                self.number=''
                if len(read_number)>0:
                    found_word=FoundWord(read_number,self.index,None)
                    found_word.is_number=True
                    self.found_word.append(found_word)
                    #self.process_work.append(self.search_root['n'])

            if len(self.process_work)==0:
                self.process_work.append(self.search_root)
            next_round_process_word=[]
            need_create_new_process=False
            has_one_success=False
            for one_proc in self.process_work:
                if one_proc.has_key(char): #检查下一个字
                    has_one_success=True
                    next=one_proc[char]
                    next_round_process_word.append(next)
                    if next.word_ref!=None:
                        #print next.word_ref
                        need_create_new_process=True
                else:
                    self.ProcessCellDie(one_proc)

            if has_one_success==False:
                if self.search_root.has_key(char):
                    need_create_new_process=False
                    next_round_process_word.append(self.search_root[char])
            if need_create_new_process:
                next_round_process_word.append(self.search_root)

            self.process_work=next_round_process_word

        if len(self.number)>0:
            self.found_word.append(FoundWord(self.number,len(line),None))
        for one_proc in self.process_work:
            if one_proc.word_ref!=None:
                self.found_word.append(FoundWord(one_proc.word_ref,len(line),one_proc))

        self.CheckDoubleOverlap()
        self.CheckCantantPre()
        self.CheckTail()
        self.CheckAfterOverlap()

        return self.found_word

    def CheckDoubleOverlap(self):
        start_pos=len(self.found_word)-2;
        while True:
            gorecheck=False
            if len(self.found_word)>=3: #检查当前词语刚好前半部分是前一个词后半部分是后一个词 当前词删除
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
        #后词包含前词的结尾的时候，重叠部分归后词
        for index in range(len(self.found_word)-1,0,-1):
            aft_word=self.found_word[index]
            now_word=self.found_word[index-1]
            while True:
                recheck=False
                for i2 in range(1,len(aft_word.word)):
                    word_pice=aft_word.word[0:i2]
                    if now_word.word.endswith(word_pice):
                        if now_word.tree_pos!=None:
                            pre_pos=now_word.tree_pos.word_pre
                            while pre_pos!=None and pre_pos.word_ref==None:
                                pre_pos=pre_pos.word_pre
                            if pre_pos!=None:
                                now_word.word=pre_pos.word_ref
                                now_word.tree_pos=pre_pos
                                recheck=True
                                break
                        else:
                            break
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
                if word.word.endswith(word_aft.word):
                    del self.found_word[index+1]
                else:
                    index+=1

fp=open('testdata.txt','r')
full_text=fp.read().decode('utf-8')
fp.close()
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
        print '》'*word.pos,word.word
