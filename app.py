from flask import Flask, jsonify, request, send_from_directory, session, render_template
import base64
from datetime import datetime
import hashlib
import json

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Needed for sessions

with open("UserData.json") as f:
    users = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/panel')
def info():
    return render_template('panel.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/guestbook')
def guestbook_page():
    return render_template('guestbook.html')

@app.route('/accountinfo')
def accountinfo_page():
    return render_template('accountinfo.html')

@app.route('/logout')
def logout():
    session.clear()  # remove session
    return jsonify({"success": True, "message": "Logged out. Thank you for using this demo environment;]"})


# Example route to return data
@app.route('/api/data', methods=['GET'])
def get_data():
    username = session.get("username")
    msg = f"Hello from SPM LAB! Logged in as {username}" if username else "Hello from SPM LAB! Not logged in."
    return jsonify({"message": msg, "logged_in_as": username, "userid": session.get("userid")})

# Login Support
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "")
    password = data.get("password", "")

    password_md5 = hashlib.md5(password.encode()).hexdigest()

    # Search for user in JSON
    for user_id, user in users.items():
        if user.get("username") == username and user.get("password") == password_md5:
            session["username"] = username
            session["userid"] = user_id
            return jsonify({"success": True, "message": "Login successful"})

    return jsonify({"success": False, "message": "Invalid username or password"})



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
