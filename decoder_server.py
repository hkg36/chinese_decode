#-*-coding:utf-8-*-
import decoder
import QueueWorker2
import gzip
from cStringIO import StringIO
import json
import re

Queue_User='guest'
Queue_PassWord='guest'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/tools'

class ChineseSplitWork(QueueWorker2.QueueWorker):
    def Prepare(self):
        self.word_dict_root=decoder.LoadDefaultWordDic()
        self.signwordpos=decoder.SignWordPos()
        self.signwordpos.LoadData()
        #self.grouptree=decoder.GroupFinder()
        #self.grouptree.LoadTree()
        return self
    def RequestWork(self,params,body):
        if params.get('zip'):
            body=gzip.GzipFile(fileobj=StringIO(body),mode='r').read()
        if isinstance(body,unicode)==False and 'encode' in params:
            body=body.decode(params['encode'])

        text_pice=re.split(u"[\s!?,。；，：“ ”（ ）、？《》·]+",body)
        text_list=[]
        for tp in text_pice:
            tp=tp.strip()
            if len(tp)>0:
                text_list.append(tp)

        result_text_list=[]
        for tp in text_list:
            spliter=decoder.LineSpliter(self.word_dict_root)
            spliter.SplitLine(tp)
            spliter.AfterProcess()
            words=spliter.found_word
            self.signwordpos.ProcessSentence(words)
            #self.grouptree.ProcessOneLine(words)
            """for word in words:
                groupstr=None
                if word.info:
                    groups=word.info.get('group')
                    if groups:
                        groupstr=','.join(groups)"""
            word_list=[]
            for word in words:
                word_list.append({'pos':word.pos,'txt':word.word,'type':word.word_type_list,'nocn':word.is_no_cn})
            result_text_list.append({'pice':tp,'words':word_list})

        outbuf=StringIO()
        json.dump(result_text_list,gzip.GzipFile(fileobj=outbuf,mode='w'))
        return {'zip':True},outbuf.getvalue()
if __name__ == '__main__':
    ChineseSplitWork(Queue_Server,Queue_Port,Queue_Path,Queue_User,Queue_PassWord,'chinese_split').Prepare().run()