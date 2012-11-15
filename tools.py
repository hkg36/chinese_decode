import sys
import subprocess
def RestartSelf():
    params=['python']
    params[1:]=sys.argv
    subprocess.Popen(params)
    exit()
if __name__ == '__main__':
    RestartSelf()
