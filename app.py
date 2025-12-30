from flask import Flask, jsonify, request, send_from_directory, session
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Needed for sessions

VALID_USERNAME = base64.b64encode("bartoszch".encode()).decode()
VALID_PASSWORD = base64.b64encode("Test123123#".encode()).decode()


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/panel')
def info():
    return send_from_directory('.', 'panel.html')

@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')


@app.route('/logout')
def logout():
    session.clear()  # remove session
    return jsonify({"success": True, "message": "Logged out. Thank you for using this demo environment;]"})


# Example route to return data
@app.route('/api/data', methods=['GET'])
def get_data():
    username = session.get("username")
    msg = f"Hello from SPM LAB! Logged in as {username}" if username else "Hello from SPM LAB! Not logged in."
    return jsonify({"message": msg, "logged_in_as": username})

# Login Support
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "")
    password = data.get("password", "")

    # Encode inputs
    username_enc = base64.b64encode(username.encode()).decode()
    password_enc = base64.b64encode(password.encode()).decode()

    if username_enc == VALID_USERNAME and password_enc == VALID_PASSWORD:
        session["username"] = username
        return jsonify({"success": True, "message": "Login successful"})

    else:
        return jsonify({"success": False, "message": "Invalid credentials"})

##
## Other API Calls
##




@app.route('/api/GetTime', methods=['GET'])
def lab_GetTime():
    time = datetime.now()
    return jsonify({"status": 200, "status_message": "OK", "data": time})

@app.route('/api/GetDayOfWeek', methods=['GET'])
def lab_GetDayOfWeek():
    weekday = datetime.now().strftime("%A")
    return jsonify({"status": 200, "status_message": "OK", "data": weekday})

@app.route('/api/GetSum', methods=['POST'])
def lab_GetSum():
    data = request.json  # Get JSON data from frontend
    arg1 = int(data["arg1"])
    arg2 = int(data["arg2"])
    sum = arg1 + arg2
    return jsonify({"status": 200, "status_message": "OK", "data": sum})

@app.route('/api/ReflectInput', methods=['POST'])
def lab_ReflectInput():
    data = request.json  # Get JSON data from frontend
    return jsonify({"status": 200, "status_message": "OK", "data": data["input"]})

if __name__ == '__main__':
    app.run(debug=True)
