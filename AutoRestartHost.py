#-*-coding:utf-8-*-
import subprocess
import sys
import time
if __name__ == '__main__':
    params=['python']
    params[1:]=sys.argv[1:]
    while True:
        proc=subprocess.Popen(params)
        proc.wait()
        time.sleep(5)
    pass