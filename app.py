from flask import jsonify
import pymongo
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from functools import wraps
from bson.objectid import ObjectId
import datetime
from collections import OrderedDict
from flask_cors import CORS
from flask_cors import cross_origin

# Setting up the database
client = pymongo.MongoClient(
    "mongodb+srv://ramukaka:password01@cluster0.vovif.mongodb.net/test?ssl=true&ssl_cert_reqs=CERT_NONE")
db = client.inventory

app = Flask(__name__)
CORS(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    # adding the cors header property manually
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    return response


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message):
    """
    Renders an apology page, whenever the user makes an error.
    """

    return render_template("apology.html", bottom=message)


@app.route("/")
def index():
    """
    The main introductory page of the program.
    """

    return render_template("index.html")


@app.route("/signUp", methods=["GET", "POST"])
def signUp():
    """
    Registers the user.
    """
    if request.method == "POST":

        message = ["All Clear"]
        postData = request.get_json()

        try:
            first_name = postData["first_name"]
        except KeyError:
            message.append("First Name Missing")
            first_name = ""

        try:
            email = postData["email"]
            username = postData["username"]
            password = postData["password"]
            confirmation = postData["confirmation"]
        except KeyError:
            return jsonify({"code": False, "message": "Required Fields Empty"})

        if password != confirmation:
            return jsonify(False, {"message": "Passwords don't match"})

        if not check_password(password):
            return jsonify(False, {"message": "Password too weak"})

        # Generating a hash key for the user's password
        hash_pas = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)

        # Checking if the username already exists
        if db.shopkeeper.count_documents({"username": username}) != 0:
            return jsonify(False, {"message": "Username already exists"})

        # Checking if the email_id already exists
        if db.shopkeeper.count_documents({"email": email}) != 0:
            return jsonify(False, {"message": "Email already exists"})

        inv_id = find_inv_id(username, first_name)

        # Inserting username and password in the database
        db.shopkeeper.insert_one({"name": first_name, "email": email,
                                  "username": username, "password": hash_pas, "inv_id": inv_id, "orders": []})

        db.inventory.insert_one({"inv_id": inv_id})

        return jsonify(True, {"message": message, "inventory id": inv_id})
    else:
        return jsonify(True)


def check_password(password):
    if len(password) < 8:
        return False
    digits = 0
    alpha = 0
    special = 0
    for i in password:
        if i.isdigit():
            digits += 1
        elif i.isalpha():
            alpha += 1
        else:
            special += 1
    if digits < 1 or special < 1:
        return False
    return True


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Logs user in.
    """

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        postData = request.get_json()
        try:
            user_inp = postData['user_inp']
            password = postData["password"]
        except KeyError:
            return jsonify({"code": False, "message": "Required Fields Empty"})

        if db.shopkeeper.count_documents({"username": user_inp}) == 0:

            if db.shopkeeper.count_documents({"email": user_inp}) == 0:
                return jsonify({"code": False, "message":  "User Not Found"})

            else:
                stored_pass = db.shopkeeper.find({"email": user_inp})

        else:
            stored_pass = db.shopkeeper.find({"username": user_inp})

        try:
            if not check_password_hash(stored_pass[0]['password'], password):
                return jsonify({"code": False, "message":  "Incorrect Password"})
        except IndexError:
            return jsonify({"code": False, "message": "User not found"})

        session["user_id"] = stored_pass[0]["_id"]
        session["name"] = stored_pass[0]["name"]
        session["inv_id"] = stored_pass[0]["inv_id"]

        return jsonify({"code": True})

    else:
        return jsonify({"code": False, "message": "Incorrect request method, use POST"})


@app.route("/logout")
@login_required
def logout():
    """
    Log user out
    """

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect('/')


def find_inv_id(username, first_name):
    ans = ""
    for i in range(0, len(first_name), 2):
        ans += first_name[i]
    return username + ans


@app.route("/addProduct", methods=["GET", "POST"])
# @login_required
def addProduct():

    if request.method == "POST":
        session["inv_id"] = "RmRam"

        postData = request.get_json()
        message = ["All Clear"]
        try:
            product_id = postData["product_id"]
            price = postData["price"]
            quantity = postData["quantity"]
        except KeyError:
            return jsonify({"code": False, "message": "Required Fields Empty"})

        try:
            description = postData["description"]
            product_name = postData["product_name"]
        except KeyError:
            message.append("Product Name and Description Empty")
            product_name = ""
            description = []

        if db.product.count_documents({"product_id": product_id}) == 0:
            db.product.insert_one(
                {"product_id": product_id, "product_name": product_name, "price": int(price), "description": description})
        else:
            message.append("Product Id already exits, incrementing the stock")

        db.inventory.update({'inv_id': session["inv_id"]}, {
            '$inc': {str(product_id): quantity}})

        x = db.inventory.find_one({"inv_id": session["inv_id"]})
        big = 0
        for i in x:
            if type(x[i]) is int:
                big += x[i]
        session["max_stock"] = big

        return jsonify({"code": True, "message": message})


@app.route("/deleteProduct", methods=["GET", "POST"])
@login_required
def deleteProduct():

    if request.method == "POST":

        postData = request.get_json()

        try:
            product_id = postData["product_id"]
        except KeyError:
            return jsonify({"code": False, "message": "Required Field Empty"})

        db.inventory.update({'inv_id': session["inv_id"]}, {
            '$set': {str(product_id): 0}})

        return jsonify({"code": True})


@app.route("/billingCheckout", methods=["GET", "POST"])
# @login_required
def billingCheckout():
    if request.method == "POST":
        session["inv_id"] = "RmRam"

        postData = request.get_json()
        message = []

        try:
            orders = postData["orders"]
        except KeyError:
            return jsonify({"code": False, "message": "Required Field Empty"})

        try:
            phone = postData["phone"]
            customer_id = phone
        except KeyError:
            # If the user doesn't provide a phone number, we will automatically generate a customer id
            customer_id = find_customer_id()
            message.append(
                f"Phone Number Missing, Customer ID = {customer_id}")
            phone = None

        name = postData["name"] if "name" in postData else ""
        wishlist = postData["wishlist"] if "wishlist" in postData else []
        location = postData["location"] if "location" in postData else ""

        if db.customer.count_documents({"customer_id": customer_id}) == 0:
            db.customer.insert_one({"customer_id": customer_id, "name": name,
                                    "phone": phone, "wishlist": wishlist, "location": location, "orders": [], "shops_visited": {session["inv_id"]: 1}})
        else:
            db.customer.update({"customer_id": customer_id}, {
                               "$inc": {"shops_visited."+session["inv_id"]: 1}})

        available_products = db.inventory.find(
            {"inv_id": session["inv_id"]})[0]
        total = 0
        for i in orders:
            if i not in available_products or available_products[i] < orders[i]:
                return jsonify({"code": False, "message": "Out of stock"})
            val = int(
                orders[i]) * float((db.product.find({"product_id": int(i)})[0]["price"]))
            total += val
            db.inventory.update({"inv_id": session["inv_id"]}, {
                                "$inc": {i: (-1) * orders[i]}})

        dateobject = datetime.date.today()
        dt = datetime.datetime.combine(dateobject, datetime.time.min)

        order_id = db.orders.insert(
            {"inv_id": session["inv_id"], "customer_id": customer_id, "order": orders, "total": total, "date": dt})

        db.customer.update({"customer_id": customer_id}, {
                           "$push": {"orders": order_id}})

        db.shopkeeper.update({"inv_id": session["inv_id"]}, {
            "$push": {"orders": order_id}})

        return jsonify({"code": True, "total": total, "message": message, "order_id": str(order_id)})


@app.route("/addToWishlist", methods=["GET", "POST"])
@login_required
def addToWishlist():
    if request.method == "POST":

        postData = request.get_json()

        message = ["All Clear"]
        if "phone" in postData:
            customer_id = postData["phone"]
        elif "customer_id" in postData:
            customer_id = postData["customer_id"]
        else:
            return jsonify({"code": False, "message": "Required Fields Empty"})
        try:
            wishlist = postData["wishlist"]
        except KeyError:
            message.append("Intial Wishlist Empty")
            wishlist = []

        if db.customer.count_documents({"customer_id": customer_id}) == 0:
            db.customer.insert_one(
                {"customer_id": customer_id, "wishlist": wishlist})
        else:
            x = db.customer.find(
                {"customer_id": customer_id})[0]["wishlist"]
            for i in wishlist:
                if i in x:
                    wishlist[i] += x[i]

        db.customer.update({"customer_id": customer_id}, {
                           "$set": {"wishlist": wishlist}})

        return jsonify({"code": True, "message": message})


def find_customer_id():
    report = db.customer.find(
        {}, sort=[('_id', pymongo.DESCENDING)])
    for i in report:
        if "phone" not in i or i["phone"] == None:
            return (i["customer_id"]) + 1


@app.route("/getInventoryID")
@login_required
def getInventoryID():
    return session["inv_id"]


@app.route("/reBilling", methods=["GET", "POST"])
@login_required
def reBilling():

    postData = request.get_json()

    try:
        order_id = postData["order_id"]
        products = postData["products"]
    except KeyError:
        return jsonify({"code": False, "message": "Required Fields Empty"})

    try:
        inp = db.orders.find_one({"_id": ObjectId(order_id)})
        if inp == None:
            return jsonify({"code": False, "message": "Invalid Order Id"})
    except:
        return jsonify({"code": False, "message": "Invalid Order Id"})
    order = inp["order"]
    total = inp["total"]

    change = 0
    for i in products:
        if products[i] > order[i]:
            return jsonify({"code": False, "message": "Cannot return more than already bought"})
        order[i] -= products[i]
        change += (int(products[i]) *
                   float((db.product.find_one({"product_id": int(i)})["price"])))

    total -= change
    db.orders.update({"_id": ObjectId(order_id)}, {
                     "$set": {"order": order, "total": total}})

    return jsonify({"code": True, "change": change})


@app.route("/dashboard")
# @login_required
def dashboard():
    session["inv_id"] = "RmRam"
    session["max_stock"] = 225

    calc = count_sold_today()
    sold_today = calc["total_sold"]
    profit = calc["profit"]
    most_selling = calc["most_selling"]

    inven_stat = calc_active_inventory()
    percentage = inven_stat["percentage"]
    quantity = inven_stat["quantity"]

    return jsonify({"code": True, "sold_today": sold_today, "active_inventory": str(percentage) + "%", "quantity": quantity, "profit": profit, "most_selling": most_selling})


@app.route("/soldToday")
# @login_required
def soldToday():
    calc = count_sold_today()
    prods = calc["products"]
    total = calc["total_sold"]
    fin = {}
    for i in prods:
        x = db.product.find_one({"product_id": int(i)})["product_name"]
        fin[x] = prods[i]
    return jsonify({"code": True, "prods": fin, "total": total})


@app.route("/activeInventory")
# @login_required
def activeInventory():
    """
    Function that runs when the user clicks on "active inventory" from the dashboard, returns the total percentage of active inventory and indivisual percentage of the products.
    """
    calc = calc_active_inventory()
    products = calc["indivisual"]
    total = calc["percentage"]
    fin = {}

    for i in products:
        x = db.product.find_one({"product_id": int(i)})["product_name"]
        fin[x] = str(products[i]) + "%"

    return jsonify({"code": True, "total": str(total) + "%", "products": fin})


def count_sold_today():
    """
    Function to calculate the number of products sold today, as well as the profit made for the day.
    """

    session["inv_id"] = "RmRam"
    dateobject = datetime.date.today()
    dt = datetime.datetime.combine(dateobject, datetime.time.min)

    x = db.orders.find({"inv_id": session["inv_id"], "date": dt})

    products = {}
    tot_sold = 0
    profit = 0

    for i in x:
        for j in i["order"]:
            tot_sold += i["order"][j]
            if j in products:
                products[j] += i["order"][j]
            else:
                products[j] = i["order"][j]

    big = max(list(products.values()))

    for i in products:
        val = db.product.find_one({"product_id": int(i)})["price"]
        profit += (int(val) * products[i])
        if products[i] == big:
            name = db.product.find_one({"product_id": int(i)})["product_name"]
            most_selling = {name: products[i]}

    return {"products": products, "total_sold": tot_sold, "profit": profit, "most_selling": most_selling}


def calc_active_inventory():
    """
    Function to calculate the number of products in stock and the percentage they make up to, as a whole and indivisually.
    """
    session["inv_id"] = "RmRam"
    session["max_stock"] = 180
    x = db.inventory.find_one({"inv_id": session["inv_id"]})

    quantity = 0
    indivisual = {}

    for i in x:
        if type(x[i]) is int:
            quantity += x[i]
            indivisual[i] = ((100 * x[i])) // session["max_stock"]

    percentage = ((100 * quantity) //
                  session["max_stock"]) if "max_stock" in session else 0

    return {"percentage": percentage, "quantity": quantity, "indivisual": indivisual}


@app.route('/scanProduct', methods=["GET", "POST"])
# @login_required
def scanProduct():
    postData = request.get_json()
    try:
        product_id = postData["product_id"]
    except KeyError:
        return jsonify({"code": False, "message": "Required Fields Empty"})
    product = db.product.find_one({"product_id": product_id})
    del product["_id"]
    if not product:
        return jsonify({"code": False, "message": "Invalid Product Id"})
    return jsonify({"code": True, "info": product})

# "wishlist": {"69": 5, "79": 9}

# signUp
# {
#     "first_name": "Ramu",
#     "email": "hrishikeshmm@gmail.com",
#     "username": "Ramu",
#     "confirmation": "ramu@1234",
#     "password": "ramu@1234"
# }
# addproduct
# {
#     "product_id": 69,
#     "product_name": "maggie",
#     "price": 12,
#     "quantity": 5,
#     "description": {"colour": "yellow"}
# }
# billingCheckout
#  {
#     "customer_id": 69,
#     "name": "Ramu",
#     "phone": 7975564044,
#     "wishlist": "idk",
#     "location": "Wagholi",
#     "orders": {"79": 5}
# }
