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

logger = logging.getLogger(__name__)

DEFAULT_WEBUI_PORT = 5050
VERSION = "1.1.0"


def create_webui_app(agent_url: str, private_key_path: Path, password: str) -> Flask:
    """
    Create Flask app for the web control panel.
    
    This server provides a web interface to:
    - Send wake commands to the agent
    - Send signed shutdown commands
    
    Args:
        agent_url: URL of the agent server
        private_key_path: Path to RSA private key for signing
        password: Access password for the web UI
        
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
                import requests as req
                
                if action == "wake":
                    resp = req.post(f"{agent_url}/wol", timeout=10)
                    
                elif action == "shutdown":
                    if not private_key:
                        raise ValueError("Private key not found. Run 'NanoWOL keygen' first.")
                    
                    signature = sign_message(b"shutdown", private_key)
                    resp = req.post(
                        f"{agent_url}/shutdown",
                        json={"signature": signature, "close_port": close_port},
                        timeout=10
                    )
                else:
                    raise ValueError("Invalid action")
                
                if resp.status_code == 200:
                    result = resp.json()
                    message = f"Success: {result.get('status', 'OK')}"
                else:
                    error = True
                    result = resp.json()
                    message = f"Error: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                error = True
                message = f"Error: {str(e)}"
                logger.error(f"WebUI action failed: {e}")
        
        return render_template("index.html", message=message, error=error)
    
    return app


def generate_password() -> str:
    """Generate a secure random password."""
    return secrets.token_urlsafe(16)

