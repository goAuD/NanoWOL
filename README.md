# NanoWOL

**Secure Remote Wake-on-LAN & Shutdown Controller**

NanoWOL is a lightweight CLI/Web tool for remote PC power management with RSA authentication. Part of the **Nano Product Family**.

![Python](https://img.shields.io/badge/Made%20with-Python-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

![NanoWOL Screenshot](nanowol.png)

## Features

* **Secure Authentication:** RSA-2048 signed commands prevent unauthorized shutdowns
* **Wake-on-LAN:** Send magic packets to wake remote machines
* **Remote Shutdown:** Signed shutdown commands with optional port blocking
* **Auto-Start Service:** Agent can run as a system service (starts on boot, no login required)
* **Web UI:** Cyberpunk-styled control panel accessible from any browser
* **CLI Tool:** Full command-line interface for scripting
* **Cross-Platform:** Windows (Task Scheduler), Linux (systemd), macOS (launchd)
* **Modular:** Clean separation into crypto, WOL, agent, service, and webui modules
* **Unit Tested:** 12 tests covering crypto, WOL, and service functionality

> **Note:** Primarily tested on Windows. Linux/macOS should work but feedback welcome!

## Requirements

* Python 3.8+
* Dependencies: `click`, `flask`, `cryptography`, `requests`

## Installation

```bash
# Clone repository
git clone https://github.com/goAuD/NanoWOL.git
cd NanoWOL

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Generate Keys
```bash
python nanowol.py keygen
```

### 2. Install as Service (Recommended)
```bash
# On target PC - installs agent to start on boot (no login required)
python nanowol.py install-service --mac AA:BB:CC:DD:EE:FF
```

### 3. Or Start Agent Manually
```bash
# Copy public.pem to target PC, then:
python nanowol.py agent --mac AA:BB:CC:DD:EE:FF --public-key ./keys/public.pem
```

### 4. Start Web UI (on controller)
```bash
python nanowol.py webui --target http://192.168.0.50:5000
```

### 5. CLI Commands
```bash
# Wake
python nanowol.py wake --target http://192.168.0.50:5000

# Shutdown
python nanowol.py shutdown --target http://192.168.0.50:5000

# Check service status
python nanowol.py service-status
```

## Project Structure (v1.2.0)

```
NanoWOL/
├── nanowol.py         # CLI entry point
├── crypto.py          # RSA key operations
├── wol.py             # Wake-on-LAN logic
├── agent.py           # Agent Flask server
├── webui.py           # Web UI Flask server
├── service.py         # Cross-platform service installation
├── templates/
│   └── index.html     # Cyberpunk web template
├── test_nanowol.py    # Unit tests (12 tests)
└── requirements.txt   # Dependencies
```

## Service Installation

NanoWOL can install itself as a system service to auto-start on boot:

| Platform | Method | Requires Login |
|----------|--------|----------------|
| Windows | Task Scheduler (Boot trigger) | No |
| Linux | systemd user service | No |
| macOS | launchd user agent | No |

```bash
# Install
python nanowol.py install-service --mac AA:BB:CC:DD:EE:FF

# Uninstall
python nanowol.py uninstall-service

# Check status
python nanowol.py service-status
```

## Running Tests

```bash
python test_nanowol.py
# or
python -m pytest test_nanowol.py -v
```

## Security

* RSA-2048 signatures for shutdown commands
* Password-protected Web UI
* Optional firewall port blocking after shutdown
* No cloud, fully offline capable

## Part of Nano Product Family

This tool uses the [Nano Design System](https://github.com/goAuD/NanoServer/blob/main/DESIGN_SYSTEM.md) for consistent styling across lightweight developer tools.

## License

MIT License
