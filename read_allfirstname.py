#-*-coding:utf-8-*-
import tools
import re
import codecs
if __name__ == '__main__':
    doc=tools.GetHtmlByCurl('http://www.sosuo.name/surnames.asp')
    fn_list=doc.findall("//div[@class='sosuo_por']/div[@class='famous']/a")
    fnlist=[]
    for one in fn_list:
        res=re.search(u'(?P<fn>[^姓]+)姓?',one.text)
        if res:
            fnlist.append(res.group('fn'))

    f=codecs.open('data/firstname_list.txt','w','utf8')
    for fn in fnlist:
        f.write('%s\n'%fn)
    f.close()