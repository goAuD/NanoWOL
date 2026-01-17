# NanoWOL

**Secure Remote Wake-on-LAN & Shutdown Controller**

NanoWOL is a lightweight CLI/Web tool for remote PC power management with RSA authentication. Part of the **Nano Product Family**.

![Python](https://img.shields.io/badge/Made%20with-Python-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

![NanoWOL Screenshot](nanowol.png)

## Features

* **Secure Authentication:** RSA-2048 signed commands prevent unauthorized shutdowns
* **Wake-on-LAN:** Send magic packets to wake remote machines
* **Remote Shutdown:** Signed shutdown commands with optional port blocking
* **Web UI:** Cyberpunk-styled control panel accessible from any browser
* **CLI Tool:** Full command-line interface for scripting
* **Modular:** Clean separation into crypto, WOL, agent, and webui modules
* **Unit Tested:** Comprehensive test suite for core functionality

> **Note:** Primarily tested on Windows. Linux should work but feedback welcome!

## Requirements

* Python 3.8+
* Dependencies: `click`, `flask`, `cryptography`, `requests`

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/NanoWOL.git
cd NanoWOL

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Generate Keys
```bash
python NanoWOL.py keygen
```

### 2. Start Agent (on target PC)
```bash
# Copy public.pem to target PC, then:
python NanoWOL.py agent --mac AA:BB:CC:DD:EE:FF --public-key ./keys/public.pem
```

### 3. Start Web UI (on controller)
```bash
python NanoWOL.py webui --target http://192.168.0.50:5000
```

### 4. Or use CLI commands
```bash
# Wake
python NanoWOL.py wake --target http://192.168.0.50:5000

# Shutdown
python NanoWOL.py shutdown --target http://192.168.0.50:5000
```

## Project Structure (v1.1.0)

```
NanoWOL/
├── NanoWOL.py        # CLI entry point
├── crypto.py          # RSA key operations
├── wol.py             # Wake-on-LAN logic
├── agent.py           # Agent Flask server
├── webui.py           # Web UI Flask server
├── templates/
│   └── index.html     # Cyberpunk web template
├── test_NanoWOL.py   # Unit tests
└── requirements.txt   # Dependencies
```

## Running Tests

```bash
python test_NanoWOL.py
# or
python -m pytest test_NanoWOL.py -v
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

