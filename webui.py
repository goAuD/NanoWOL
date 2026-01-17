"""
NanoWOL - Web UI Server Module
Flask server providing a web control panel for remote power management.
Part of the Nano Product Family.
"""

import logging
import secrets
from pathlib import Path
from flask import Flask, request, render_template

from crypto import load_private_key, sign_message
from wol import send_wol_packet

logger = logging.getLogger(__name__)

DEFAULT_WEBUI_PORT = 5050
VERSION = "1.2.0"


def create_webui_app(agent_url: str, private_key_path: Path, password: str, target_mac: str = None) -> Flask:
    """
    Create Flask app for the web control panel.
    
    This server provides a web interface to:
    - Send wake commands DIRECTLY (magic packet via UDP broadcast)
    - Send signed shutdown commands to the agent
    
    Args:
        agent_url: URL of the agent server (for shutdown)
        private_key_path: Path to RSA private key for signing
        password: Access password for the web UI
        target_mac: MAC address for WOL (sends directly, not through agent)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder='templates')
    
    # Load private key for signing shutdown commands
    private_key = None
    if private_key_path.exists():
        private_key = load_private_key(private_key_path)
    
    @app.route("/", methods=["GET", "POST"])
    def index():
        message = ""
        error = False
        
        if request.method == "POST":
            # Verify password
            submitted_password = request.form.get("password", "")
            if submitted_password != password:
                return render_template("index.html", message="Invalid password", error=True)
            
            action = request.form.get("action")
            close_port = "close_port" in request.form
            
            try:
                if action == "wake":
                    # Send WOL packet DIRECTLY from this machine
                    if not target_mac:
                        raise ValueError("MAC address not configured. Use --mac option.")
                    
                    send_wol_packet(target_mac)
                    message = f"Wake-on-LAN packet sent to {target_mac}"
                    logger.info(f"WOL packet sent to {target_mac}")
                    
                elif action == "shutdown":
                    import requests as req
                    
                    if not private_key:
                        raise ValueError("Private key not found. Run 'nanowol keygen' first.")
                    
                    signature = sign_message(b"shutdown", private_key)
                    resp = req.post(
                        f"{agent_url}/shutdown",
                        json={"signature": signature, "close_port": close_port},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        message = f"Success: {result.get('status', 'OK')}"
                    else:
                        error = True
                        result = resp.json()
                        message = f"Error: {result.get('error', 'Unknown error')}"
                else:
                    raise ValueError("Invalid action")
                    
            except Exception as e:
                error = True
                message = f"Error: {str(e)}"
                logger.error(f"WebUI action failed: {e}")
        
        return render_template("index.html", message=message, error=error)
    
    return app


def generate_password() -> str:
    """Generate a secure random password."""
    return secrets.token_urlsafe(16)


