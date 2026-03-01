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



app.secret_key = os.getenv("SECRET_KEY")  # Needed for sessions


file_basedir = os.path.dirname(os.path.abspath(__file__))
file_guestbook = Path( os.path.join(file_basedir, "GuestBookEntries.json"))
file_productdb = os.path.join(file_basedir, "DBs/ProductDB.json")
file_productcategorydb = os.path.join(file_basedir, "DBs/ProductCategoryDB.json")
file_userdb = os.path.join(file_basedir, "DBs/UserDB.json")

###### LOAD DATA FUNCTIONS 

def load_UserDB():
    with open(file_userdb) as f:
        return json.load(f)

def load_ProductDB():
    with open(file_productdb) as f:
        return json.load(f)

def load_ProductCategoryDB():
    with open(file_productcategorydb) as f:
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

@app.route('/wafpanel')
def wafpanel_page():
    return render_template('wafpanel.html')

@app.route('/apipanel')
def apipanel_page():
    return render_template('apipanel.html')

@app.route('/webshop')
def webshop_page():
    return render_template('webshop.html')

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

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
    username = session.get("username")
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


@app.route('/api/GetProductByID', methods=['POST'])
def api_GetProductByID():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    products = load_ProductDB()
    data = request.json 

    if data["pID"]:
        return products[data["pID"]]
    else:
        return jsonify({"error_message": "Unknown Error"}), 400


@app.route('/api/GetProductsByCategory', methods=['POST'])
def api_GetProductByCategory():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    products = load_ProductDB()
    data = request.json 
    requested_category = data["pCAT"]
    return_data = []
    if not requested_category: requested_category = 1

    if requested_category:
        for item_pID, item in products.items():
            if str(item["category_id"]) == requested_category:
                item["pID"] = item_pID
                return_data.append(item)
        return return_data
    else:
        return jsonify({"error_message": "Unknown Error"}), 400


@app.route('/api/GetCategories', methods=['GET'])
def api_GetCategories():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    categories = load_ProductCategoryDB()
    return categories



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


@app.route("/api/GetHeaders", methods=["GET"])
def api_getheaders_get():
    return jsonify(list(request.headers.items()))


@app.route("/api/AddToCart", methods=["POST"])
def api_addtocard_post():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    data = request.json

    # Validate request body
    if not data or "pID" not in data or "pQTY" not in data:
        return jsonify({"error_message": "Missing pID or pQTY"}), 400

    products = load_ProductDB()
    new_pID = data["pID"]
    new_pQTY = data["pQTY"]

    # Validate format
    if not isinstance(new_pID, str):
        return jsonify({"error_message": "pID must be a string"}), 400
    
    if not isinstance(new_pQTY, int):
        return jsonify({"error_message": "pQTY must be an integer"}), 400
    
    if new_pID not in products:
        return jsonify({"error_message": "pID not valid. Not in the product database"}), 400

    if "cart" not in session or not isinstance(session["cart"], dict):
        session["cart"] = {}

    
    if new_pID in session["cart"]:
        session["cart"][str(new_pID)]["pQTY"] += new_pQTY
    else:
        session["cart"][str(new_pID)] = {
            "pQTY": new_pQTY
        }

    session.modified = True
    
    return jsonify({"success": True})


@app.route("/api/GetCart", methods=["GET"])
def api_getcard_get():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    products = load_ProductDB()
    cart_to_return = session["cart"]

    for item_pID, item in cart_to_return.items():
        item["pName"] = products[item_pID]["name"]
        item["pPrice"] = products[item_pID]["price"]
        item["pTotalPrice"] = round(products[item_pID]["price"]*item["pQTY"],2)

    return cart_to_return


@app.route("/api/DeleteCart", methods=["DELETE"])
def api_deletecart_delete():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    session["cart"] = {}
    session["coupons"] = []

    return jsonify({"success": True})


@app.route("/api/GetCartInfo", methods=["GET"])
def api_getcartinfo_get():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    cart = session.get("cart", {})
    coupons = session.get("coupons", [])
    products = load_ProductDB()
    
    cPRICE = 0
    cDISCOUNT = 0
    cPRICEFINAL = 0
    cITEMS = 0

    for item_pID, item in cart.items():
        cITEMS += item["pQTY"]
        cPRICE += products[item_pID]["price"]*item["pQTY"]

    for coupon in coupons:
        cDISCOUNT += coupon["cDISCOUNT"]
    
    cPRICEFINAL = cPRICE - cDISCOUNT

    return jsonify({"cITEMS": cITEMS, "cPRICE": round(cPRICE, 2), "cDISCOUNT": cDISCOUNT , "cPRICEFINAL": round(cPRICEFINAL, 2)})


@app.route("/api/AddCoupon", methods=["POST"])
def api_addcoupon_post():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    data = request.json
    
    if not data or "cCODE" not in data:
        return jsonify({"error_message": "Missing cCODE"}), 400

    cCODE = data["cCODE"]

    # Validate format
    if not isinstance(cCODE, str):
        return jsonify({"error_message": "cCODE must be a string"}), 400

    if len(cCODE) != 6:
        return jsonify({"error_message": "cCODE must be exactly 6 characters"}), 400

    if not cCODE.startswith("12345"):
        return jsonify({"error_message": "Invalid code"}), 400

    if "coupons" not in session:
        session["coupons"] = []
    
    session["coupons"].append({"cCODE": cCODE, "cDISCOUNT": 100 })
    session.modified = True
    return jsonify({"success": True})


@app.route("/api/GetCoupons", methods=["GET"])
def api_getcoupon_get():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    return session["coupons"]


@app.route("/api/DeleteCoupons", methods=["DELETE"])
def api_deletecoupons_delete():
    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    session["coupons"] = []
    return jsonify({"success": True})






@app.route("/api/ChatBot", methods=["POST"])
def api_ChatBot():

    if ( "username" not in session ):
        return jsonify({"error_message": "Not Authenticated"}), 401
    
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    if data["good_mood"]: 
        system_prompt = "Be a helpful, supportive, and encouraging assistant. Answer clearly and politely. Do not respond in Spanish or include Spanish words or phrases."
    else: 
        system_prompt = "Respond in a rude, dismissive, and sarcastic tone. Be blunt, impatient, and slightly condescending. Do not apologize. Do not soften criticism. Do not respond in Spanish or include Spanish words or phrases."

    user_message = data["message"]



    try:
        if data["protected"]: 

            client = OpenAI(base_url=os.getenv("AIFIREWALL_BASE_URL"), 
                    default_headers={
                        "x-imperva-api-key": os.getenv("AIFIREWALL_API_KEY"),
                        "x-user-id": session.get("username"),
                        "x-target-url": os.getenv("ORIGINAL_LLM_PROVIDER_URL")
                        })
            if "<USER_INPUT>" in user_message or "</USER_INPUT>" in user_message:
                return {"error": "User input contains invalid tags."}, 400

            input_prompt = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"<USER_INPUT>{user_message}</USER_INPUT>"}
                ]
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=input_prompt,
            )
            AIresponse = response.choices[0].message.content

        else:
            client = OpenAI() 

            input_prompt = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]

            response = client.responses.create(
                model="gpt-5-nano",
                input=input_prompt
            )
            AIresponse = response.output_text

        return jsonify({
            "reply": AIresponse,
            "prompt": input_prompt
        })

    except OpenAIError as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=False)
