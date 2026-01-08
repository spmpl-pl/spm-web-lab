from flask import Flask, jsonify, request, send_from_directory, session, render_template
import base64
from datetime import datetime
import hashlib
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv("/var/www/spm-web-lab/.env")

app = Flask(__name__)
AIclient_direct = OpenAI() 
AIclient_AIFirewall = OpenAI(base_url=os.getenv("AIFIREWALL_BASE_URL"), 
                    default_headers={"x-imperva-api-key": os.getenv("AIFIREWALL_API_KEY"),
                                    "x-target-url": os.getenv("ORIGINAL_LLM_PROVIDER_URL")})

app.secret_key = os.getenv("SECRET_KEY")  # Needed for sessions

file_basedir = os.path.dirname(os.path.abspath(__file__))
file_guestbook = Path( os.path.join(file_basedir, "GuestBookEntries.json"))
file_productdb = os.path.join(file_basedir, "ProductDB.json")
file_userdb = os.path.join(file_basedir, "UserDB.json")

###### LOAD DATA FUNCTIONS 

def load_UserDB():
    with open(file_userdb) as f:
        return json.load(f)

def load_ProductDB():
    with open(file_productdb) as f:
        return json.load(f)
    
def load_guestbook():
    if not file_guestbook.exists():
        return {"entries": []}
    
    with open(file_guestbook, "r") as f:
        return json.load(f)

def save_guestbook(data):
    with open(file_guestbook, "w") as f:
        json.dump(data, f, indent=2)


###### ERROR HANDLING 

@app.errorhandler(500)
def handle_500(error):
    return jsonify({
        "status": 500,
        "status_message": "Internal Server Error"
    }), 500



###### ROUTING 

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

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')


###### API FUNCTIONS 

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get("username", "")
    password = data.get("password", "")

    password_md5 = hashlib.md5(password.encode()).hexdigest()
    users = load_UserDB()

    # Search for user in JSON
    for user_id, user in users.items():
        if user.get("username") == username and user.get("password") == password_md5:
            session["username"] = username
            session["userid"] = user_id
            session["first_name"] = user.get("first_name")
            session["last_name"] = user.get("last_name")
            return jsonify({"success": True, "message": "Login successful"})

    return jsonify({"success": False, "message": "Invalid username or password"})


@app.route('/api/logout')
def api_logout():
    session.clear() 
    return jsonify({"success": True, "message": "Logged out. Thank you for using this demo environment;]"})


@app.route('/api/GetSession', methods=['GET'])
def api_GetSession():
    username = session.get("first_name")
    msg = f"Hello {username}! This is SPM LAB! Enjoy your day!" if username else "Hello from SPM LAB! Not logged in."
    return jsonify({"message": msg, "username": username, "userid": session.get("userid"), "first_name": session.get("first_name"), "last_name": session.get("last_name") })


@app.route('/api/GetSum', methods=['POST'])
def api_GetSum():
    data = request.json  # Get JSON data from frontend
    try:
        arg1 = int(data["arg1"])
    except (ValueError, TypeError): 
        return jsonify({"error_message": "Invalid argument type"}), 400
    
    arg2 = int(data["arg2"])
    sum = arg1 + arg2
    return jsonify({"sum": sum})


@app.route('/api/GetUserData', methods=['POST'])
def api_GetUserData():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    data = request.json  # Get JSON data from frontend
    users = load_UserDB()

    if data["id"] == "' OR 1 = 1;":
        return jsonify(users)
    return jsonify(users.get(data["id"]))


@app.route('/api/GetProductOverview', methods=['GET'])
def api_GetProductOverview():
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
    return jsonify( flat_products )


@app.route('/api/GetProduct', methods=['POST'])
def api_GetProduct():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    products = load_ProductDB()
    data = request.json 
    ## TODO - error handling and excessive data exposure 

    if data["category"] and data["id"]:
        for category in products:
            if category["category_id"] == int(data["category"]):
                for product in category["products"]:
                    if product["id"] == int(data["id"]):
                        return jsonify(product)
    
    return jsonify({"error_message": "Unknown Error"}), 400


@app.route("/api/GuestBook", methods=["GET"])
def api_guestbook_get():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    data = load_guestbook()
    return jsonify(data["entries"])


@app.route("/api/GuestBook", methods=["POST"])
def api_guestbook_post():
    payload = request.json

    first_name = session.get("first_name")
    last_name = session.get("last_name")
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message required"}), 400

    entry = {
        "username": str(first_name) + " " + str(last_name),
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data = load_guestbook()
    data["entries"].insert(0, entry)
    save_guestbook(data)

    return jsonify({"success": True})


@app.route("/api/GuestBook", methods=["DELETE"])
def api_guestbook_delete():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    data = { "entries": [] }
    save_guestbook(data)
    return jsonify({"success": True})

@app.route("/api/ChatBot", methods=["POST"])
def api_ChatBot():

    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400
    

    if data["protected"]: 
        selectedAI = AIclient_AIFirewall
    else: 
        selectedAI = AIclient_direct

    if data["good_mood"]: 
        system_prompt = "You are a helpful assistant."
    else: 
        system_prompt = "You are rude assistant."

    user_message = data["message"]

    try:
        input_prompt = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        
        response = selectedAI.responses.create(
            model="gpt-5-nano",
            input=input_prompt
        )

        return jsonify({
            "reply": response.output_text,
            "prompt": input_prompt
        })

    except OpenAIError as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=False)
