# wherewol_webui.py
from flask import Flask, render_template_string, request, redirect
import requests
import os

# === CONFIG ===
AGENT_URL = "http://192.168.0.50:5000"

# === HTML UI TEMPLATE WITH DARK MODE, ICONS, PASSWORD ===
HTML_TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>WhereWOL Control</title>
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            padding-top: 50px;
        }
        button {
            font-size: 18px;
            padding: 12px 30px;
            margin: 10px;
            border: none;
            border-radius: 5px;
            background-color: #1e88e5;
            color: white;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #1565c0;
        }
        input[type='password'] {
            padding: 8px;
            margin-top: 15px;
            font-size: 16px;
            border-radius: 4px;
            border: none;
        }
        .status {
            margin-top: 20px;
            font-weight: bold;
            color: #00e676;
        }
        .error {
            color: #ff5252;
        }
        label {
            font-size: 16px;
        }
    </style>
</head>
<body>
    <h1>?? WhereWOL Remote Control</h1>
    <form method=\"post\">
        <div>
            <input type=\"password\" name=\"password\" placeholder=\"Enter password\" required><br><br>
            <button name=\"action\" value=\"wol\">?? Wake PC</button>
            <button name=\"action\" value=\"shutdown\">? Shutdown PC</button><br>
            <label><input type=\"checkbox\" name=\"close_port\"> ?? Close Port After Shutdown</label>
        </div>
    </form>
    {% if message %}
        <div class=\"status {{ 'error' if error else '' }}\">{{ message }}</div>
    {% endif %}
</body>
</html>
"""

app = Flask(__name__)
PASSWORD = "wolpass123"  # Change this to your secure password

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    error = False

    if request.method == "POST":
        password = request.form.get("password")
        if password != PASSWORD:
            return render_template_string(HTML_TEMPLATE, message="Wrong password", error=True)

        action = request.form.get("action")
        close_port = "close_port" in request.form

        try:
            if action == "wol":
                resp = requests.post(f"{AGENT_URL}/wol")
            elif action == "shutdown":
                from client_shutdown import sign_shutdown_message
                signature = sign_shutdown_message()
                resp = requests.post(f"{AGENT_URL}/shutdown", json={
                    "signature": signature,
                    "close_port": close_port
                })
            else:
                raise ValueError("Invalid action")

            if resp.status_code == 200:
                message = resp.json().get("status", "Success")
            else:
                error = True
                message = resp.json().get("error", "Unknown error")

        except Exception as e:
            error = True
            message = str(e)

    return render_template_string(HTML_TEMPLATE, message=message, error=error)

if __name__ == "__main__":
    app.run(debug=True, port=5050)
