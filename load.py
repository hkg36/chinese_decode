#-*-coding:utf-8-*-
import re
import copy
import ujson
fp=open('chinese_data.txt','r')
all_line=fp.readlines()
fp.close()

class WordCell(dict):
    word_ref=None
    word_pre=None

def BuildFindTree(all_line):
    word_dict_root=WordCell()
    for line in all_line:
        line=line.strip()
        line_text=line.decode('utf-8')

        startcell=None
        if word_dict_root.has_key(line_text[0]):
            startcell=word_dict_root[line_text[0]]
        else:
            startcell=WordCell()
            word_dict_root[line_text[0]]=startcell
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
    return word_dict_root

word_dict_root=BuildFindTree(all_line)

class FoundWord:
    word=None
    pos=-1
    def __init__(self,str,nowpos):
        self.word=str
        self.pos=nowpos-len(str)

def ProcessLine(word_dict_root,line):
    process_work=[]

    found_word=[]
    number_set=set()
    for char in u"0123456789.一二三四五六七八九十百千万亿几某":
        number_set.add(char)
    number=''
    for index in range(len(line)):
        char=line[index]
        if char in number_set:
            number=number+char
        else:
            read_number=number
            number=''

            if len(read_number)>0:
                found_word.append(FoundWord(read_number,index))
                process_work.append(word_dict_root['n'])

        if len(process_work)==0:
            process_work.append(word_dict_root)
        next_round_process_word=[]
        need_create_new_process=False
        has_one_success=False
        for one_proc in process_work:
            if one_proc.has_key(char):
                has_one_success=True
                next=one_proc[char]
                next_round_process_word.append(next)
                if next.word_ref!=None:
                    #print next.word_ref
                    need_create_new_process=True
            else:
                if one_proc.word_ref!=None:
                    found_word.append(FoundWord(one_proc.word_ref,index))
                else:
                    pre_index=0
                    while one_proc.word_pre!=None:
                        pre_index+=1
                        one_proc=one_proc.word_pre
                        if one_proc.word_ref!=None:
                            found_word.append(FoundWord(one_proc.word_ref,index-pre_index))
                            break

        if has_one_success==False:
            if word_dict_root.has_key(char):
                need_create_new_process=False
                next_round_process_word.append(word_dict_root[char])
        if need_create_new_process:
            next_round_process_word.append(word_dict_root)

        process_work=next_round_process_word

    for one_proc in process_work:
        if one_proc.word_ref!=None:
            found_word.append(FoundWord(one_proc.word_ref,len(line)))

    if len(found_word)>=2:
        res_found_word=[]
        last_word=found_word[len(found_word)-1]
        for index in range(len(found_word)-2,-1,-1):
            word=found_word[index]
            if word.word.endswith(last_word.word):
                last_word=word
            else:
                res_found_word.append(last_word)
                last_word=word
        res_found_word.append(found_word[0])
        res_found_word.reverse()
        found_word=res_found_word
    return found_word

full_text=u"""除苏拉以外，今年第10号台风“达维”也已在西北太平洋上生成，目前正向中国沿海逼近。预计将于2日傍晚到3日早晨在江苏启东到山东青岛沿海一带登陆。
据介绍，此次台风有六个特点：一是双台风活动，路径变数大。二是风圈半径较大，中心风力强。三是鼎盛期正面登陆，防御战线长。四是可能深入内陆，影响范围广。五是多地引发强降雨，持续时间长。六是风雨潮遭遇，防御难度大.
中央气象台1日18时发布暴雨蓝色预警，预计1日20时至2日20时，浙江东部、福建东部、台湾等地有大到暴雨，其中，浙江南部沿海和福建北部沿海局地有大暴雨(100～140毫米)，台湾中北部有大暴雨，部分地区有特大暴雨(300～500毫米)。
国家防总透露，从目前预测情况看，“苏拉”、“达维”登陆后可能深入内陆影响长江流域的江西以及淮河、黄河甚至海河流域的江苏、安徽、山东、河南以及华北等地。预计两个台风的影响范围将跨长江中下游、淮河、黄河中下游、海河等流域10多个省份。
由于南北方前期降雨过程多、洪水量级大、土壤含水量趋于饱和，遇强降雨极易引发大的洪涝灾害，局部地区可能造成严重的山洪、泥石流和滑坡等次生灾害。""";

text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]",full_text)
text_list=[]
for tp in text_pice:
    tp=tp.strip()
    if len(tp)>0:
        text_list.append(tp)

for tp in text_list:
    print tp
    words=ProcessLine(word_dict_root,tp)
    for word in words:
        print '》'*word.pos,word.word
