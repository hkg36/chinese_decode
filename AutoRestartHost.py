#-*-coding:utf-8-*-
import subprocess
import sys
import time
if __name__ == '__main__':
    params=['python']
    params[1:]=sys.argv[1:]
    proc=None
    try:
        while True:
            proc=subprocess.Popen(params)
            proc.wait()
            time.sleep(5)
    except BaseException,e:
        print e
        pass
    finally:
        if proc and proc.returncode is None:
            proc.kill()