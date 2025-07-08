import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from pathlib import Path

# === CONFIG ===
AGENT_URL = "http://192.168.0.50:5000/shutdown"  # cseréld le, ha máshol fut
PRIVATE_KEY_PATH = "./keys/private.pem"

# === LOAD PRIVATE KEY ===
with open(PRIVATE_KEY_PATH, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# === SIGN MESSAGE ===
message = b"shutdown"
signature = private_key.sign(
    message,
    padding.PKCS1v15(),
    hashes.SHA256()
)

# === BUILD AND SEND REQUEST ===
payload = {
    "signature": signature.hex(),
    "close_port": False  # tedd True-ra, ha portzárást is akarsz
}

response = requests.post(AGENT_URL, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())
