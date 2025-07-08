from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import subprocess
import os

# === CONFIG ===
PUBLIC_KEY_PATH = "./keys/public.pem"
WOL_MAC_ADDRESS = "4C:ED:FB:42:F7:64"  # Replace this
PORT_TO_CLOSE = 5000                  # Optional
SHUTDOWN_CMD = "shutdown /s /t 5"     # Windows: 5 sec delay

# === LOAD PUBLIC KEY ===
with open(PUBLIC_KEY_PATH, "rb") as f:
    public_key = serialization.load_pem_public_key(f.read())

app = Flask(__name__)

@app.route("/wol", methods=["POST"])
def wol():
    try:
        subprocess.run(["wakeonlan", WOL_MAC_ADDRESS])
        return jsonify({"status": "WOL packet sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/shutdown", methods=["POST"])
def shutdown():
    try:
        data = request.get_json()
        signature = bytes.fromhex(data.get("signature", ""))
        message = b"shutdown"

        public_key.verify(
            signature,
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        if data.get("close_port"):
            os.system(f"netsh advfirewall firewall add rule name='BlockWherewol' dir=in action=block protocol=TCP localport={PORT_TO_CLOSE}")

        subprocess.Popen(SHUTDOWN_CMD, shell=True)
        return jsonify({"status": "Shutdown initiated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
