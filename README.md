## I am not in any way responsible for any damages caused by this Project.


# FIXER Botnet

FIXER Botnet is a simple botnet management system built using Python-socketio, Flask-socketio and Flask. It allows for like keylogging, persistence, and taking screenshots, webcam Pictures, recording audios, Bi-Directional File Transfer, DDOS PING-OF-DEATH, Command Execution, Payload Generation (Including Pythnon to Executable Conversion).

## Installation

This repository might not work on Linux because of winreg library in the persistence module.

1. Download the Repository:
```Download Zip https://github.com/TheLeopard65/fixer-botnet.git```
2. Navigate into the directory:
```Go the fixer-botnet-main Folder```
3. Open CMD in that directory by typing cmd in address bar of File Manager
4. Install the required Modules:
```pip instll -r requirements.txt```
5. Run the Server:
```python Server.py```
6. Run the Client:
```Python Client.py```

## Usage

1. Start the server by running `Server.py`.
2. Connect clients to the server by running `Client.py` on remote machines.
3. Access the Login Page at `http://server_ip:port/login.html`. by default it is `http://localhost:8000/login.html`
4. Login using the provided credentials. USERNAME : `admin` and PASSWORD : `admin9876`
5. Send commands to the connected clients via the Dashboard interface.
6. View the output and status of executed commands on the Web Application.
7. View the Screenshots taken, keylogs captured, files transfered in there respective Folders

## Features

- **Authentication:** Users can log in with a predefined username and password.
- **Dashboard:** Provides an overview of connected clients and their status.
- **Command Execution:** Allows users to send commands to connected clients.
- **Keylogger:** Captures keystrokes on client machines and saves them locally.
- **Persistence:** Enables persistence by adding the botnet to startup programs.
- **Screenshot:** Captures and sends screenshots of client desktops to the server.
- **Command Execution:** Send command to Client for execution and Displays Output on screen.
- **DDOS PING:** Launches a PING-OF-DEATH DDOS Attack on any provided IP-Address.
- **File Transfer:** Allows File Transfering between the Server and the Client.
- **Payload Generater:** Allows Generation of .exe and non .exe payload generation.

## Credits

This project was created by @TheLeopard65. 
