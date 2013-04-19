import decoder
if __name__ == '__main__':
    decoder.BuildDefaultWordDic()
    gt=decoder.GroupTree()
    gt.DumpGroupTree()