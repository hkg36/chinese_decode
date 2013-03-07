#-*-coding:utf-8-*-
import re
import string
import codecs
import bsddb3
import os
import pickle
import math
import sqlite3
import gzip
try:
    import ujson as json
except Exception,e:
    import json

class WordCell:
    freq=0
    type=None
    weight=0
    wordgroup=None

class DbTree:
    def __init__(self):
        home_dir='data/dictdb'
        self.dbenv = bsddb3.db.DBEnv()
        self.dbenv.open(home_dir, bsddb3.db.DB_CREATE | bsddb3.db.DB_INIT_MPOOL |
                                  bsddb3.db.DB_INIT_LOCK | bsddb3.db.DB_THREAD |bsddb3.db.DB_INIT_TXN|
                                  bsddb3.db.DB_RECOVER)
        self.db = bsddb3.db.DB(self.dbenv)
        self.db.open('maindb.db','main',bsddb3.db.DB_BTREE,bsddb3.db.DB_RDONLY, 0666)
        self.cursor=self.db.cursor()

        f=codecs.open('data/dictbase/firstname_list.txt','r','utf8')
        fnlist=set()
        for line in f:
            fnlist.add(line.strip())
        f.close()
        self.firstname=fnlist

    def findword(self,word):
        word_find=word.encode('utf8')
        res = self.cursor.get(word_find,bsddb3.db.DB_SET_RANGE)

        if res!=None:
            res=(res[0].decode('utf8'),pickle.loads(res[1]));
        return res
    def getwordinfo(self,word):
        word_find=word.encode('utf8')
        res=self.db.get(word_find)
        if res!=None:
            return pickle.loads(res)
        return None
    def __del__(self):
        if self.db:
            self.cursor.close()
            self.db.close()
        self.dbenv.close()
class WordTree:
    word_all=[]
    word_loaded={}
    def __init__(self):
        home_dir='data/dictdb'
        try:
            os.mkdir(home_dir)
        except Exception,e:
            print e
        self.dbenv = bsddb3.db.DBEnv()
        self.dbenv.open(home_dir, bsddb3.db.DB_CREATE | bsddb3.db.DB_INIT_MPOOL |
                             bsddb3.db.DB_INIT_LOCK | bsddb3.db.DB_THREAD |bsddb3.db.DB_INIT_TXN|
                             bsddb3.db.DB_RECOVER)
    def __del__(self):
        if self.db:
            self.db.close()
        self.dbenv.close()

    def BuildFindTree(self,all_line):
        for line in all_line:
            line=line.strip()
            self.AddWordToTree(line)

    def AddWordToTree(self,line_text):
        if line_text in self.word_loaded:
            return self.word_loaded[line_text]
        else:
            wc=WordCell()
            wc.word_ref=line_text
            self.word_loaded[line_text]=wc
            return wc
    def LoadFinish(self):
        for one in self.word_loaded:
            self.word_all.append(one)
        self.word_all.sort()

        self.db = bsddb3.db.DB(self.dbenv)
        try:
            self.db.remove('maindb.db','main')
        except Exception,e:
            print e
        self.db = bsddb3.db.DB(self.dbenv)
        self.db.open('maindb.db','main',bsddb3.db.DB_BTREE,bsddb3.db.DB_CREATE, 0666)

        for one in self.word_loaded:
            wc=self.word_loaded[one]
            info={'freq':wc.freq}
            if wc.type:
                info['type']=wc.type
            if wc.weight:
                info['weight']=wc.weight
            if wc.wordgroup:
                info['group']=wc.wordgroup
            self.db.put(one.encode('utf8'),pickle.dumps(info,pickle.HIGHEST_PROTOCOL))

        self.dbenv.txn_checkpoint()
        self.dbenv.log_archive(bsddb3.db.DB_ARCH_REMOVE)

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
            addedCell.type=word_type
            addedCell.weight=1/math.log(freq,2)
    def LoadWordType(self):
        fp=gzip.open('data/dictbase/word_pos.txt.gz')
        word_pos=json.load(fp)
        fp.close()
        for word in word_pos:
            wordtype=word_pos[word]
            wt=[]
            for type in wordtype:
                wt.append((type,wordtype[type]))
            wt.sort(lambda a,b:cmp(a[1],b[1]))
            wc=self.AddWordToTree(word)
            wc.type=[a[0] for a in wt]
    def LoadTextFreqBase(self,all_line):
        line_reader=re.compile("^(?P<word>[^\s]*)\s+(?P<freq>\d*)\s+(?P<type>[^\s]*)",re.IGNORECASE)
        for line in all_line:
            re_res=line_reader.match(line)
            word=re_res.group("word")
            freq=string.atoi(re_res.group('freq'))
            type=re_res.group('type')
            wc=self.AddWordToTree(word)
            wc.type=type
    def LoadWordFreqFile(self):
        try:
            fp=gzip.open("data/dictbase/word_freq.txt.gz")
            word_freq_list=json.load(fp)
            fp.close()
        except Exception,e:
            print e
            return

        for word in word_freq_list:
            freq=word_freq_list[word]
            addedCell=self.AddWordToTree(word)
            addedCell.freq=freq
            addedCell.weight=freq**(1.0/2)
    def LoadHudongbaikeWords(self):
        fp=gzip.open('../fetch_hudongbaike/data/hudongbaike_groupofword.txt.gz','r')
        word_group=json.load(fp)
        fp.close()
        fp=gzip.open('../fetch_hudongbaike/data/hudongbaike_allword.txt.gz','r')
        info = codecs.lookup('utf-8')
        fp = codecs.StreamReaderWriter(fp, info.streamreader, info.streamwriter)
        for line in fp:
            line=line.strip()
            wc=self.AddWordToTree(line)
            word_attr=word_group.get(line)
            if word_attr:
                wc.wordgroup=word_attr.get('group')
        fp.close()

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
            if res[0]==self.temp_word:
                foundword=FoundWord(self.temp_word,self.startpos)
                foundword.info=res[1]
                return foundword
            elif res[0].startswith(self.temp_word):
                return True
            else:
                return False
class LineSpliter:
    def __init__(self,search_root):
        self.number_set=set(u"0123456789%.一二三四五六七八九十百千万亿几某多单双")
        self.no_cn=''
        self.no_cn_start_pos=-1
        self.process_work=[]
        self.found_word=[]
        self.search_root=search_root
    def NoCnFound(self):
        if len(self.no_cn)>0:
            found_word=FoundWord(self.no_cn,self.no_cn_start_pos)
            found_word.is_no_cn=True
            for char in found_word.word:
                if char not in self.number_set:
                    found_word.is_num=False
                    break
            else:
                found_word.is_num=True
            self.found_word.append(found_word)
        self.no_cn=''
        self.no_cn_start_pos=-1
    def SplitLine(self,line):
        for index in xrange(len(line)):
            char=line[index]
            if char in self.number_set or re.match("[a-zA-Z]",char):
                if self.no_cn_start_pos==-1:
                    self.no_cn_start_pos=index
                self.no_cn=self.no_cn+char
            else:
                self.NoCnFound()

            if len(self.process_work)==0:
                self.process_work.append(SearchWork(index,self.search_root))
            next_round_process_word=[]
            need_create_new_process=False
            has_one_success=False
            for one_proc in self.process_work:
                res=one_proc.test_next_word(char) #检查下一个字
                if isinstance(res,FoundWord):
                    has_one_success=True
                    self.found_word.append(res)
                    next_round_process_word.append(one_proc)
                    need_create_new_process=True
                elif res==True:
                    has_one_success=True
                    next_round_process_word.append(one_proc)
                    #else:
                #    self.ProcessCellDie(one_proc)

            if has_one_success==False:
                sw=SearchWork(index,self.search_root)
                res=sw.test_next_word(char)
                if isinstance(res,FoundWord):
                    self.found_word.append(res)
                    next_round_process_word.append(sw)
                elif res==True:
                    next_round_process_word.append(sw)
                    need_create_new_process=False

            if need_create_new_process:
                next_round_process_word.append(SearchWork(index+1,self.search_root))

            self.process_work=next_round_process_word

        self.NoCnFound()

        self.found_word.sort(lambda a,b:cmp(a.pos,b.pos))
    def AfterProcess(self):
        self.CheckCantantPre()
        self.CheckTail()

        self.CheckDoubleOverlap()
        self.CheckAfterOverlap()

        self.CheckCantantPre()
        self.CheckTail()

        self.CheckName()
    def ProcessLine(self,line):
        self.SplitLine(line)
        self.AfterProcess()
        return self.found_word

    def split_small_word(self,word):
        proc_work=[]
        found_word=[]
        for index in xrange(len(word)):
            char=word[index]
            next_round_process_word=[]
            if len(proc_work)==0:
                proc_work.append(SearchWork(index,self.search_root))
            for one_proc in proc_work:
                res=one_proc.test_next_word(char) #检查下一个字
                if isinstance(res,FoundWord):
                    has_one_success=True
                    found_word.append(res)
                    next_round_process_word.append(one_proc)
                    need_create_new_process=True
                elif res==True:
                    has_one_success=True
                    next_round_process_word.append(one_proc)
            proc_work=next_round_process_word
        return found_word

    def printFoundList(self):
        for word in self.found_word:
            print "))-",word.pos,word.word
    def CheckDoubleOverlap(self):
        #检查当前词语刚好前半部分是前一个词后半部分是后一个词 当前词删除
        start_pos=1;
        while True:
            gorecheck=False
            if len(self.found_word)>=3:
                for index in xrange(start_pos,len(self.found_word)-1):
                    pre_word=self.found_word[index-1]
                    aft_word=self.found_word[index+1]
                    now_word=self.found_word[index]

                    for i2 in xrange(1,len(now_word.word)):
                        if pre_word.word.endswith(now_word.word[0:i2]):
                            if aft_word.word.startswith(now_word.word[i2:]):
                                start_pos=max(start_pos-1,1)
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
            for index in xrange(len(self.found_word)-1,0,-1):
                word=self.found_word[index]
                pre_word=self.found_word[index-1]
                if word.word.find(pre_word.word)>=0:
                    del self.found_word[index-1]

    def CheckAfterOverlap(self):
        #后词包含前词的结尾的时候，重叠部分归出现概率大的词
        for index in xrange(len(self.found_word)-1,0,-1):
            aft_word=self.found_word[index]
            now_word=self.found_word[index-1]
            if now_word.pos+len(now_word.word)<=aft_word.pos:
                continue
            for i2 in xrange(1,len(aft_word.word)):
                word_pice=aft_word.word[0:i2]
                if now_word.word.endswith(word_pice):
                    if (now_word.info!=None and aft_word.info!=None) and (now_word.info['freq']==0 or aft_word.info['freq']/now_word.info['freq']>2):
                        #字归后词 重新拆分前词
                        new_word=now_word.word
                        new_word=new_word[0:len(new_word)-i2]
                        new_found=self.split_small_word(new_word)
                        for found in new_found:
                            found.pos+=now_word.pos
                        del self.found_word[index-1]
                        self.found_word.extend(new_found)
                        self.found_word.sort(lambda a,b:cmp(a.pos,b.pos))
                        break
                    new_word=aft_word.word[i2:]
                    new_found=self.split_small_word(new_word)
                    offset_index=aft_word.pos+i2
                    for found in new_found:
                        found.pos+=offset_index
                    del self.found_word[index]
                    self.found_word.extend(new_found)
                    self.found_word.sort(lambda a,b:cmp(a.pos,b.pos))


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
def BuildDefaultWordDic():
    word_dict_root=WordTree()
    fp=codecs.open('dict/word3.txt','r','utf8')## 来自国家语言委员会
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)

    word_dict_root.LoadWordType()

    word_dict_root.LoadWordFreqFile()

    word_dict_root.LoadHudongbaikeWords()

    word_dict_root.LoadFinish()
    print 'dict loaded'
    return word_dict_root

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
    def BuildTree(self):
        sqlcon=sqlite3.connect('data/group.db')
        sqlc=sqlcon.cursor()
        sqlc.execute('select word,parent_group from groupword')

        group_dic={}
        for word,parent_group in sqlc:
            if parent_group:
                parent_group=parent_group.split(u',')
                obj=self.WordGroupInfo()
                obj.parent_group=parent_group
                obj.groupname=word
                obj.parent_obj=[]
                group_dic[word]=obj

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
        if level>2:
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
        for word in linewords:
            if word.info:
                groups=word.info.get('group')
                if groups:
                    for group in groups:
                        foundgroup=self.FindAllParent(group)
                        if foundgroup is not None:
                            for fg in foundgroup:
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
    #full_text=u"在今年的市两会上持续发酵"
    text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]+",full_text)
    text_list=[]
    for tp in text_pice:
        tp=tp.strip()
        if len(tp)>0:
            text_list.append(tp)

    grouptree=GroupFinder()
    grouptree.BuildTree()
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
            print u">>%s %s"%(word.word,word.word_type_list),groupstr
    grouptree.EndCountGroup()
