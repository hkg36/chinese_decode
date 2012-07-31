#-*-coding:utf-8-*-
fp=open('chinese_data.txt','r')
all_line=fp.readlines();
fp.close();
import json
class WordCell(dict):
    is_word_end=False

word_dict_root=dict()
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


full_text=u'人民网华盛顿7月30日电 7月30日，美国国务卿克林顿向国会递交了《2011年度国际宗教自由报告》。当日中午，美国国务院负责国际宗教自由的无任所大使苏珊·约翰逊·库克在此间就这一报告进行了吹风。'+\
u'美国国务院在这一报告中再次攻击中国宗教人权状况，显示其干涉中国内政恶习不改。报告妄称，2011年，在政府尊重和保护宗教自由方面，中国的情况“显著恶化”，并被列入所谓“特别关注”名单。此外，阿富汗、古巴、厄立特里亚、伊朗、朝鲜、巴基斯坦、俄罗斯、沙特阿拉伯、苏丹、叙利亚、越南、乌兹别克斯坦、土库曼斯坦等多国也被美国“特别关注”。'+\
u'1998年，美国国会通过了《国际宗教自由法》。根据这一法律，美国国务院建立了国际宗教自由办公室，并由美国总统任命的无任所大使领导这一办公室。这一办公室负责起草年度国际宗教自由报告。'+\
u'7月30日下午，美国国务卿克林顿还将在卡内基国际和平基金会就这一报告发表讲话。'