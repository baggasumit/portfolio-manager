from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    userid = int(session["user_id"])
    
    # Retrieve user's cash 
    cashRow = db.execute("SELECT cash from users WHERE id = :userid", userid=userid)
    cash_balance = cashRow[0]['cash']
    
    # Retrieve user's shares info from transactions table
    # Retrieve total number of shares for each symbol
    shares_info = db.execute(
        'SELECT symbol, SUM(quantity) as count FROM "transactions" \
        WHERE userid = :userid GROUP BY symbol', userid=userid)
    
    # add current price and total market value to shares info
    grand_total = cash_balance
    if shares_info:
        for share in shares_info:
            symbol = share['symbol']
            count = share['count']
            current_price = lookup(symbol)['price']
            market_value = current_price * count
            share['price'] = usd(current_price)
            share['market_value'] = usd(market_value)
            grand_total += market_value
    
    return render_template("index.html", shares_info=shares_info, grand_total=usd(grand_total), cash_balance=usd(cash_balance))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        quantity = request.form.get("quantity")
        
        # Check if any fields are blank
        if not symbol:
            return apology("Stock symbol cannot be blank")
        elif not quantity:
            return apology("Number of shares cannot be blank")

        # Check if number of shares is a positive integer
        if not quantity.isdigit() or int(quantity) < 1:
            return apology("Number of shares should be a positive integer")

        # Retrieve stock info
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Stock symbol does not exist")
        
        price = float(stock["price"])
        # calculate total price of shares
        total_price = int(quantity) * price
        # Retreive user info
        userid = int(session["user_id"])
        # query database for userid
        rows = db.execute("SELECT * FROM users WHERE id = :id", id=userid)
        if not rows:
            return apology("You don't have an entry in the database")
        # Retrieve user's available cash   
        cash = float(rows[0]["cash"])
        # Check if user has enough cash
        if cash < total_price:
            return apology("Not enough cash")
        
        # Add transaction to database and update users cash
        db.execute("INSERT INTO transactions (userid, symbol, price, quantity) VALUES (:userid, :symbol, :price, :quantity)", 
            userid=userid, symbol=symbol, price=price, quantity=int(quantity))
        db.execute("UPDATE users SET cash = :cash_left WHERE id = :id", id=userid, cash_left=(cash - total_price))
        
        return render_template("bought.html", stock=stock, quantity=quantity)
    else:
        return render_template("buy.html")
    

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    userid = int(session["user_id"])
    transactions = db.execute(
        'SELECT * FROM "transactions" WHERE userid = :userid', userid=userid)
    return render_template("history.html", transactions=transactions)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Stock symbol cannot be blank")
        stock = lookup(request.form.get("symbol"))
        
        if not stock:
            return apology("Stock symbol does not exist")
        return render_template("quoted.html", stock=stock)
    else:
        return render_template("quote.html")
    # return apology("TODO")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()
    
    if request.method == "POST":
        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")
        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
        # ensure user confirmed password
        elif not request.form.get("confirmPassword"):
            return apology("must confirm password")
            
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")
        
        if password != confirm_password:
            return apology("Passwords do not match")
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if rows:
            return apology("Username already exists")
        
        # Insert user into DB
        userid = db.execute("INSERT INTO users (username, hash) VALUES (:username, :pwhash)", 
            username=username, pwhash=pwd_context.encrypt(password))

        session["user_id"] = userid
        return redirect(url_for("index"))
    # else if user reached route via GET
    else:
        return render_template("register.html")
        
    # return apology("TODO")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        quantity = request.form.get("quantity")
        
        # Check if any fields are blank
        if not symbol:
            return apology("Stock symbol cannot be blank")
        elif not quantity:
            return apology("Number of shares cannot be blank")

        # Check if number of shares is a positive integer
        if not quantity.isdigit() or int(quantity) < 1:
            return apology("Number of shares should be a positive integer")
        quantity = int(quantity)
        # Retrieve stock info
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Stock symbol does not exist")
            
        # Retreive user info
        userid = int(session["user_id"])
        
        # Check if user has enough shares
        shares_info = db.execute(
            'SELECT SUM(quantity) as count FROM "transactions" \
            WHERE userid = :userid AND symbol = :symbol', userid=userid, symbol=symbol)
        if not shares_info or not shares_info[0]['count'] or shares_info[0]['count'] == 0:
            return apology("No shares available for given symbol")
        shares_count = shares_info[0]['count']

        if shares_count < quantity:
            return apology("Not enough shares")
            
        price = float(stock["price"])
        # calculate total price of shares
        total_price = quantity * price
        
        # query database for userid
        rows = db.execute("SELECT * FROM users WHERE id = :id", id=userid)
        if not rows:
            return apology("You don't have an entry in the database")
        # Retrieve user's available cash   
        cash = float(rows[0]["cash"])
        # Check if user has enough cash
    
        
        # Add transaction to database and update users cash
        db.execute("INSERT INTO transactions (userid, symbol, price, quantity) VALUES (:userid, :symbol, :price, :quantity)", 
            userid=userid, symbol=symbol.upper(), price=price, quantity=-quantity)
        db.execute("UPDATE users SET cash = :cash_left WHERE id = :id", id=userid, cash_left=(cash + total_price))
        
        return render_template("sold.html", stock=stock, quantity=quantity)
    else:
        return render_template("sell.html")


@app.route("/changepw", methods=["GET", "POST"])
@login_required
def changepw():
    if request.method == "POST":
        
        # Retrieve form fields
        old_password = request.form.get("oldPassword")
        new_password = request.form.get("newPassword")
        confirm_password = request.form.get("confirmPassword")
        
        # ensure fields are not empty
        if not old_password:
            return apology("must provide old password")
        elif not new_password:
            return apology("must provide new password")  
        elif not confirm_password:
            return apology("must confirm password")
            
        # check if passwords match
        if new_password != confirm_password:
            return apology("Passwords do not match")
            
        userid = int(session["user_id"])
        
        # Retrieve user's password hash
        user_info = db.execute("SELECT hash FROM users WHERE id = :userid", userid=userid)
        
        # ensure password is correct
        if not pwd_context.verify(old_password, user_info[0]["hash"]):
            return apology("Old password is incorrect")
        db.execute("UPDATE users SET hash = :hash WHERE id = :userid", hash=pwd_context.encrypt(new_password), userid=userid)
        
        return render_template("pwchanged.html")
    else:
        return render_template("changepw.html")