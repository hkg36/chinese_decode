#-*-coding:utf-8-*-
import re
import ujson
fp=open('chinese_data.txt','r')
all_line=fp.readlines()
fp.close()

class WordCell(dict):
    is_word_end=False
    word_ref=None

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
                startcell[word]=thiscell
            startcell=thiscell
        startcell.is_word_end=True
        startcell.word_ref=line_text
    return word_dict_root

word_dict_root=BuildFindTree(all_line)

full_text=u'人民网华盛顿7月30日电 7月30日，美国国务卿克林顿向国会递交了《2011年度国际宗教自由报告》。当日中午，美国国务院负责国际宗教自由的无任所大使苏珊·约翰逊·库克在此间就这一报告进行了吹风。';
text_pice=re.split(u"[\\p。；，：“ ”（ ）、？《》·]",full_text)
text_list=[]
for tp in text_pice:
    tp=tp.strip()
    if len(tp)>0:
        text_list.append(tp)

PROCESS_DONE=0
PROCESS_MID_SUCCESS=1
PROCESS_END_FAIL=2
PROCESS_MID_SUCCESS_WITH_WORD=3

class WordProcessor:
    def __init__(self,start_step):
        self.next_step=start_step
    def input(self,one):
        if self.next_step.has_key(one):
            self.next_step=self.next_step[one]
            if self.next_step.is_word_end:
                return PROCESS_MID_SUCCESS_WITH_WORD
            else:
                return PROCESS_MID_SUCCESS
        else:
            if self.next_step.is_word_end:
                return PROCESS_DONE
            else:
                return PROCESS_END_FAIL

def ProcessLine(word_dict_root,line):
    process_work=[]
    new_processor=WordProcessor(word_dict_root)
    process_work.append(new_processor)

    found_word={}
    for char in line:
        next_round_process_word=[]
        need_create_new_process=False
        for one_proc in process_work:
            res=one_proc.input(char)
            if PROCESS_MID_SUCCESS==res:
                next_round_process_word.append(one_proc)
            elif PROCESS_MID_SUCCESS_WITH_WORD==res:
                need_create_new_process=True
                next_round_process_word.append(one_proc)

                count=found_word.get(one_proc.next_step.word_ref,0)
                found_word[one_proc.word_ref]=count+1
            elif PROCESS_DONE==res:
                next_round_process_word.append(one_proc)

                count=found_word.get(one_proc.word_ref,0)
                found_word[one_proc.word_ref]=count+1

        if need_create_new_process:
            new_processor=WordProcessor(word_dict_root)
            next_round_process_word.append(new_processor)
        process_work=next_round_process_word

for tp in text_list:
    print tp
    ProcessLine(word_dict_root,tp)
