#-*-coding:utf-8-*-
import codecs
import StringIO
import threading

class STTrans(object):
    T2S={}
    S2T={}
    def init(self):
        fp=codecs.open('T_To_S_List.txt','r','utf-8')
        all_line=fp.readlines()
        fp.close()


        for index in range(0,len(all_line)-1,2):
            TLine=all_line[index].strip()
            SLine=all_line[index+1].strip()
            for wi in range(len(TLine)):
                self.T2S[TLine[wi]]=SLine[wi]
                self.S2T[SLine[wi]]=TLine[wi]
    __inst = None # make it so-called private
    __lock = threading.Lock() # used to synchronize code
    @staticmethod
    def getInstanse():
        STTrans.__lock.acquire()
        if not STTrans.__inst:
            STTrans.__inst = object.__new__(STTrans)
            object.__init__(STTrans.__inst)
            STTrans.__inst.init()
        STTrans.__lock.release()
        return STTrans.__inst
    def TransT2S(self,line):
        resline=StringIO.StringIO()
        for word in line:
            if word in self.T2S:
                resline.write(self.T2S[word])
            else:
                resline.write(word)
        return resline.getvalue()
    def TransS2T(self,line):
        resline=StringIO.StringIO()
        for word in line:
            if word in self.S2T:
                resline.write(self.S2T[word])
            else:
                resline.write(word)
        return resline.getvalue()
if __name__ == '__main__':
    print STTrans.getInstanse().TransT2S(u"好展覽與大家分享！去拓展眼界吧！")