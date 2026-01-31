"""
NanoWOL - Agent Server Module
Flask server running on the target PC to receive wake/shutdown commands.
Part of the Nano Product Family.
"""

import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify

from crypto import load_public_key, verify_signature, verify_signed_payload
from wol import send_wol_packet
from version import VERSION

logger = logging.getLogger(__name__)

DEFAULT_AGENT_PORT = 5000


def create_agent_app(mac_address: str, public_key_path: Path, shutdown_delay: int = 5) -> Flask:
    """
    Create Flask app for the agent server.
    
    This server runs on the target PC and:
    - Sends WOL packets to wake the machine
    - Accepts signed shutdown commands
    
    Args:
        mac_address: MAC address for WOL
        public_key_path: Path to RSA public key for signature verification
        shutdown_delay: Seconds to wait before shutdown
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load public key for signature verification
    public_key = load_public_key(public_key_path)
    
    # Used nonces for replay protection (in-memory, clears on restart)
    used_nonces = set()
    
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": VERSION
        })
    
    @app.route("/wol", methods=["POST"])
    def wol():
        """Send Wake-on-LAN packet (requires signed payload for authentication)."""
        try:
            data = request.get_json() or {}
            
            # Require authentication via signed payload
            if "payload" not in data:
                logger.warning("WOL rejected: no payload")
                return jsonify({"error": "Authentication required. Use signed payload."}), 401
            
            is_valid, error = verify_signed_payload(
                data, public_key, "wol",
                max_age_seconds=60,
                used_nonces=used_nonces
            )
            if not is_valid:
                logger.warning(f"WOL rejected: {error}")
                return jsonify({"error": error}), 403
            
            send_wol_packet(mac_address)
            logger.info(f"WOL packet sent for {mac_address}")
            return jsonify({"status": "WOL packet sent", "mac": mac_address}), 200
        except Exception as e:
            logger.error(f"WOL failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        """Initiate shutdown with RSA signature verification and replay protection."""
        try:
            data = request.get_json() or {}
            close_port = data.get("close_port", False)
            
            # Check for payload format (required - legacy format removed for security)
            if "payload" not in data:
                logger.warning("Shutdown rejected: legacy format not supported")
                return jsonify({"error": "Legacy signature format removed. Use payload with timestamp and nonce."}), 400
            
            # Verify signed payload with replay protection
            is_valid, error = verify_signed_payload(
                data, public_key, "shutdown",
                max_age_seconds=60,
                used_nonces=used_nonces
            )
            if not is_valid:
                logger.warning(f"Shutdown rejected: {error}")
                return jsonify({"error": error}), 403
            
            logger.info("Valid shutdown command received")

            use_sudo = False
            shutdown_path = shutil.which("shutdown") or "/sbin/shutdown"
            if sys.platform != "win32" and os.geteuid() != 0:
                if shutil.which("sudo"):
                    sudo_check = subprocess.run(
                        ["sudo", "-n", "-v"],
                        capture_output=True,
                        text=True,
                    )
                    if sudo_check.returncode == 0:
                        use_sudo = True
                    else:
                        return jsonify({"error": "Shutdown requires passwordless sudo on this platform"}), 403
                else:
                    return jsonify({"error": "Shutdown requires root privileges on this platform"}), 403
            
            # Optional: block the agent port after shutdown
            warning = None
            if close_port:
                port = request.environ.get("SERVER_PORT", DEFAULT_AGENT_PORT)
                if sys.platform == "win32":
                    os.system(
                        f'netsh advfirewall firewall add rule name="BlockNanoWOL" dir=in action=block protocol=TCP localport={port}'
                    )
                else:
                    warning = "close_port is only supported on Windows"
                    logger.info(warning)
            
            # Initiate shutdown
            delay_seconds = max(0, int(shutdown_delay))
            if sys.platform == "win32":
                subprocess.Popen(["shutdown", "/s", "/t", str(delay_seconds)])
            else:
                shutdown_cmd = f"sleep {delay_seconds}; {shutdown_path} -h now"
                if use_sudo:
                    shutdown_cmd = f"sleep {delay_seconds}; sudo -n {shutdown_path} -h now"
                subprocess.Popen(["/bin/sh", "-c", shutdown_cmd])

            response = {"status": f"Shutdown initiated (delay: {delay_seconds}s)"}
            if warning:
                response["warning"] = warning
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app

