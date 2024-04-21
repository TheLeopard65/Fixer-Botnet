## I am not in any way responsible for any damages caused by this Project.


# FIXER Botnet

FIXER Botnet is a simple botnet management system built using Python and Flask. It allows for remote command execution on client machines, as well as features such as keylogging, persistence, and taking screenshots.

## Installation

This repository might not work on Linux because of winreg library in the persistence module.

1. Clone the repository:
```git clone https://github.com/yourusername/fixer-botnet.git```
2. Navigate into the directory:
```cd fixer-botnet/```
3. Install the required Modules:
```pip instll -r requirements.txt```
4. Run the Server:
```python3 Server.py```
5. Run the Client:
```Python3 Client.py```

## Usage

1. Start the server by running `Server.py`.
2. Connect clients to the server by running `Client.py` on remote machines.
3. Access the dashboard at `http://server_ip:port/login.html`.
4. Login using the provided credentials. USERNAME : `admin` and PASSWORD : `admin9876`
5. Send commands to the connected clients via the dashboard interface.
6. View the output and status of executed commands.

## Features

- **Authentication:** Users can log in with a predefined username and password.
- **Dashboard:** Provides an overview of connected clients and their status.
- **Command Execution:** Allows users to send commands to connected clients.
- **Keylogger:** Captures keystrokes on client machines and saves them locally.
- **Persistence:** Enables persistence by adding the botnet to startup programs.
- **Screenshot:** Captures and sends screenshots of client desktops to the server.

## Credits

This project was created by @TheLeopard65. 

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
