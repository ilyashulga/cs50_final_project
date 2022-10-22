#!/usr/bin/python3

#from asyncio.windows_events import NULL
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, safe_join, send_file, abort
from pathlib import Path
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
import os


from helpers import apology, login_required, generate_graph, getIconClassForFilename

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
    
    #df = pd.read_csv('All_Traces.csv', skiprows=18)
    
    # Change column names in dataframe to more intuitive
    #df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
    #print(df.columns)
    #print(df.head)
    
    # Generate JSON graph from dataframe
    #graph1JSON = generate_graph(df)

    #return apology("Main Page will be here)", 200)
    return render_template("index.html", graph1JSON=1)

@app.route("/upload_online", methods=["GET", "POST"], defaults={'reqPath': ''})
@app.route('/upload_online/<path:reqPath>')
@login_required
def upload_online(reqPath):
    """GUI for adding plots one-by-one"""
    #db.execute("UPDATE sessions SET is_open = 0 WHERE id = 11")
    
    # Check if there is any unclosed test session for current user, if none - render a new session page
    try:
        session_is_open = db.execute("SELECT is_open FROM sessions WHERE is_open=1 AND user_id=?", session["user_id"])[0]["is_open"]
    except:
        return render_template("new_session.html")
    
    session_folder = db.execute("SELECT folder FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])[0]["folder"]
    graph1JSON = []

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
            
            file.save(os.path.join(session_folder, filename))
            flash("Result was successfully added")
        # Read csv content with pandas into dataframe starting from row 18 (otherwise pandas can't read properly the data)
        try:
            df = pd.read_csv(os.path.join(session_folder, filename), skiprows=18)
        except:
            return render_template("upload_online.html")
        
        # Change column names in dataframe to more intuitive
        df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
        
        # Generate JSON graph from dataframe
        graph1JSON = generate_graph(df, request.form.get("graph_title"))

    # Join the base and the requested path
    # could have done os.path.join, but safe_join ensures that files are not fetched from parent folders of the base folder
    absPath = safe_join(session_folder, reqPath)

    # Return 404 if path doesn't exist
    if not os.path.exists(absPath):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(absPath):
        return send_file(absPath)

    # Show directory contents
    def fObjFromScan(x):
        fileStat = x.stat()
        # return file information for rendering
        return {'name': x.name,
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
                'relPath': os.path.relpath(x.path, session_folder).replace("\\", "/"),
                }
    fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]
    # get parent directory url
    parentFolderPath = os.path.relpath(Path(absPath).parents[0], session_folder).replace("\\", "/")
    print(fileObjs)
    return render_template("upload_online.html", graph1JSON=graph1JSON, data={'files': fileObjs,
                                                 'parentFolder': parentFolderPath})

@app.route("/graphs_compare", methods=["GET", "POST"])
@login_required
def graphs_compare():
    """GUI for comparing plots"""
    # Display a list of uploaded user files and folder structure, select with checkboxes what graphs to compare and press compare
    #if request.method == 'POST':
    session_folders = db.execute("SELECT folder FROM sessions WHERE user_id=? AND NOT folder='' AND NOT folder='tmp'", session["user_id"])
    for folder in session_folders:
        print(os.listdir(folder['folder']))
    
    return render_template("graphs_compare.html")
    #print(session_folders)
    """
    # Read csv content with pandas into dataframe starting from row 18 (otherwise pandas can't read properly the data)
    try:
        df = pd.read_csv(os.path.join(session_folder, filename), skiprows=18)
    except:
        return render_template("upload_online.html")
    
    # Change column names in dataframe to more intuitive
    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
    
    # Generate JSON graph from dataframe
    graph1JSON = generate_graph(df, request.form.get("graph_title"))


    return render_template("upload_online.html", graph1JSON=graph1JSON)
    """

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

        # Check if user has opened session to continue uploads
        try:
            session["session"] = db.execute("SELECT name FROM sessions WHERE is_open=1 AND user_id=?", session['user_id'])[0]['name']
        except:
            return redirect("/")
        print(session["session"])
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


@app.route("/new_session", methods=["GET", "POST"])
@login_required
def new_session():
    if request.method == "POST":
        session_name = request.form.get("session_name")
        session_desc = request.form.get("session_description")

        try:
            db.execute("INSERT INTO sessions (name, description, user_id, timestamp, is_open, folder) VALUES(?, ?, ?, DATETIME('now','localtime'), 1, 'tmp')", session_name, session_desc, session["user_id"])
        except:
            apology("Can't open new session", 400)
        session["session"] = db.execute("SELECT name FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])[0]['name']
        db.execute("UPDATE sessions SET folder = ? WHERE user_id=? AND is_open=1", create_test_session_folder(), session["user_id"])
        return redirect("/upload_online")

@app.route("/close_session", methods=["GET", "POST"])
@login_required
def close_session():
    if request.method == "POST":
        try:
            db.execute("UPDATE sessions SET is_open=0 WHERE user_id=? AND is_open=1", session["user_id"])
        except:
            apology("Can't close session", 400)
        # Clear session name from session dictionary (used to display session in the header)
        session.pop("session")

        return redirect("/")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_test_session_folder():
    # Get path to current folder (app.py)
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Get username from SQL Database based on session user_id
    username = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])[0]["username"]
    
    # Get user_folder absolute address
    user_folder = os.path.join(basedir, app.config['UPLOAD_FOLDER'], username)
    
    # Create a folder user private folder if not exists already
    if not os.path.exists(user_folder): 
        os.makedirs(user_folder)
    
    # Get session_folder absolute address
    session_folder = os.path.join(basedir, app.config['UPLOAD_FOLDER'], username, session["session"] + "_" + datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
    
    # Create a session folder inside private folder if not exists already
    if not os.path.exists(session_folder): 
        os.makedirs(session_folder)
    
    return session_folder


# route handler
@app.route('/reports/', defaults={'reqPath': ''})
@app.route('/reports/<path:reqPath>')
def getFiles(reqPath):
    # Get session folder path from SQL database
    FolderPath = db.execute("SELECT folder FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])[0]["folder"]
    
    # Join the base and the requested path
    # could have done os.path.join, but safe_join ensures that files are not fetched from parent folders of the base folder
    absPath = safe_join(FolderPath, reqPath)

    # Return 404 if path doesn't exist
    if not os.path.exists(absPath):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(absPath):
        return send_file(absPath)

    # Show directory contents
    def fObjFromScan(x):
        fileStat = x.stat()
        # return file information for rendering
        return {'name': x.name,
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
                'relPath': os.path.relpath(x.path, FolderPath).replace("\\", "/"),
                }
    fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]
    # get parent directory url
    parentFolderPath = os.path.relpath(Path(absPath).parents[0], FolderPath).replace("\\", "/")
    return render_template('files.html', data={'files': fileObjs,
                                                 'parentFolder': parentFolderPath})



if __name__ == '__main__':
    app.run()