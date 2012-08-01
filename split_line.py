#-*-coding:utf-8-*-
import re
import ujson

full_text=u'人民网华盛顿7月30日电 7月30日，美国国务卿克林顿向国会递交了《2011年度国际宗教自由报告》。当日中午，美国国务院负责国际宗教自由的无任所大使苏珊·约翰逊·库克在此间就这一报告进行了吹风。';
text_pice=re.split(u"[\\p。 ；  ， ： “ ”（ ） 、 ？ 《 》]",full_text)
for tp in text_pice:
    print tp