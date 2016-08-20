#-*-coding:utf-8-*-
from decoder import WordCell
import codecs
import pickle
import json,gzip
import math,sqlite3
import worddict2

class WordTree:
    word_all=[]
    word_loaded={}
    dbenv=None
    db=None
    def __init__(self):
        pass
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
    def LoadFinish2(self):
        wordlist=[]
        for one in self.word_loaded:
            wc=self.word_loaded[one]
            info={'freq':wc.freq}
            if wc.type:
                info['type']=wc.type
            if wc.weight:
                info['weight']=wc.weight
            if wc.wordgroup:
                info['group']=wc.wordgroup
            wordlist.append((one.encode('utf8'),pickle.dumps(info,pickle.HIGHEST_PROTOCOL)))
        return wordlist
    def LoadWordType(self):
        fp=open('hmm/wordtype.txt')
        print 'data/dictbase/word_pos.txt.gz loaded'
        word_pos=json.load(fp)
        fp.close()
        for word in word_pos:
            wc = self.AddWordToTree(word)
            wc.type=word_pos[word]
    def LoadWordFreqFile(self):
        try:
            fp=gzip.open("data/dictbase/word_freq.txt.gz")
            print "data/dictbase/word_freq.txt.gz loaded"
            word_freq_list=json.load(fp)
            fp.close()
        except Exception,e:
            print e
            return

        for word in word_freq_list:
            freq=word_freq_list[word]
            addedCell=self.AddWordToTree(word)
            addedCell.freq=freq

            bs=math.log(freq,math.e)
            if bs==0:
                addedCell.weight=0
            else:
                addedCell.weight=math.log(freq,math.e)
    def LoadHudongbaikeWords(self):
        fp=gzip.open('data/hudongbaike_groupofword.txt.gz','r')
        print 'data/hudongbaike_groupofword.txt.gz loaded'
        word_group=json.load(fp)
        fp.close()
        for word in word_group:
            wc=self.AddWordToTree(word)
            wc.wordgroup=word_group[word].get('group')
        """fp=gzip.open('../fetch_hudongbaike/data/hudongbaike_allword.txt.gz','r')
        info = codecs.lookup('utf-8')
        fp = codecs.StreamReaderWriter(fp, info.streamreader, info.streamwriter)
        for line in fp:
            line=line.strip()
            wc=self.AddWordToTree(line)
            word_attr=word_group.get(line)
            if word_attr:
                wc.wordgroup=word_attr.get('group')
        fp.close()"""
    def LoadXinHuaZhiDian(self):
        db=sqlite3.connect('../fetch_hudongbaike/data/xinhuazhidian.db')
        print '../fetch_hudongbaike/data/xinhuazhidian.db loaded'
        dc=db.cursor()
        dc.execute('select distinct(word) from words')
        for word, in dc:
            wc=self.AddWordToTree(word)
        dc.close()
        db.close()
def BuildDefaultWordDic():
    word_dict_root=WordTree()
    fp=codecs.open('dict/word3.txt','r','utf8')## 来自国家语言委员会
    print 'dict/word3.txt loaded'
    all_line=fp.readlines()
    fp.close()
    word_dict_root.BuildFindTree(all_line)
    word_dict_root.LoadWordType()
    word_dict_root.LoadWordFreqFile()
    word_dict_root.LoadHudongbaikeWords()
    word_dict_root.LoadXinHuaZhiDian()
    print 'dict loaded'
    return word_dict_root.LoadFinish2()
    #if worddict:
    #    worddict.buildDict('data/dictdb','data/outdata','data/outindex',db_env_flag)

def DumpGroupTree():
    sqlcon=sqlite3.connect('../fetch_hudongbaike/data/group.db')
    sqlc=sqlcon.cursor()
    sqlc.execute('select word,parent_group from groupword')

    f=codecs.open('data/grouplist.txt','w','utf8')
    for word,parent_group in sqlc:
        if parent_group!=None:
            print >>f,'%s %s'%(word,parent_group)
    f.close()
if __name__ == '__main__':
    print worddict2.version()
    wordlist=BuildDefaultWordDic()
    buildres=worddict2.buildDict('data/dbindex',wordlist)
    print 'build res:',buildres
    DumpGroupTree()