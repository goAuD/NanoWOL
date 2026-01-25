# NanoWOL

Secure Remote Wake on LAN and Shutdown Controller

NanoWOL is a lightweight command line and web tool for remote PC power management with RSA authentication. It is part of the Nano Product Family.

![Python](https://img.shields.io/badge/Made%20with-Python-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

![NanoWOL Screenshot](nanowol.png)

## Features

1. Secure authentication with RSA 2048 signatures for shutdown commands
2. Wake on LAN magic packets
3. Remote shutdown with optional port blocking
4. Service mode for automatic startup
5. Web UI control panel
6. Command line interface for scripts
7. Cross platform support for Windows, Linux, and macOS
8. Modular design across crypto, WOL, agent, service, and web UI modules
9. Unit tests for crypto, WOL, and service functionality

Note: primarily tested on Windows. Linux and macOS should work but feedback is welcome.

## Use cases

### IT admin and office management

Deploy the NanoWOL agent on workstations so an admin can wake or shut down machines remotely. This saves time and reduces power usage.

### Home lab and server room

Wake a NAS or home server before access and shut it down after a backup job completes.

### Remote work

If a home PC is left running, shut it down remotely. If a file is needed, wake the machine, access it, then shut it down.

### Energy saving

Schedule regular shutdowns and only wake systems when needed.

## Requirements

1. Python 3.8 or later
2. Dependencies: click, flask, cryptography, requests

## Installation

1. Clone the repository

   ```bash
   git clone https://github.com/goAuD/NanoWOL.git
   ```
2. Open the project folder

   ```bash
   cd NanoWOL
   ```
3. Install dependencies using pip and the requirements file

## Quick start

### Step 1: Generate RSA keys (on any machine, copy to both)

```bash
python nanowol.py keygen
```

This creates `keys/private.pem` and `keys/public.pem`. The private key stays on the controller, the public key goes to the target PC.

### Step 2: Start the agent on the TARGET PC

The target PC is the machine you want to wake/shutdown remotely.

```bash
python nanowol.py agent --mac AA:BB:CC:DD:EE:FF --public-key ./keys/public.pem
```

Replace `AA:BB:CC:DD:EE:FF` with the target PC's MAC address.
Find it with `ipconfig /all` (Windows) or `ip link` (Linux).

### Step 3: Control from the CONTROLLER machine

The controller is where you send commands from.

**Option A: Web UI (recommended)**

```bash
python nanowol.py webui --target http://TARGET_IP:5000 --mac AA:BB:CC:DD:EE:FF
```

If you omit `--password`, a secure random password is generated and printed to the console.

Then open `http://localhost:5050` in your browser.

**Option B: CLI commands**

Wake a machine:
```bash
python nanowol.py wake --mac AA:BB:CC:DD:EE:FF
```

Shutdown a machine:
```bash
python nanowol.py shutdown --target http://TARGET_IP:5000
```

### Step 4 (optional): Install as service on TARGET PC

```bash
python nanowol.py install-service --mac AA:BB:CC:DD:EE:FF
```

This starts the agent automatically on boot (Windows) or login (Linux/macOS).

### Example with real values

Target PC:
- IP: `192.168.0.50`
- MAC: `1C:69:7A:AB:CD:EF`

On target PC:
```bash
python nanowol.py agent --mac 1C:69:7A:AB:CD:EF
```

On controller:
```bash
python nanowol.py webui --target http://192.168.0.50:5000 --mac 1C:69:7A:AB:CD:EF --password secret123
```

## Project structure

1. nanowol.py CLI entry point
2. crypto.py RSA key operations
3. wol.py Wake on LAN logic
4. agent.py Agent Flask server
5. webui.py Web UI Flask server
6. service.py Cross platform service installation
7. templates index.html Web UI template
8. test_nanowol.py Unit tests
9. requirements.txt Dependencies

## Service installation

The agent can install itself as a user service on Linux and macOS, and as a scheduled task on Windows. User services run when the user session is active. To start at boot without login on Linux, enable user lingering with the system login manager. On macOS, starting at boot without login requires a system launch daemon, which is not covered here.

## Running tests

Run pytest in your Python environment against test_nanowol.py.

## Security

1. RSA 2048 signatures for shutdown commands
2. Password protected Web UI
3. Optional firewall port blocking after shutdown
4. Self hosted with no external services required

Note: NanoWOL is designed for LAN use. For internet access, use a VPN solution.

## Linux and macOS operational notes

This section explains how to run the agent reliably on Linux and macOS, including WSL usage.

1. Shutdown permissions
   On Linux and macOS the shutdown command requires elevated permissions. Use a sudoers rule that allows only the shutdown command without a password.

   ```bash
   sudo visudo
   ```

   ```
   youruser ALL=NOPASSWD:/sbin/shutdown
   ```

2. Service behavior on Linux
   The Linux service is installed as a user service. It runs when your user session is active. To start at boot without login, enable user lingering for your account using the system login manager.

3. Service behavior on macOS
   The macOS agent runs as a launchd user agent. It starts when you log in to your user session. To run at boot without login you need a system launch daemon, which is a different setup.

4. WSL behavior
   WSL is not a full Linux boot environment. Service managers may behave differently and shutdown will not power off Windows. Use WSL for development or testing.

## FAQ

### Why do I need NanoWOL

A local shutdown command works only when you are at the machine. NanoWOL is for remote power management and secure authentication, with the ability to wake a machine that is fully off.

### What is Wake on LAN

Wake on LAN is a hardware feature that allows a powered off PC to start when it receives a special magic packet on the network. The network adapter listens for that packet while the system is off.

Requirements include WOL enabled in BIOS, wake on magic packet enabled in the network adapter, an Ethernet connection, and power to the machine.

### Why not use SSH and a shutdown command

SSH gives full shell access and requires credentials. NanoWOL limits the agent to wake and shutdown only, and uses signed commands so a password is not transmitted.

### Is this a security risk

NanoWOL uses RSA 2048 signatures for shutdown commands. The private key stays on the controller. The agent accepts only requests signed by the matching key. This reduces the attack surface compared to a general remote shell.

## Part of Nano Product Family

This tool uses the [Nano Design System](https://github.com/goAuD/NanoServer/blob/main/DESIGN_SYSTEM.md) for consistent styling across lightweight developer tools.

## License

MIT License
