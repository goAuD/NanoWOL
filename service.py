"""
NanoWOL - Service Module
Cross-platform service installation for automatic agent startup.
Part of the Nano Product Family.

Supported platforms:
- Windows: Task Scheduler (no admin required) or NSSM service
- Linux: systemd user service
- macOS: launchd user agent
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"

SERVICE_NAME = "NanoWOL-Agent"


def get_python_executable() -> str:
    """Get the path to the Python executable."""
    return sys.executable


def get_script_path() -> Path:
    """Get the path to nanowol.py."""
    return Path(__file__).parent / "nanowol.py"


# =============================================================================
# WINDOWS
# =============================================================================

def install_windows_task(mac_address: str, public_key: str = "./keys/public.pem") -> bool:
    """
    Install NanoWOL agent as a Windows Task Scheduler task.
    Runs at system startup, before user login.
    """
    if not IS_WINDOWS:
        return False
    
    python_exe = get_python_executable()
    script_path = get_script_path()
    
    # Create XML for task - S4U allows running without storing password
    import getpass
    username = getpass.getuser()
    
    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>NanoWOL Agent - Remote power control service</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{username}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{python_exe}"</Command>
      <Arguments>"{script_path}" agent --mac {mac_address} --public-key "{public_key}"</Arguments>
      <WorkingDirectory>{script_path.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
    
    # Write XML to temp file
    xml_path = Path.home() / ".nanowol_task.xml"
    xml_path.write_text(task_xml, encoding='utf-16')
    
    try:
        # Create the task - use encoding to handle non-English Windows
        result = subprocess.run(
            [
                "schtasks", "/create",
                "/tn", SERVICE_NAME,
                "/xml", str(xml_path),
                "/f"  # Force overwrite
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            logger.info(f"Windows task '{SERVICE_NAME}' installed successfully")
            return True
        else:
            logger.error(f"Failed to create task: {result.stderr}")
            return False
    finally:
        xml_path.unlink(missing_ok=True)


def uninstall_windows_task() -> bool:
    """Remove the Windows scheduled task."""
    if not IS_WINDOWS:
        return False
    
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", SERVICE_NAME, "/f"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode == 0:
        logger.info(f"Windows task '{SERVICE_NAME}' removed")
        return True
    else:
        logger.warning(f"Could not remove task: {result.stderr}")
        return False


def get_windows_task_status() -> dict:
    """Get the status of the Windows scheduled task."""
    if not IS_WINDOWS:
        return {"installed": False, "platform": "not windows"}
    
    result = subprocess.run(
        ["schtasks", "/query", "/tn", SERVICE_NAME, "/fo", "CSV", "/nh"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode == 0:
        return {"installed": True, "status": "ready", "output": result.stdout.strip()}
    else:
        return {"installed": False, "status": "not found"}


# =============================================================================
# LINUX (systemd)
# =============================================================================

def get_systemd_user_dir() -> Path:
    """Get the systemd user services directory."""
    return Path.home() / ".config" / "systemd" / "user"


def install_linux_service(mac_address: str, public_key: str = "./keys/public.pem") -> bool:
    """
    Install NanoWOL agent as a systemd user service.
    """
    if not IS_LINUX:
        return False
    
    service_dir = get_systemd_user_dir()
    service_dir.mkdir(parents=True, exist_ok=True)
    
    python_exe = get_python_executable()
    script_path = get_script_path()
    
    service_content = f'''[Unit]
Description=NanoWOL Agent - Remote power control service
After=network.target

[Service]
Type=simple
ExecStart={python_exe} {script_path} agent --mac {mac_address} --public-key {public_key}
WorkingDirectory={script_path.parent}
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
'''
    
    service_file = service_dir / f"{SERVICE_NAME.lower()}.service"
    service_file.write_text(service_content)
    
    # Enable and start
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    result = subprocess.run(["systemctl", "--user", "enable", SERVICE_NAME.lower()])
    
    if result.returncode == 0:
        logger.info(f"Linux service '{SERVICE_NAME}' installed")
        return True
    return False


def uninstall_linux_service() -> bool:
    """Remove the systemd user service."""
    if not IS_LINUX:
        return False
    
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME.lower()])
    subprocess.run(["systemctl", "--user", "disable", SERVICE_NAME.lower()])
    
    service_file = get_systemd_user_dir() / f"{SERVICE_NAME.lower()}.service"
    if service_file.exists():
        service_file.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"])
        logger.info(f"Linux service '{SERVICE_NAME}' removed")
        return True
    return False


def get_linux_service_status() -> dict:
    """Get the status of the systemd service."""
    if not IS_LINUX:
        return {"installed": False, "platform": "not linux"}
    
    result = subprocess.run(
        ["systemctl", "--user", "is-active", SERVICE_NAME.lower()],
        capture_output=True, text=True
    )
    
    service_file = get_systemd_user_dir() / f"{SERVICE_NAME.lower()}.service"
    installed = service_file.exists()
    
    return {
        "installed": installed,
        "status": result.stdout.strip() if installed else "not installed"
    }


# =============================================================================
# MACOS (launchd)
# =============================================================================

def get_launchd_dir() -> Path:
    """Get the launchd user agents directory."""
    return Path.home() / "Library" / "LaunchAgents"


def install_macos_service(mac_address: str, public_key: str = "./keys/public.pem") -> bool:
    """
    Install NanoWOL agent as a macOS launchd agent.
    """
    if not IS_MACOS:
        return False
    
    launch_dir = get_launchd_dir()
    launch_dir.mkdir(parents=True, exist_ok=True)
    
    python_exe = get_python_executable()
    script_path = get_script_path()
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nano.wol.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>agent</string>
        <string>--mac</string>
        <string>{mac_address}</string>
        <string>--public-key</string>
        <string>{public_key}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{script_path.parent}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
'''
    
    plist_file = launch_dir / "com.nano.wol.agent.plist"
    plist_file.write_text(plist_content)
    
    result = subprocess.run(["launchctl", "load", str(plist_file)])
    
    if result.returncode == 0:
        logger.info(f"macOS agent '{SERVICE_NAME}' installed")
        return True
    return False


def uninstall_macos_service() -> bool:
    """Remove the macOS launchd agent."""
    if not IS_MACOS:
        return False
    
    plist_file = get_launchd_dir() / "com.nano.wol.agent.plist"
    
    if plist_file.exists():
        subprocess.run(["launchctl", "unload", str(plist_file)])
        plist_file.unlink()
        logger.info(f"macOS agent '{SERVICE_NAME}' removed")
        return True
    return False


def get_macos_service_status() -> dict:
    """Get the status of the macOS launchd agent."""
    if not IS_MACOS:
        return {"installed": False, "platform": "not macos"}
    
    plist_file = get_launchd_dir() / "com.nano.wol.agent.plist"
    installed = plist_file.exists()
    
    if installed:
        result = subprocess.run(
            ["launchctl", "list", "com.nano.wol.agent"],
            capture_output=True, text=True
        )
        running = result.returncode == 0
        return {"installed": True, "status": "running" if running else "stopped"}
    
    return {"installed": False, "status": "not installed"}


# =============================================================================
# CROSS-PLATFORM API
# =============================================================================

def install_service(mac_address: str, public_key: str = "./keys/public.pem") -> bool:
    """Install the agent service on the current platform."""
    if IS_WINDOWS:
        return install_windows_task(mac_address, public_key)
    elif IS_LINUX:
        return install_linux_service(mac_address, public_key)
    elif IS_MACOS:
        return install_macos_service(mac_address, public_key)
    else:
        logger.error(f"Unsupported platform: {sys.platform}")
        return False


def uninstall_service() -> bool:
    """Uninstall the agent service on the current platform."""
    if IS_WINDOWS:
        return uninstall_windows_task()
    elif IS_LINUX:
        return uninstall_linux_service()
    elif IS_MACOS:
        return uninstall_macos_service()
    else:
        logger.error(f"Unsupported platform: {sys.platform}")
        return False


def get_service_status() -> dict:
    """Get the service status on the current platform."""
    if IS_WINDOWS:
        return get_windows_task_status()
    elif IS_LINUX:
        return get_linux_service_status()
    elif IS_MACOS:
        return get_macos_service_status()
    else:
        return {"installed": False, "platform": sys.platform, "error": "unsupported"}


def get_platform_name() -> str:
    """Get a friendly name for the current platform."""
    if IS_WINDOWS:
        return "Windows (Task Scheduler)"
    elif IS_LINUX:
        return "Linux (systemd)"
    elif IS_MACOS:
        return "macOS (launchd)"
    else:
        return f"Unknown ({sys.platform})"
