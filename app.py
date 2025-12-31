from flask import Flask, jsonify, request, send_from_directory, session, render_template
import base64
from datetime import datetime
import hashlib
import json
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Needed for sessions




BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GUESTBOOK_FILE = Path( os.path.join(BASE_DIR, "GuestBookEntries.json"))
def load_guestbook():
    if not GUESTBOOK_FILE.exists():
        return {"entries": []}
    
    with open(GUESTBOOK_FILE, "r") as f:
        return json.load(f)

def save_guestbook(data):
    with open(GUESTBOOK_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_ProductDB():
    DATA_FILE = os.path.join(BASE_DIR, "ProductDB.json")
    with open(DATA_FILE) as f:
        return json.load(f)

DATA_FILE = os.path.join(BASE_DIR, "UserData.json")
with open(DATA_FILE) as f:
    users = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/panel')
def panel_page():
    return render_template('panel.html')

@app.route('/webshop')
def webshop_page():
    return render_template('webshop.html')

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
@app.route('/api/GetSession', methods=['GET'])
def get_data():
    username = session.get("username")
    msg = f"Hello from SPM LAB! Logged in as {username}" if username else "Hello from SPM LAB! Not logged in."
    return jsonify({"message": msg, "username": username, "userid": session.get("userid"), "first_name": session.get("first_name"), "last_name": session.get("last_name") })

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
            session["first_name"] = user.get("first_name")
            session["last_name"] = user.get("last_name")
            return jsonify({"success": True, "message": "Login successful"})

    return jsonify({"success": False, "message": "Invalid username or password"})

# GUESTBOOK
@app.route("/api/guestbook", methods=["GET"])
def get_entries():
    data = load_guestbook()
    return jsonify(data["entries"])

@app.route("/api/guestbook", methods=["POST"])
def add_entry():
    payload = request.json
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    first_name = session.get("first_name")
    last_name = session.get("last_name")
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message required"}), 400

    entry = {
        "username": first_name + " " + last_name,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data = load_guestbook()
    data["entries"].insert(0, entry)
    save_guestbook(data)

    return jsonify({"success": True})


##
## Other API Calls
##

@app.route('/api/GetTime', methods=['GET'])
def lab_GetTime():
    time = datetime.now()
    return jsonify({"time": time})

@app.route('/api/GetDayOfWeek', methods=['GET'])
def lab_GetDayOfWeek():
    weekday = datetime.now().strftime("%A")
    return jsonify({"weekday": weekday})

@app.route('/api/GetSum', methods=['POST'])
def lab_GetSum():
    data = request.json  # Get JSON data from frontend
    arg1 = int(data["arg1"])
    arg2 = int(data["arg2"])
    sum = arg1 + arg2
    return jsonify({"sum": sum})

@app.route('/api/GetUserData', methods=['POST'])
def lab_GetUserData():
    data = request.json  # Get JSON data from frontend
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    return jsonify(users.get(data["id"]))

@app.route('/api/GetProductOverview', methods=['GET'])
def lab_GetProductOverview():
    data = load_ProductDB()
    flat_products = []
    for category in data:
        cat_id = category["category_id"]
        cat_name = category["category_name"]
        for product in category["products"]:
            flat_product = {
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description", ""),
                "category_id": cat_id,
                "category_name": cat_name
            }       
            flat_products.append(flat_product)
    return jsonify({"status": 200, "status_message": "OK", "data": flat_products})


@app.route('/api/GetProduct', methods=['POST'])
def lab_GetProduct():
    products = load_ProductDB()
    data = request.json  # Get JSON data from frontend
    if ( "username" not in session ):
        return jsonify({"status": 401, "status_message": "Not Authenticated", "data": "Not Authenticated"}), 401
    else:
        for category in products:
            if category["category_id"] == int(data["category"]):
                for product in category["products"]:
                    if product["id"] == int(data["id"]):
                        return jsonify(product)
        return None


@app.route('/api/ReflectInput', methods=['POST'])
def lab_ReflectInput():
    data = request.json  # Get JSON data from frontend
    return jsonify({"status": 200, "status_message": "OK", "data": data["input"]})

if __name__ == '__main__':
    app.run(debug=True)
