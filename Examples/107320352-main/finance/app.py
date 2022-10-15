import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import time
import json

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Get user's current holdings from SQL table "holdings"
    holdings = db.execute('SELECT * FROM holdings WHERE user_id = ?', session["user_id"])
    # Get user's current cash balance from SQL table "users"
    cash = db.execute('SELECT cash FROM users WHERE id = ?', session["user_id"])[0]['cash']
    # Calculate total holdings value. Try,except is to eliminate server crashing when the holdings table is empty
    try:
        total_holdings_value = db.execute('SELECT SUM(total_value) FROM holdings WHERE user_id = ?',
                                         session["user_id"])[0]['SUM(total_value)'] + cash
    except:
        return apology("Your portfolio is empty, please buy some stock :)", 200)
    # Create current price dictionary, get updated prices from server (iexcloud.io) and save them for future use
    current_price = {}
    for holding in holdings:
        current_price[holding['symbol']] = lookup(holding['symbol'])['price']
    # Return index.html and pass required parameters to jinja on front-end
    return render_template("index.html", holdings=holdings, cash=usd(cash), total_holdings_value=usd(total_holdings_value), current_price=current_price)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # When user submits data to /buy via POST
    if request.method == "POST":
        # Get the number of shares to buy from form at buy.html (Try except is used to eliminate errors if invalid shares amount provided)
        try:
            int(request.form.get("shares"))
        except:
            return apology("must provide symbol and valid number of shares to buy", 400)

        # Ensure correct symbol and shares number were submited submitted
        if not request.form.get("symbol") or not request.form.get("shares") or not int(request.form.get("shares")) >= 1 or not request.form.get("shares").isdigit():
            return apology("must provide symbol and valid number of shares to buy", 400)

        # Get an updated quote from server at iexcloud.io for requested by user symbol
        try:
            stock_quote = lookup(request.form.get("symbol"))
        except:
            return apology("Symbols database sever not reachable, pleast try later", 400)

        # Verify valid ticker symbol (aka. AAPL, T, SEDG etc...) was entered by checking server response
        if stock_quote is None:
            return apology("Invalid ticker provided", 400)

        # Create variable storing the value of shares to be bought
        number_of_shares = int(request.form.get("shares"))

        # Create variable storing the total cost of shares to be bought
        total_cost = number_of_shares*stock_quote['price']

        # Get user's cash balance
        user_balance = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        # Verify user's cash balance is sufficient for purchasing requested amount of specified stock
        if (user_balance[0]['cash'] < total_cost):
            return apology("Sorry, insufficient funds", 400)
        else:
            # Check if the requested stick is already owned by user
            if not db.execute("SELECT 1 FROM holdings WHERE symbol = ?", stock_quote["symbol"]):
                # If user do now own any amount of specific ticker - create new row in "holding" table with all required information
                db.execute("INSERT INTO holdings (user_id,symbol,company_name,number_of_shares,share_price,total_value) VALUES(?, ?, ?, ?, ?, ?)",
                         session["user_id"], stock_quote['symbol'], stock_quote['name'], number_of_shares, stock_quote['price'], total_cost)

                # Calculate remaining cash balance after transaction
                new_cash = user_balance[0]['cash'] - total_cost

                # Update remaining cash balance after transaction
                db.execute("UPDATE users SET cash = ? WHERE id = ?",new_cash, session["user_id"])
            else:
                # If user has some amount of shares already - calculate the new amount
                new_number_of_shares = db.execute("SELECT number_of_shares FROM holdings WHERE symbol = ? AND user_id = ?",
                                                 stock_quote['symbol'], session["user_id"])[0]['number_of_shares'] + number_of_shares

                # Calculate total value for updated amount
                new_total_value = db.execute("SELECT total_value FROM holdings WHERE symbol = ? AND user_id = ?",
                                             stock_quote['symbol'], session["user_id"])[0]['total_value'] + total_cost

                # Calculate new avarage cost for specific stock
                new_avg_price = new_total_value/new_number_of_shares

                # Update user holdings with above
                db.execute("UPDATE holdings SET number_of_shares = ?, share_price = ?, total_value = ? WHERE symbol = ? AND user_id = ?",
                            new_number_of_shares, new_avg_price, new_total_value, stock_quote['symbol'], session["user_id"])

                # Calculate remaining cash balance after transaction
                new_cash = user_balance[0]['cash'] - total_cost
                db.execute("UPDATE users SET cash = ? WHERE id = ?",new_cash, session["user_id"])

            # Save transaction in History
            db.execute('INSERT INTO transactions (user_id, type, symbol, amount, price, total_transaction, balance) VALUES(?,"buy",?,?,?,?,?)',
                        session["user_id"], request.form.get("symbol"), number_of_shares, stock_quote['price'], total_cost, new_cash)

            return render_template("bought.html", stock_quote=stock_quote, number_of_shares=number_of_shares, total_cost=usd(total_cost), new_cash=new_cash)

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    try:
        transactions = db.execute('SELECT * FROM transactions WHERE user_id = ?', session["user_id"])
    except:
        return apology("No transactions found", 403)
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # Ensure ticker was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)
        elif not request.form.get("symbol").isalpha():
            return apology("invalid symbol", 400)

        try:
            stock_quote = lookup(request.form.get("symbol"))
        except:
            return apology("Symbols database sever not reachable, pleast try later", 400)

        # Check if ticker symbol is valid by verifying response from server
        if stock_quote is None:
            return apology("Invalid symbol provided", 400)
        return render_template("quoted.html", stock_quote=stock_quote)
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Please check password filled", 400)
        elif not (request.form.get("password") == request.form.get("confirmation")):
            return apology("Please check passwords match", 400)
        else:
            username = request.form.get("username")
            password = request.form.get("password")
            password_hash = generate_password_hash(password)
            try:
                db.execute("INSERT INTO users (username,hash) VALUES(?, ?)", username, password_hash)
            except:
                # If the username already exists.
                return apology("Username already in use", 400)
            return render_template("login.html")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Get user's current holdings and store them in variable
    holdings = db.execute('SELECT * FROM holdings WHERE user_id = ?', session["user_id"])

    # Get updated holdings prices and store them in dictionary
    current_price = {}
    for holding in holdings:
        current_price[holding['symbol']] = lookup(holding['symbol'])['price']

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Verify user is trying to sell number of shares that he/she owns and not more
        if int(db.execute('SELECT number_of_shares FROM holdings WHERE user_id = ? and symbol = ?',
                session["user_id"], request.form.get("symbol"))[0]['number_of_shares']) >= int(request.form.get("shares")[0]):
            symbol = request.form.get("symbol")
            number_to_sell = int(request.form.get("shares"))
            sell_price = current_price[symbol]
            total_sell_price = sell_price * number_to_sell
            new_number_of_shares = int(db.execute('SELECT number_of_shares FROM holdings WHERE user_id = ? and symbol = ?',
                                         session["user_id"], request.form.get("symbol"))[0]['number_of_shares']) - number_to_sell
            new_total_value = new_number_of_shares * db.execute('SELECT share_price FROM holdings WHERE user_id = ? and symbol = ?',
                                                                session["user_id"], request.form.get("symbol"))[0]['share_price']

            # Check if after transaction no shares of specific holdings left - delete the row in holdings table (index.html).
            if new_total_value == 0:
                db.execute('DELETE FROM holdings WHERE user_id = ? and symbol = ?', session["user_id"], symbol)
            else:
                db.execute("UPDATE holdings SET number_of_shares = ?, total_value = ? WHERE symbol = ? AND user_id = ?",
                            new_number_of_shares, new_total_value, symbol, session["user_id"])

            # Update user's cash balance
            db.execute('UPDATE users SET cash = cash + ? WHERE id = ?', sell_price*int(number_to_sell), session["user_id"])

            # Get user's updated cash balance
            remaining_balance = db.execute('SELECT cash FROM users WHERE id = ?', session["user_id"])[0]['cash']
            # Save current transaction in history
            db.execute('INSERT INTO transactions (user_id, type, symbol, amount, price, total_transaction, balance) VALUES(?,"sell",?,?,?,?,?)',
                        session["user_id"], symbol, number_to_sell, sell_price, total_sell_price, remaining_balance)

            return render_template("sold.html", holdings=holdings, number_of_shares=int(number_to_sell), symbol=symbol, quote=sell_price, total_cost=total_sell_price, cash=remaining_balance)
        else:
            return apology("Trying to sell more than you have", 400)

    return render_template("sell.html", holdings=holdings, current_price=current_price)


@app.route("/cash_deposit", methods=["GET", "POST"])
@login_required
def deposit():
    """Allow user to add more cash to account"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("cash") or not float(request.form.get("cash")) > 0:
            return apology("must enter positive cash amount to be deposited", 400)

        cash = float(request.form.get("cash"))

        db.execute('UPDATE users SET cash = cash + ? WHERE id = ?', cash, session["user_id"])

        new_cash = db.execute('SELECT cash FROM users WHERE id = ?', session["user_id"])[0]['cash']

        db.execute('INSERT INTO transactions (user_id, type, symbol, amount, price, total_transaction, balance) VALUES(?,"cash deposit","NA","1","1",?,?)',
                    session["user_id"], cash, new_cash)

        return render_template("deposited.html", cash=cash, total_cash=new_cash)

    return render_template("deposit.html")