#!/usr/bin/python3

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import time
import json
import pandas as pd
import plotly
import plotly.express as px


from helpers import apology, login_required, generate_graph

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    """Below will be the main page"""
    # Read csv content with pandas into dataframe starting from line 18 (otherwise pandas can't read properly the data)
    
    df = pd.read_csv('All_Traces.csv', skiprows=18)
    
    # Change column names in dataframe to more intuitive
    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
    #print(df.columns)
    #print(df.head)
    
    # Generate JSON graph from dataframe
    graph1JSON = generate_graph(df)

    #return apology("Main Page will be here)", 200)
    return render_template("index.html", graph1JSON=graph1JSON)



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