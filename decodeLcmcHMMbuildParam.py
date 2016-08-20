#coding:utf-8
import codecs
import json
import math

save=codecs.open("hmm/countdata.txt","r","utf-8")
data=json.load(save)
save.close()

typecount=data["typecount"]
typewordcount=data["typewordcount"]
typetranscount=data["typetranscount"]
starttype=data["starttype"]
endtype=data["endtype"]

def Normalization(list):
    tcount = 0
    for one in list:
        tcount += list[one]
    for one in list:
        list[one] = math.log(math.e,float(list[one]) / tcount)

Normalization(typecount)

for one in typewordcount:
    typewordcount[one]=len(typewordcount[one])
Normalization(typewordcount)

pre_count={}
rev_count={}

for one in typetranscount:
    start=one[0]
    end=one[-1]
    if start not in pre_count:
        pre_count[start]={}
    if end not in rev_count:
        rev_count[end]={}
    pre_count[start][one]=typetranscount[one]
    rev_count[end][one]=typetranscount[one]

for start in pre_count:
    alltran=pre_count[start]
    Normalization(alltran)

for end in rev_count:
    alltran=rev_count[end]
    Normalization(alltran)

Normalization(starttype)
Normalization(endtype)

save=codecs.open("hmm/countdata_norm.txt","w","utf-8")
json.dump({"typecount":typecount,
           "typewordcount":typewordcount,
           "typetranscount_pre":pre_count,
            "typetranscount_rev":rev_count,
           "starttype":starttype,
           "endtype":endtype},save,ensure_ascii=False,indent=2)
save.close()