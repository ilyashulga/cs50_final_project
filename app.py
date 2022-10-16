#!/usr/bin/python3

#from asyncio.windows_events import NULL
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import time
import json
import pandas as pd
import plotly
import plotly.express as px
import datetime


from helpers import apology, login_required, generate_graph

# Configure File uploads
UPLOAD_FOLDER = 'users_data/'
ALLOWED_EXTENSIONS = {'csv'}


# Configure application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///plotter.db")


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

@app.route("/upload_online", methods=["GET", "POST"])
@login_required
def upload_online():
    """GUI for adding plots one-by-one"""
    db.execute("UPDATE sessions SET is_open = 0 WHERE id = 7")
    #print(session("session"))
    try:
        session_is_open = db.execute("SELECT is_open FROM sessions WHERE is_open=1 AND user_id=?", session["user_id"])[0]["is_open"]
    except:
        return render_template("new_session.html")
        #return apology("Can't access database", 400)
    
    #if session_is_open == 0:
        #return render_template("new_session.html")

    # Read csv content with pandas into dataframe starting from line 18 (otherwise pandas can't read properly the data)
    df = pd.read_csv('All_Traces.csv', skiprows=18)
    
    # Change column names in dataframe to more intuitive
    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
    
    # Generate JSON graph from dataframe
    graph1JSON = generate_graph(df)

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            
            # Get path to current folder (app.py)
            basedir = os.path.abspath(os.path.dirname(__file__))
            # Get username from SQL Database based on session user_id
            username = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])[0]["username"]
            # Get user_folder absolute address
            user_folder = os.path.join(basedir, app.config['UPLOAD_FOLDER'], username)
            # Get session_folder absolure address
            session_folder = os.path.join(basedir, app.config['UPLOAD_FOLDER'], username, session["session"][0]['name'] + "_" + datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
            # Create a folder user private folder if not exists already
            if not os.path.exists(user_folder): 
                os.makedirs(user_folder)
            # Create a session folder inside private folder if not exists already
            if not os.path.exists(session_folder): 
                os.makedirs(session_folder)
            file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], username, session["session"][0]['name'] + "_" + datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S"), filename))
            #return redirect(url_for('download_file', name=filename))
    return render_template("upload_online.html", graph1JSON=graph1JSON)

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
            account_type = "user"
            #db.execute("INSERT INTO users (username,hash,type) VALUES(?, ?, ?)", username, password_hash, account_type)
            try:
                db.execute("INSERT INTO users (username,hash,type) VALUES(?, ?, ?)", username, password_hash, account_type)
            except:
                # If the username already exists.
                return apology("Username already in use", 400)
            return render_template("login.html")
    else:
        return render_template("register.html")



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/new_session", methods=["GET", "POST"])
@login_required
def new_session():
    if request.method == "POST":
        session_name = request.form.get("session_name")
        session_desc = request.form.get("session_description")
        try:
            db.execute("INSERT INTO sessions (name, description, user_id, timestamp, is_open) VALUES(?, ?, ?, DATETIME('now','localtime'), 1)", session_name, session_desc, session["user_id"])
        except:
            apology("Can't open new session", 400)
        session["session"] = db.execute("SELECT name FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])
        return redirect("/")