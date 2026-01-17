#!/usr/bin/env python3
"""
NanoWOL – Secure Remote Wake-on-LAN & Shutdown Controller
Version 1.2.0 | Part of the Nano Product Family

A modular CLI tool for remote PC power management with RSA authentication.

Commands:
    keygen          - Generate RSA key pair
    agent           - Start the agent server on target PC
    wake            - Send Wake-on-LAN magic packet
    shutdown        - Send signed shutdown command
    webui           - Start the web control panel
    install-service - Install agent as system service
    uninstall-service - Remove agent service
    service-status  - Check service status

Usage:
    python nanowol.py keygen
    python nanowol.py agent --mac AA:BB:CC:DD:EE:FF
    python nanowol.py install-service --mac AA:BB:CC:DD:EE:FF
    python nanowol.py wake --target http://192.168.0.50:5000
    python nanowol.py shutdown --target http://192.168.0.50:5000
    python nanowol.py webui --target http://192.168.0.50:5000
"""

import sys
import logging
from pathlib import Path

import click

# Import from modules
from crypto import generate_key_pair, load_private_key, sign_message
from wol import send_wol_packet
from agent import create_agent_app, DEFAULT_AGENT_PORT
from webui import create_webui_app, generate_password, DEFAULT_WEBUI_PORT
from service import install_service, uninstall_service, get_service_status, get_platform_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VERSION = "1.2.0"


# =============================================================================
# CLI COMMANDS
# =============================================================================

@click.group()
@click.version_option(version=VERSION, prog_name="NanoWOL")
def cli():
    """
    NanoWOL – Secure Remote Wake-on-LAN & Shutdown Controller
    
    A tool for remote PC power management with RSA authentication.
    Part of the Nano Product Family.
    """
    pass


@cli.command()
@click.option("--keys-dir", default="./keys", help="Directory to store keys")
@click.option("--force", is_flag=True, help="Overwrite existing keys")
def keygen(keys_dir: str, force: bool):
    """Generate RSA-2048 key pair for authentication."""
    keys_path = Path(keys_dir)
    private_path = keys_path / "private.pem"
    
    if private_path.exists() and not force:
        click.echo(click.style("Warning: Keys already exist. Use --force to overwrite.", fg="yellow"))
        return
    
    click.echo("Generating RSA-2048 key pair...")
    private_path, public_path = generate_key_pair(keys_path)
    
    click.echo(click.style("Key pair generated successfully!", fg="green"))
    click.echo(f"  Private key: {private_path}")
    click.echo(f"  Public key:  {public_path}")
    click.echo()
    click.echo(click.style("IMPORTANT:", fg="yellow"))
    click.echo("  - Keep the private key SECRET (controller side)")
    click.echo("  - Copy the public key to the target PC (agent side)")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=DEFAULT_AGENT_PORT, help="Port to listen on")
@click.option("--mac", required=True, help="MAC address for WOL (format: AA:BB:CC:DD:EE:FF)")
@click.option("--public-key", default="./keys/public.pem", help="Path to public key")
@click.option("--shutdown-delay", default=5, help="Delay before shutdown in seconds")
def agent(host: str, port: int, mac: str, public_key: str, shutdown_delay: int):
    """Start the agent server on the target PC."""
    public_key_path = Path(public_key)
    
    if not public_key_path.exists():
        click.echo(click.style(f"Error: Public key not found: {public_key}", fg="red"))
        click.echo("  Run 'nanowol keygen' first, then copy public.pem to this machine.")
        sys.exit(1)
    
    click.echo(click.style("NanoWOL Agent", fg="cyan", bold=True))
    click.echo(f"  MAC Address:    {mac}")
    click.echo(f"  Public Key:     {public_key_path}")
    click.echo(f"  Shutdown Delay: {shutdown_delay}s")
    click.echo()
    click.echo(f"Starting server on http://{host}:{port}")
    click.echo(click.style("Press Ctrl+C to stop", fg="yellow"))
    click.echo()
    
    app = create_agent_app(mac, public_key_path, shutdown_delay)
    app.run(host=host, port=port, debug=False)


@cli.command()
@click.option("--target", required=True, help="Agent URL (e.g., http://192.168.0.50:5000)")
def wake(target: str):
    """Send Wake-on-LAN request to the agent."""
    import requests as req
    
    click.echo(f"Sending WOL request to {target}...")
    
    try:
        resp = req.post(f"{target}/wol", timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            click.echo(click.style(f"Success: {result.get('status', 'OK')}", fg="green"))
        else:
            result = resp.json()
            click.echo(click.style(f"Error: {result.get('error', 'Failed')}", fg="red"))
            
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--target", required=True, help="Agent URL (e.g., http://192.168.0.50:5000)")
@click.option("--private-key", default="./keys/private.pem", help="Path to private key")
@click.option("--close-port", is_flag=True, help="Close agent port after shutdown")
def shutdown(target: str, private_key: str, close_port: bool):
    """Send signed shutdown command to the agent."""
    import requests as req
    
    private_key_path = Path(private_key)
    
    if not private_key_path.exists():
        click.echo(click.style(f"Error: Private key not found: {private_key}", fg="red"))
        click.echo("  Run 'nanowol keygen' first.")
        sys.exit(1)
    
    click.echo(f"Sending shutdown command to {target}...")
    
    try:
        key = load_private_key(private_key_path)
        signature = sign_message(b"shutdown", key)
        
        resp = req.post(
            f"{target}/shutdown",
            json={"signature": signature, "close_port": close_port},
            timeout=10
        )
        
        if resp.status_code == 200:
            result = resp.json()
            click.echo(click.style(f"Success: {result.get('status', 'OK')}", fg="green"))
        else:
            result = resp.json()
            click.echo(click.style(f"Error: {result.get('error', 'Failed')}", fg="red"))
            
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=DEFAULT_WEBUI_PORT, help="Port to listen on")
@click.option("--target", required=True, help="Agent URL (e.g., http://192.168.0.50:5000)")
@click.option("--private-key", default="./keys/private.pem", help="Path to private key")
@click.option("--password", envvar="NANOWOL_PASSWORD", help="Access password (or set NANOWOL_PASSWORD env var)")
def webui(host: str, port: int, target: str, private_key: str, password: str):
    """Start the web control panel."""
    private_key_path = Path(private_key)
    
    if not password:
        password = generate_password()
        click.echo(click.style("Warning: No password set. Generated temporary password:", fg="yellow"))
        click.echo(click.style(f"   {password}", fg="cyan", bold=True))
        click.echo()
    
    if not private_key_path.exists():
        click.echo(click.style(f"Warning: Private key not found: {private_key}", fg="yellow"))
        click.echo("  Shutdown commands will not work. Run 'nanowol keygen' first.")
        click.echo()
    
    click.echo(click.style("NanoWOL Web UI", fg="cyan", bold=True))
    click.echo(f"  Target Agent: {target}")
    click.echo(f"  Private Key:  {private_key_path}")
    click.echo()
    click.echo(f"Starting web UI on http://{host}:{port}")
    click.echo(click.style("Press Ctrl+C to stop", fg="yellow"))
    click.echo()
    
    app = create_webui_app(target, private_key_path, password)
    app.run(host=host, port=port, debug=False)


# =============================================================================
# SERVICE COMMANDS
# =============================================================================

@cli.command("install-service")
@click.option("--mac", required=True, help="MAC address for WOL (format: AA:BB:CC:DD:EE:FF)")
@click.option("--public-key", default="./keys/public.pem", help="Path to public key")
def install_service_cmd(mac: str, public_key: str):
    """Install agent as a system service (auto-start on boot)."""
    click.echo(click.style("NanoWOL Service Installer", fg="cyan", bold=True))
    click.echo(f"  Platform: {get_platform_name()}")
    click.echo(f"  MAC:      {mac}")
    click.echo()
    
    public_key_path = Path(public_key)
    if not public_key_path.exists():
        click.echo(click.style(f"Error: Public key not found: {public_key}", fg="red"))
        click.echo("  Run 'nanowol keygen' first.")
        sys.exit(1)
    
    click.echo("Installing service...")
    if install_service(mac, public_key):
        click.echo(click.style("Service installed successfully!", fg="green"))
        click.echo()
        click.echo("The agent will now start automatically on system boot.")
        click.echo("Use 'nanowol service-status' to check the status.")
    else:
        click.echo(click.style("Failed to install service.", fg="red"))
        sys.exit(1)


@cli.command("uninstall-service")
def uninstall_service_cmd():
    """Remove the agent system service."""
    click.echo(click.style("NanoWOL Service Uninstaller", fg="cyan", bold=True))
    click.echo(f"  Platform: {get_platform_name()}")
    click.echo()
    
    click.echo("Removing service...")
    if uninstall_service():
        click.echo(click.style("Service removed successfully!", fg="green"))
    else:
        click.echo(click.style("Service not found or could not be removed.", fg="yellow"))


@cli.command("service-status")
def service_status_cmd():
    """Check the status of the agent service."""
    click.echo(click.style("NanoWOL Service Status", fg="cyan", bold=True))
    click.echo(f"  Platform: {get_platform_name()}")
    click.echo()
    
    status = get_service_status()
    
    if status.get("installed"):
        click.echo(click.style(f"  Status: {status.get('status', 'unknown')}", fg="green"))
    else:
        click.echo(click.style("  Status: Not installed", fg="yellow"))
        click.echo()
        click.echo("Use 'nanowol install-service --mac XX:XX:XX:XX:XX:XX' to install.")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    cli()


