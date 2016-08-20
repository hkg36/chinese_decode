#-*-coding:utf-8-*-
import xml.etree.cElementTree as etree
import os.path
import json
import gzip
import codecs
import re

type_change={
'a':'a',        #adjective        形容词
'ad':'d',       #adjective as adverbial    形容词当副词用
'ag':'a',       #adjective morpheme 形容词词素
'an':"v",       # adjective with nominal function	形容词当动词
'b':'a',          #non-predicate adjective	非前置形容词
'bg':'a',        #non-predicate adjective morpheme	非前置形容词素
'c':'c',           #conjunction		连词
'cg':"c",         #conjunction morpheme		连词词素
'd':'d',           #adverb		副词
'dg':'d',         #adverb morpheme	副词词素
'e':'e',           #interjection	感叹词
'ew':'ew',        #sentential punctuation	句子标点
'f':'n',            #directional locality	地点方位
'fg':'n',         #locality morpheme		地点语素
'g':'g',           #morpheme		语素
'h':'n',           #prefix		前缀
'i':'i',            #idiom		成语
'j':'n',            #abbreviation	缩写
'k':'k',           #suffix		后缀
'l':'l',            #fixed expressions		固定表达式
'm':'m',         #numeral		数字
'mg':'m',       #numeric morpheme	数字语素
'n':'n',           #common noun		一般名词
'ng':'n',         #noun morpheme	名词语素
'nr':'n',          #personal name	人名
'ns':'n',         #place name		地名
'nt':'n',         #organization name	机构名称
'nx':'n',         #nominal character string	名词性角色串
'nz':'n',         #other proper noun	其他名词
'o':'o',           #onomatopoeia	拟声词
'p':'p',           #preposition		介词
'pg':'p',         #preposition morpheme	介词语素
'q':'q',           #classifier		量词
'qg':'q',         #classifier morpheme	量词语素
'r':'r',            #pronoun		代词
'rg':'r',          #pronoun morpheme	代词语素
's':'n',           #space word		分割词
't':'t',            #time word		时间词
'tg':'t',          #time word morpheme	时间词语素
'u':'u',           #auxiliary		助词
'v':'v',           #verb		动词
'vd':'d',         #verb as adverbial	动词做副词
'vg':'v',         #verb morpheme	动词语素
'vn':'n',         #verb with nominal function	动词当名词
'w':'w',          #symbol and non-sentential punctuation	标点符号
'x':'n',           #unclassified items	未分类
'y':'u',           #modal particle	形态小品词
'yg':'u',         #modal particle morpheme 形态小品词语素
'z':'z',           #descriptive		描述符
'zg':'z',         #descriptive morpheme	描述符语素
}
rootdir = "dict/character"
all_file=[]
for parent, dirnames, filenames in os.walk(rootdir):
    for filename in filenames:
        all_file.append(os.path.join(parent, filename))

typecount=dict()
typewordcount=dict()
typetranscount=dict()
starttype=dict()
endtype=dict()
wordtype=dict()
for file in all_file:
    tree = etree.parse(file)

    for s in tree.findall('./text/file/p/s'):
        last_pos = None
        for w in s:
            if w.tag=='w':
                now_text=w.text
                now_pos=w.attrib['POS'].strip()
                now_pos=type_change[now_pos]
                if now_pos in typecount:
                    typecount[now_pos]+=1
                else:
                    typecount[now_pos]=1
                if now_text not in wordtype:
                    wordtype[now_text]=set()
                wordtype[now_text].add(now_pos)
                if now_pos not in typewordcount:
                    typewordcount[now_pos]=set()
                typewordcount[now_pos].add(now_text)

                if last_pos:
                    transtoken=last_pos+'>'+now_pos
                    if transtoken in typetranscount:
                        typetranscount[transtoken]+=1;
                    else:
                        typetranscount[transtoken]=1;
                else:
                    if now_pos not in starttype:
                        starttype[now_pos]=0
                    starttype[now_pos]+=1
                last_pos=now_pos
            else:
                if last_pos:
                    if last_pos not in endtype:
                        endtype[last_pos]=0
                    endtype[last_pos]+=1
                last_pos=None

allm=typewordcount['m']
new_m=set()
for one in allm:
    res=re.sub(ur"(１|２|３|４|５|６|７|８|９|０|．|廿|零|一|二|三|四|五|六|七|八|九|十|百|千|万|亿|1|2|3|4|5|6|7|8|9|0|·|\.|％|／|\\|%)",ur"",one)
    if len(res)>0:
        new_m.add(one)
typewordcount['m']=new_m
for type in typewordcount:
    typewordcount[type]=list(typewordcount[type])
save=codecs.open("hmm/countdata.txt","w","utf-8")
json.dump({"typecount":typecount,
           "typewordcount":typewordcount,
           "typetranscount":typetranscount,
           "starttype":starttype,
           "endtype":endtype},save,ensure_ascii=False,indent=2)
save.close()

for one in wordtype:
    wordtype[one]=list(wordtype[one])
save=codecs.open("hmm/wordtype.txt","w","utf-8")
json.dump(wordtype,save,ensure_ascii=False,indent=2)
save.close()