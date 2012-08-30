#-*-coding:utf-8-*-
import xml.etree.ElementTree as etree
import os
import os.path
import json

rootdir = "dict/character"
all_file=[]
for parent, dirnames, filenames in os.walk(rootdir):
    for filename in filenames:
        all_file.append(os.path.join(parent, filename))

s_list=[]
for file in all_file:
    tree = etree.parse(file)
    root=tree.getroot()
    for l in root:
        if l.tag==u'text':
            for l2 in l:
                if l2.tag==u'file':
                    #文章
                    for l3 in l2:
                        if l3.tag==u'p':
                            #断落
                            for l4 in l3:
                                if l4.tag==u's':
                                    #句子
                                    one_s=[]
                                    for l5 in l4:
                                        if l5.tag==u'w':
                                            one_s.append((l5.text,l5.attrib[u'POS']))
                                    s_list.append(one_s)

word_list={}
for s in s_list:
    for w in s:
        POS_Set=None
        if w[0] in word_list:
            POS_Set=word_list[w[0]]
        else:
            POS_Set=dict()
            word_list[w[0]]=POS_Set
        if w[1] in POS_Set:
            POS_Set[w[1]]+=1
        else:
            POS_Set[w[1]]=1
#词/每个词性出现的次数
fp=open('data/word_pos.txt','w+')
json.dump(word_list,fp)
fp.close()

word_trans={}
for s in s_list:
    if len(s)<2:
        continue
    for index in range(1,len(s)-1):
        befor_w=s[index-1]
        now_w=s[index]

        if len(word_list[now_w[0]])==1:
            continue

        if now_w[0] in word_trans:
            now_w_state=word_trans[now_w[0]]
        else:
            now_w_state=dict()
            word_trans[now_w[0]]=now_w_state

        if now_w[1] in now_w_state:
            POS_State=now_w_state[now_w[1]]
        else:
            POS_State=dict()
            now_w_state[now_w[1]]=POS_State

        if befor_w[1] in POS_State:
            POS_State[befor_w[1]]+=1
        else:
            POS_State[befor_w[1]]=1

for word in word_trans:
    pos_list=word_trans[word]
    for pos in pos_list:
        before_pos = pos_list[pos]

        count=0
        for b_p in before_pos:
            count+=before_pos[b_p]

        before_pos_1=dict()
        for b_p in before_pos:
            before_pos_1[b_p]=float(before_pos[b_p])/count
        pos_list[pos]=before_pos_1
#词/可能的词性/前词词性导致本词词性的概率
fp=open('data/word_trans.txt','w+')
json.dump(word_trans,fp)
fp.close()

print len(word_list),len(word_trans)

