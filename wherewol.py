#!/usr/bin/env python3
"""
WhereWOL – Secure Remote Wake-on-LAN & Shutdown Controller

A single-file CLI tool for remote PC power management with RSA authentication.

Commands:
    keygen   - Generate RSA key pair
    agent    - Start the agent server on target PC
    wake     - Send Wake-on-LAN magic packet
    shutdown - Send signed shutdown command
    webui    - Start the web control panel

Usage:
    python wherewol.py keygen
    python wherewol.py agent --mac AA:BB:CC:DD:EE:FF
    python wherewol.py wake --target http://192.168.0.50:5000
    python wherewol.py shutdown --target http://192.168.0.50:5000
    python wherewol.py webui --port 5050
"""

import os
import sys
import socket
import struct
import subprocess
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

import click
from flask import Flask, request, jsonify, render_template_string
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_KEYS_DIR = Path("./keys")
DEFAULT_PRIVATE_KEY = DEFAULT_KEYS_DIR / "private.pem"
DEFAULT_PUBLIC_KEY = DEFAULT_KEYS_DIR / "public.pem"
DEFAULT_AGENT_PORT = 5000
DEFAULT_WEBUI_PORT = 5050

# =============================================================================
# CYBERPUNK WEB UI TEMPLATE
# =============================================================================

WEBUI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhereWOL Control Panel</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: rgba(20, 20, 35, 0.8);
            --cyan: #00f0ff;
            --cyan-dim: #00a0aa;
            --magenta: #ff00aa;
            --green: #00ff88;
            --red: #ff4466;
            --yellow: #ffcc00;
            --text-primary: #e8e8f0;
            --text-secondary: #8888aa;
            --border-glow: 0 0 20px rgba(0, 240, 255, 0.3);
            --button-glow: 0 0 30px rgba(0, 240, 255, 0.4);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        /* Animated grid background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px),
                linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: gridMove 20s linear infinite;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes gridMove {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }

        /* Gradient overlay */
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(ellipse at center, transparent 0%, var(--bg-primary) 70%);
            pointer-events: none;
            z-index: 1;
        }

        .container {
            position: relative;
            z-index: 10;
            width: 100%;
            max-width: 480px;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--cyan), var(--magenta));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(0, 240, 255, 0.5);
            letter-spacing: 0.1em;
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 0.85rem;
            color: var(--text-secondary);
            letter-spacing: 0.3em;
            text-transform: uppercase;
        }

        /* Main card */
        .card {
            background: var(--bg-card);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 16px;
            padding: 32px;
            backdrop-filter: blur(20px);
            box-shadow: var(--border-glow);
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--cyan), var(--magenta), transparent);
        }

        /* Auth section */
        .auth-section {
            margin-bottom: 28px;
        }

        .auth-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.75rem;
            color: var(--cyan);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 12px;
        }

        .auth-label svg {
            width: 16px;
            height: 16px;
        }

        .password-input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        }

        .password-input:focus {
            outline: none;
            border-color: var(--cyan);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }

        .password-input::placeholder {
            color: var(--text-secondary);
        }

        /* Action buttons */
        .actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }

        .btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.1), rgba(255, 0, 170, 0.05));
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn:hover {
            border-color: var(--cyan);
            box-shadow: var(--button-glow);
            transform: translateY(-2px);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-icon {
            width: 32px;
            height: 32px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .btn-icon svg {
            width: 100%;
            height: 100%;
        }

        .btn-wake .btn-icon { color: var(--green); }
        .btn-wake .btn-icon svg { fill: var(--green); stroke: var(--green); }
        .btn-shutdown .btn-icon { color: var(--red); }
        .btn-shutdown .btn-icon svg { stroke: var(--red); }

        .btn-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .btn-wake:hover {
            border-color: var(--green);
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
        }

        .btn-shutdown:hover {
            border-color: var(--red);
            box-shadow: 0 0 30px rgba(255, 68, 102, 0.3);
        }

        /* Options */
        .options {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            margin-bottom: 24px;
        }

        .checkbox {
            width: 20px;
            height: 20px;
            accent-color: var(--cyan);
            cursor: pointer;
        }

        .options label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            cursor: pointer;
        }

        /* Toast messages */
        .toast {
            display: none;
            padding: 16px 20px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            text-align: center;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .toast.success {
            display: block;
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid var(--green);
            color: var(--green);
        }

        .toast.error {
            display: block;
            background: rgba(255, 68, 102, 0.15);
            border: 1px solid var(--red);
            color: var(--red);
        }

        /* Footer */
        .footer {
            text-align: center;
            margin-top: 24px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .footer a {
            color: var(--cyan-dim);
            text-decoration: none;
        }

        .footer a:hover {
            color: var(--cyan);
        }

        /* Status indicator */
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
            margin-right: 6px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Responsive */
        @media (max-width: 500px) {
            .logo {
                font-size: 1.8rem;
            }
            .card {
                padding: 24px;
            }
            .actions {
                grid-template-columns: 1fr;
            }
            .btn {
                flex-direction: row;
                gap: 12px;
                padding: 18px 20px;
            }
            .btn-icon {
                font-size: 1.5rem;
                margin: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1 class="logo">WHEREWOL</h1>
            <p class="subtitle">Remote Power Control</p>
        </header>

        <main class="card">
            <form method="POST" id="controlForm">
                <div class="auth-section">
                    <label class="auth-label">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0110 0v4"/>
                        </svg>
                        Authentication
                    </label>
                    <input type="password" name="password" class="password-input" 
                           placeholder="Enter access password" required>
                </div>

                <div class="actions">
                    <button type="submit" name="action" value="wake" class="btn btn-wake">
                        <span class="btn-icon"><svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg></span>
                        <span class="btn-label">Wake Up</span>
                    </button>
                    <button type="submit" name="action" value="shutdown" class="btn btn-shutdown">
                        <span class="btn-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M12 2v10M18.4 6.6a9 9 0 1 1-12.8 0"/></svg></span>
                        <span class="btn-label">Shutdown</span>
                    </button>
                </div>

                <div class="options">
                    <input type="checkbox" name="close_port" id="closePort" class="checkbox">
                    <label for="closePort">Close port after shutdown</label>
                </div>

                {% if message %}
                <div class="toast {{ 'error' if error else 'success' }}">
                    {{ message }}
                </div>
                {% endif %}
            </form>
        </main>

        <footer class="footer">
            <span class="status-dot"></span>
            WhereWOL v1.0.0 • 
            <a href="https://github.com/yourusername/wherewol" target="_blank">GitHub</a>
        </footer>
    </div>
</body>
</html>
"""

# =============================================================================
# CRYPTO UTILITIES
# =============================================================================

def generate_key_pair(keys_dir: Path = DEFAULT_KEYS_DIR) -> tuple[Path, Path]:
    """Generate RSA-2048 key pair for signing/verification."""
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    private_path = keys_dir / "private.pem"
    public_path = keys_dir / "public.pem"
    
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    
    # Restrict private key permissions on Unix
    if os.name != 'nt':
        os.chmod(private_path, 0o600)
    
    return private_path, public_path


def load_private_key(path: Path = DEFAULT_PRIVATE_KEY):
    """Load private key from PEM file."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key(path: Path = DEFAULT_PUBLIC_KEY):
    """Load public key from PEM file."""
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def sign_message(message: bytes, private_key) -> str:
    """Sign a message with the private key, return hex-encoded signature."""
    signature = private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return signature.hex()


def verify_signature(message: bytes, signature_hex: str, public_key) -> bool:
    """Verify a signature against a message using the public key."""
    try:
        signature = bytes.fromhex(signature_hex)
        public_key.verify(
            signature,
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


# =============================================================================
# WAKE-ON-LAN
# =============================================================================

def send_wol_packet(mac_address: str, broadcast: str = "255.255.255.255", port: int = 9):
    """Send a Wake-on-LAN magic packet."""
    # Clean and validate MAC address
    mac = mac_address.replace(":", "").replace("-", "").upper()
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address: {mac_address}")
    
    # Build magic packet: 6 bytes of 0xFF + MAC repeated 16 times
    mac_bytes = bytes.fromhex(mac)
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    # Send via UDP broadcast
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast, port))


# =============================================================================
# AGENT SERVER
# =============================================================================

def create_agent_app(mac_address: str, public_key_path: Path, shutdown_delay: int = 5):
    """Create Flask app for the agent server."""
    app = Flask(__name__)
    
    # Load public key for signature verification
    public_key = load_public_key(public_key_path)
    
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        })
    
    @app.route("/wol", methods=["POST"])
    def wol():
        """Send Wake-on-LAN packet (to wake another machine from this agent)."""
        try:
            send_wol_packet(mac_address)
            return jsonify({"status": "WOL packet sent", "mac": mac_address}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        """Initiate shutdown with RSA signature verification."""
        try:
            data = request.get_json() or {}
            signature = data.get("signature", "")
            close_port = data.get("close_port", False)
            
            # Verify signature
            message = b"shutdown"
            if not verify_signature(message, signature, public_key):
                return jsonify({"error": "Invalid signature"}), 403
            
            # Optional: block the agent port after shutdown
            if close_port:
                port = request.environ.get('SERVER_PORT', DEFAULT_AGENT_PORT)
                if sys.platform == "win32":
                    os.system(f'netsh advfirewall firewall add rule name="BlockWhereWOL" dir=in action=block protocol=TCP localport={port}')
            
            # Initiate shutdown
            if sys.platform == "win32":
                subprocess.Popen(f"shutdown /s /t {shutdown_delay}", shell=True)
            else:
                subprocess.Popen(f"shutdown -h +{shutdown_delay // 60 or 1}", shell=True)
            
            return jsonify({"status": f"Shutdown initiated (delay: {shutdown_delay}s)"}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app


# =============================================================================
# WEB UI SERVER
# =============================================================================

def create_webui_app(agent_url: str, private_key_path: Path, password: str):
    """Create Flask app for the web control panel."""
    app = Flask(__name__)
    
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
                return render_template_string(WEBUI_TEMPLATE, message="Invalid password", error=True)
            
            action = request.form.get("action")
            close_port = "close_port" in request.form
            
            try:
                import requests as req
                
                if action == "wake":
                    resp = req.post(f"{agent_url}/wol", timeout=10)
                    
                elif action == "shutdown":
                    if not private_key:
                        raise ValueError("Private key not found. Run 'wherewol keygen' first.")
                    
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
                    message = f"✓ {result.get('status', 'Success')}"
                else:
                    error = True
                    result = resp.json()
                    message = f"✗ {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                error = True
                message = f"✗ {str(e)}"
        
        return render_template_string(WEBUI_TEMPLATE, message=message, error=error)
    
    return app


# =============================================================================
# CLI COMMANDS
# =============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="WhereWOL")
def cli():
    """
    ⚡ WhereWOL – Secure Remote Wake-on-LAN & Shutdown Controller
    
    A tool for remote PC power management with RSA authentication.
    """
    pass


@cli.command()
@click.option("--keys-dir", default="./keys", help="Directory to store keys")
@click.option("--force", is_flag=True, help="Overwrite existing keys")
def keygen(keys_dir: str, force: bool):
    """Generate RSA-2048 key pair for authentication."""
    keys_path = Path(keys_dir)
    private_path = keys_path / "private.pem"
    public_path = keys_path / "public.pem"
    
    if private_path.exists() and not force:
        click.echo(click.style("⚠ Keys already exist. Use --force to overwrite.", fg="yellow"))
        return
    
    click.echo("🔐 Generating RSA-2048 key pair...")
    private_path, public_path = generate_key_pair(keys_path)
    
    click.echo(click.style("✓ Key pair generated successfully!", fg="green"))
    click.echo(f"  Private key: {private_path}")
    click.echo(f"  Public key:  {public_path}")
    click.echo()
    click.echo(click.style("⚠ IMPORTANT:", fg="yellow"))
    click.echo("  • Keep the private key SECRET (controller side)")
    click.echo("  • Copy the public key to the target PC (agent side)")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5000, help="Port to listen on")
@click.option("--mac", required=True, help="MAC address for WOL (format: AA:BB:CC:DD:EE:FF)")
@click.option("--public-key", default="./keys/public.pem", help="Path to public key")
@click.option("--shutdown-delay", default=5, help="Delay before shutdown in seconds")
def agent(host: str, port: int, mac: str, public_key: str, shutdown_delay: int):
    """Start the agent server on the target PC."""
    public_key_path = Path(public_key)
    
    if not public_key_path.exists():
        click.echo(click.style(f"✗ Public key not found: {public_key}", fg="red"))
        click.echo("  Run 'wherewol keygen' first, then copy public.pem to this machine.")
        sys.exit(1)
    
    click.echo(click.style("⚡ WhereWOL Agent", fg="cyan", bold=True))
    click.echo(f"  MAC Address:    {mac}")
    click.echo(f"  Public Key:     {public_key_path}")
    click.echo(f"  Shutdown Delay: {shutdown_delay}s")
    click.echo()
    click.echo(f"🌐 Starting server on http://{host}:{port}")
    click.echo(click.style("   Press Ctrl+C to stop", fg="yellow"))
    click.echo()
    
    app = create_agent_app(mac, public_key_path, shutdown_delay)
    app.run(host=host, port=port, debug=False)


@cli.command()
@click.option("--target", required=True, help="Agent URL (e.g., http://192.168.0.50:5000)")
def wake(target: str):
    """Send Wake-on-LAN request to the agent."""
    import requests as req
    
    click.echo(f"☀️ Sending WOL request to {target}...")
    
    try:
        resp = req.post(f"{target}/wol", timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            click.echo(click.style(f"✓ {result.get('status', 'Success')}", fg="green"))
        else:
            result = resp.json()
            click.echo(click.style(f"✗ {result.get('error', 'Failed')}", fg="red"))
            
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
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
        click.echo(click.style(f"✗ Private key not found: {private_key}", fg="red"))
        click.echo("  Run 'wherewol keygen' first.")
        sys.exit(1)
    
    click.echo(f"⏻ Sending shutdown command to {target}...")
    
    try:
        # Load key and sign
        key = load_private_key(private_key_path)
        signature = sign_message(b"shutdown", key)
        
        # Send request
        resp = req.post(
            f"{target}/shutdown",
            json={"signature": signature, "close_port": close_port},
            timeout=10
        )
        
        if resp.status_code == 200:
            result = resp.json()
            click.echo(click.style(f"✓ {result.get('status', 'Success')}", fg="green"))
        else:
            result = resp.json()
            click.echo(click.style(f"✗ {result.get('error', 'Failed')}", fg="red"))
            
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5050, help="Port to listen on")
@click.option("--target", required=True, help="Agent URL (e.g., http://192.168.0.50:5000)")
@click.option("--private-key", default="./keys/private.pem", help="Path to private key")
@click.option("--password", envvar="WHEREWOL_PASSWORD", help="Access password (or set WHEREWOL_PASSWORD env var)")
def webui(host: str, port: int, target: str, private_key: str, password: str):
    """Start the web control panel."""
    private_key_path = Path(private_key)
    
    if not password:
        # Generate a random password if not provided
        password = secrets.token_urlsafe(16)
        click.echo(click.style("⚠ No password set. Generated temporary password:", fg="yellow"))
        click.echo(click.style(f"   {password}", fg="cyan", bold=True))
        click.echo()
    
    if not private_key_path.exists():
        click.echo(click.style(f"⚠ Private key not found: {private_key}", fg="yellow"))
        click.echo("  Shutdown commands will not work. Run 'wherewol keygen' first.")
        click.echo()
    
    click.echo(click.style("⚡ WhereWOL Web UI", fg="cyan", bold=True))
    click.echo(f"  Target Agent: {target}")
    click.echo(f"  Private Key:  {private_key_path}")
    click.echo()
    click.echo(f"🌐 Starting web UI on http://{host}:{port}")
    click.echo(click.style("   Press Ctrl+C to stop", fg="yellow"))
    click.echo()
    
    app = create_webui_app(target, private_key_path, password)
    app.run(host=host, port=port, debug=False)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    cli()
