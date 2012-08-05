__author__ = 'applepc'
import codecs
fp=open('chinese_data.txt','r')
all_line=fp.readlines()
fp.close()

word_exist=set()
word_out=[]
for line in all_line:
    line=line.strip()
    line_text=line.decode('utf-8')
    if line_text not in word_exist:
        word_out.append(line_text)
        word_exist.add(line_text)

fp=codecs.open('chinese_data.txt','w','utf-8')
for one in word_out:
    fp.write(one)
    fp.write(u"\n")
fp.close()