import codecs
fp=codecs.open('dict/chinese_data.txt','r','utf-8')
all_line=fp.readlines()
fp.close()

word_exist=set()
word_out=[]
for line in all_line:
    line=line.strip()
    if line not in word_exist:
        word_out.append(line)
        word_exist.add(line)

fp=codecs.open('dict/chinese_data.txt','w','utf-8')
for one in word_out:
    fp.write(one)
    fp.write(u"\n")
fp.close()