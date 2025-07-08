import requests

# === CONFIG ===
AGENT_URL = "http://192.168.0.50:5000/wol"  # Cseréld ki, ha más az IP

# === SEND WOL REQUEST ===
try:
    response = requests.post(AGENT_URL)
    print("Status:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", str(e))
