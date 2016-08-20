#-*-coding:utf-8-*-
import re
import string
import codecs
import pickle
import gzip
import math

try:
    import ujson as json
except Exception,e:
    import json

try:
    import worddict2 as worddict
    ver=worddict.version()
    if ver[1]<2:
        print 'worddict version error %d.%d.%d'%ver
        exit(0)
except Exception,e:
    worddict=None

class WordCell:
    freq=0
    type=None
    weight=0
    wordgroup=None

class DbTree:
    dbenv=None
    db=None
    cursor=None
    def __init__(self):
        self.dbenv = None
        self.db = None
        self.cursor=None

        self.dbFileFinder=worddict.DbFileFinder('data/dbindex')

        f=codecs.open('data/dictbase/firstname_list.txt','r','utf8')
        fnlist=set()
        for line in f:
            fnlist.add(line.strip())
        f.close()
        self.firstname=fnlist
    def findword(self,word):
        word_find=word.encode('utf8')
        res=None
        res=self.dbFileFinder.findString(word_find)
        if res!=None:
            res=res.decode('utf8')
        return res
    def getwordinfo(self,word):
        word_find=word.encode('utf8')
        res=None

        word_res=self.dbFileFinder.findString(word_find)
        if word_res == word_find:
            res=self.dbFileFinder.lastFoundValue()

        if res!=None and len(res)>0:
            return pickle.loads(res)
        return None

class FoundWord:
    def __init__(self,str,pos):
        self.word=str
        self.pos=pos
        self.word_type_list=None
        self.info=None
        self.is_no_cn=False
    def __str__(self):
        return self.word
class SearchWork:
    def __init__(self,startpos,searchroot):
        self.startpos=startpos
        self.searchroot=searchroot
        self.temp_word=''
    def __str__(self):
        return self.temp_word
    def test_next_word(self,char):
        self.temp_word+=char
        res=self.searchroot.findword(self.temp_word)
        if res==None:
            return False
        else:
            if res==self.temp_word:
                foundword=FoundWord(self.temp_word,self.startpos)
                return foundword
            elif res.startswith(self.temp_word):
                return True
            else:
                return False
class StaticVar:
    pass
StaticVar.number_set=set(u"0123456789%.一二三四五六七八九十百千万亿几某多单双廿零")
class LineSpliter:
    def __init__(self,search_root):
        self.found_word=None
        self.search_root=search_root
        self.no_cn=''
        self.no_cn_start_pos=-1

    def BaseSplitLine(self,line):

        process_work=[]
        found_word=[]

        def NoCnFound():
            if len(self.no_cn)>0:
                f_word=FoundWord(self.no_cn,self.no_cn_start_pos)
                f_word.is_no_cn=True
                for char in f_word.word:
                    if char not in StaticVar.number_set:
                        f_word.is_num=False
                        break
                else:
                    f_word.is_num=True
                found_word.append(f_word)
            self.no_cn=''
            self.no_cn_start_pos=-1

        for index in xrange(len(line)):
            char=line[index]
            if char in StaticVar.number_set or re.match("[a-zA-Z]",char):
                if self.no_cn_start_pos==-1:
                    self.no_cn_start_pos=index
                self.no_cn=self.no_cn+char
            else:
                NoCnFound()

            emptyadd=len(process_work)==0
            if emptyadd:
                process_work.append(SearchWork(index,self.search_root))
            next_round_process_word=[]
            for one_proc in process_work:
                res=one_proc.test_next_word(char) #检查下一个字
                if isinstance(res,FoundWord):
                    found_word.append(res)
                    next_round_process_word.append(one_proc)
                elif res==True:
                    next_round_process_word.append(one_proc)
                    #else:
                #    ProcessCellDie(one_proc)
            if not emptyadd:
                sw=SearchWork(index,self.search_root)
                res=sw.test_next_word(char)
                if isinstance(res,FoundWord):
                    found_word.append(res)
                    next_round_process_word.append(sw)
                elif res==True:
                    next_round_process_word.append(sw)

            process_work=next_round_process_word

        NoCnFound()

        def word_sort(a,b):
            res=cmp(a.pos,b.pos)
            if res==0:
                return cmp(len(a.word),len(b.word))
            return res
        found_word.sort(word_sort)

        for one in found_word:
            one.info=self.search_root.getwordinfo(one.word)
            if "freq" in one.info and one.info['freq']>0:
                one.info['freq']=math.log10(one.info['freq'])
        return found_word
    def SplitLine(self,line):
        self.found_word=self.BaseSplitLine(line)
    def AfterProcess(self):

        self.CheckCantantPre()
        self.CheckTail()
        #self.CheckOverlap()
        self.CheckAfterOverlap()

        self.CheckName()
    def ProcessLine(self,line):
        self.SplitLine(line)
        self.AfterProcess()
        return self.found_word

    def printFoundList(self):
        for word in self.found_word:
            print "))-",word.pos,word.word
    def CheckOverlap(self):
        check_index=[]
        end_index = len(self.found_word)
        for i in xrange(end_index):
            if self.found_word[i].pos==0:
                check_index.append(i)
            else:
                break
        while check_index:
            next_round_check_index=[]
            for i in check_index:
                nowword=self.found_word[i]
                nowword.pass_check=True
                endpos=nowword.pos+len(nowword.word)
                for ci in xrange(i+1,end_index):
                    ciw=self.found_word[ci]
                    if ciw.pos==endpos:
                        next_round_check_index.append(ci)
                    elif ciw.pos>endpos:
                        break
            check_index=next_round_check_index
        check_index=[end_index-1,]
        wend_pos=self.found_word[-1].pos+len(self.found_word[-1].word)-1
        for i in xrange(end_index-2,-1,-1):
            if (self.found_word[i].pos+len(self.found_word[i].word)-1)==wend_pos:
                check_index.append(i)
            else:
                break

        while check_index:
            next_round_check_index=[]
            for i in check_index:
                nowword=self.found_word[i]
                nowword.back_pass_check = True
                endpos=nowword.pos
                for ci in xrange(i-1,-1,-1):
                    ciw=self.found_word[ci]
                    cend=ciw.pos+len(ciw.word)
                    if cend==endpos:
                        next_round_check_index.append(ci)
                    elif cend<endpos:
                        break
            check_index=next_round_check_index

        new_word_order=[]
        for one in self.found_word:
            if hasattr(one,"pass_check") and hasattr(one,"back_pass_check"):
                new_word_order.append(one)
        self.found_word=new_word_order
    def CheckCantantPre(self):
        #检查前一个词语是当前词语的一部分 全文索引不需要这个
        if len(self.found_word)>=2:
            for index in xrange(len(self.found_word)-1,0,-1):
                word=self.found_word[index]
                pre_word=self.found_word[index-1]
                if word.word.startswith(pre_word.word):
                    del self.found_word[index-1]

    def CheckAfterOverlap(self):
        #后词包含前词的结尾的时候，重叠部分归出现概率大的词
        index=len(self.found_word)-1
        while True:
            if index<1:
                break
            aft_word=self.found_word[index]
            now_word=self.found_word[index-1]

            i2=now_word.pos+len(now_word.word)-aft_word.pos
            if i2<=0:
                index-=1
                continue
            if (now_word.info!=None and aft_word.info!=None) and\
                    (now_word.info['freq']==0 or aft_word.info['freq']/now_word.info['freq']<0.5):
                new_word = aft_word.word[i2:]
                new_found = self.BaseSplitLine(new_word)
                offset_index = aft_word.pos + i2
                for found in new_found:
                    found.pos += offset_index
                del self.found_word[index]
                self.found_word.extend(new_found)
                self.found_word.sort(lambda a, b: cmp(a.pos, b.pos))
            else:
                # 字归后词 重新拆分前词
                new_word = now_word.word
                new_word = new_word[0:len(new_word) - i2]
                new_found = self.BaseSplitLine(new_word)
                for found in new_found:
                    found.pos += now_word.pos
                del self.found_word[index - 1]
                self.found_word.extend(new_found)
                self.found_word.sort(lambda a, b: cmp(a.pos, b.pos))
            self.CheckCantantPre()
            self.CheckTail()
            index-=1

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
    def CheckName(self):
        if len(self.found_word)<2:
            return
        index=0
        while index<len(self.found_word):
            word=self.found_word[index]
            if len(word.word)==1:
                if word.word in self.search_root.firstname:
                    pass
            elif len(word.word)==2:
                if word.word in self.search_root.firstname:
                    pass
                elif word.word[0] in self.search_root.firstname:
                    pass
            index+=1
def LoadDefaultWordDic():
    return DbTree()

class SignWordPos:
    def LoadData(self):
        fp=gzip.open('data/dictbase/word_pos.txt.gz')
        self.word_pos=json.load(fp)
        fp.close()
        fp=gzip.open('data/dictbase/word_pos_max.txt.gz')
        self.word_pos_max=json.load(fp)
        fp.close()
        fp=gzip.open('data/dictbase/word_trans.txt.gz')
        self.word_tran=json.load(fp)
        fp.close()

    def ProcessSentence(self,words):
        if len(words)==0:
            return
        first_word=words[0]
        if first_word.word in self.word_pos_max:
            first_word.word_type_list=self.word_pos_max[first_word.word]
        else:
            first_word.word_type_list=None
        if len(words)>=2:
            for index in xrange(1,len(words)-1):
                pre_word=words[index-1]
                now_word=words[index]
                now_word.word_type_list=None
                if now_word.word in self.word_tran:
                    now_pos=self.word_tran[now_word.word]
                    if pre_word.word_type_list!=None:
                        now_posible_pos={}
                        for wt in pre_word.word_type_list:
                            if wt in now_pos:
                                sub_pos=now_pos[wt]
                                for wt2 in sub_pos:
                                    if wt2 in now_posible_pos:
                                        now_posible_pos[wt2]+=sub_pos[wt2]
                                    else:
                                        now_posible_pos[wt2]=sub_pos[wt2]
                        max_possible=0
                        for wt in now_posible_pos:
                            max_possible=max(max_possible,now_posible_pos[wt])
                        now_posible_pos_list=[]
                        for wt in now_posible_pos:
                            if max_possible==now_posible_pos[wt]:
                                now_posible_pos_list.append(wt)
                        now_word.word_type_list=now_posible_pos_list
                if now_word.word_type_list==None:
                    if now_word.word in self.word_pos_max:
                        now_word.word_type_list=self.word_pos_max[now_word.word]
class GroupTree:
    class WordGroupInfo:
        parent_group=None
        groupname=None
        parent_obj=set()
        def __str__(self):
            return self.groupname

    def LoadTree(self):
        group_dic={}
        f=codecs.open('data/grouplist.txt','r','utf8')
        for line in f:
            line=line.strip()
            word,parent_group=line.split(' ')
            parent_group=parent_group.split(u',')
            obj=self.WordGroupInfo()
            obj.parent_group=parent_group
            obj.groupname=word
            obj.parent_obj=[]
            group_dic[word]=obj
        f.close()

        for word in group_dic:
            obj=group_dic[word]
            for pg in obj.parent_group:
                po=group_dic.get(pg)
                if po:
                    obj.parent_obj.append(po)

        self.group_dic=group_dic

    def FindAllParent(self,groupname):
        foundgroup=set()
        ginfo=self.group_dic.get(groupname)
        if ginfo is None:
            return None
        foundgroup.add(ginfo)
        self._findparentgroup(ginfo,foundgroup)
        return foundgroup
    def _findparentgroup(self,ginfo,foundgroups,level=0):
        if level>4:
            return
        tofind=[]
        for obj in ginfo.parent_obj:
            if obj not in foundgroups:
                tofind.append(obj)
                foundgroups.add(obj)
        for tf in tofind:
            self._findparentgroup(tf,foundgroups,level+1)
class GroupFinder(GroupTree):
    def StartCountGroup(self):
        self.group_count={}
    def ProcessOneLine(self,linewords):
        all_groups=set()
        for word in linewords:
            passproc=False
            if word.word_type_list and len(word.word_type_list)>0:
                passproc=True
                for type in word.word_type_list:
                    if string.find(type,'n')!=-1:
                        passproc=False
                        break
            if passproc:
                continue
            if word.info:
                groups=word.info.get('group')
                if groups:
                    for group in groups:
                        foundgroup=self.FindAllParent(group)
                        if foundgroup is not None:
                            #for oneg in foundgroup:
                                #self.group_count[oneg.groupname]=self.group_count.get(oneg.groupname,0)+1
                            all_groups.update(foundgroup)
        for fg in all_groups:
            self.group_count[fg.groupname]=self.group_count.get(fg.groupname,0)+1
    def EndCountGroup(self):
        itemlist=self.group_count.items()
        itemlist.sort(lambda a,b:-cmp(a[1],b[1]))
        for i in xrange(len(itemlist)):
            print itemlist[i][0],itemlist[i][1]
if __name__ == '__main__':
    #BuildDefaultWordDic()

    word_dict_root=LoadDefaultWordDic()
    signwordpos=SignWordPos()
    signwordpos.LoadData()

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

    grouptree=GroupFinder()
    grouptree.LoadTree()
    grouptree.StartCountGroup()
    for tp in text_list:
        print tp
        spliter=LineSpliter(word_dict_root)
        spliter.SplitLine(tp)
        spliter.AfterProcess()
        words=spliter.found_word
        signwordpos.ProcessSentence(words)
        grouptree.ProcessOneLine(words)
        for word in words:
            groupstr=None
            if word.info:
                groups=word.info.get('group')
                if groups:
                    groupstr=','.join(groups)
            #print u">>%s "%(word.word,word.word_type_list),groupstr
            print u"%s/" % (word.word),
        print u"\n"
    #grouptree.EndCountGroup()
