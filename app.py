#!/usr/bin/python3

import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, safe_join, send_file, abort, send_from_directory
from pathlib import Path
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
#import time
import json
import pandas as pd
import plotly
import plotly.express as px
import datetime
#import pyvisa
#import requests


from helpers import apology, login_required, generate_graph, getIconClassForFilename, generate_multiple_graphs, get_csv_from_spectrum, delete_folder, evaluate_scores

""" OPTION: connect to spectrum via VISA
# Configure Spectrum Analyzer Keysight
# Alter this host name, or IP address, in the line below to accommodate your specific instrument
host = 'k-n5245b-81275' # Or you could utilize an IP address.

# Alter the socket port number in the line below to accommodate your 
# specific instrument socket port. Traditionally, most Keysight Technologies, 
# Agilent Technologies, LAN based RF instrumentation socket ports use 5025. 
# Refer to your specific instrument User Guide for additional details.
port = 5025
"""

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
    """This is main page with EMC Lab picture and program version"""
    return render_template("index.html", graph1JSON=1)

@app.route("/upload_online", methods=["GET", "POST"], defaults={'reqPath': ''})
@app.route('/upload_online/<path:reqPath>')
@login_required
def upload_online(reqPath):
    """GUI for adding plots one-by-one"""

    # Check if there is any unclosed test session for current user, if none - render a new session page
    try:
        session_is_open = db.execute("SELECT is_open FROM sessions WHERE is_open=1 AND user_id=?", session["user_id"])[0]["is_open"]
    except:
        # Block below is converting SQLite3 query to JSON format in order to pass it to the page renderer and being able to use it easily to prefill session data in EDIT functuin
        # Read user's session table from database
        user_sessions_table = db.execute("SELECT * FROM sessions WHERE user_id=?", session["user_id"]) # user_sessions_table is passed to the renderer as well for proper session table display on upload_online page
        # Convert the list of dictionaries to a JSON object
        json_user_sessions_table = json.dumps(user_sessions_table)
        # Print or use the JSON data as needed
        #print(json_user_sessions_table)
        return render_template("new_session.html", user_sessions_table=user_sessions_table, json_user_sessions_table=json_user_sessions_table, enumerate=enumerate)
    session_folder = db.execute("SELECT folder FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])[0]["folder"]
    # TODO Check possible bug when if the database is transferred to another server or folder - will session_folder be accessible? Need to make sure what is stored in database is relative to the app.py folder and not absolute pass
    session_id = db.execute("SELECT id FROM sessions WHERE user_id=? and is_open=1", session["user_id"])[0]["id"]
    # Create an empty JSON graph object
    graph1JSON = []

    if request.method == 'POST':
        # Check if there are special characters in inputs (e.g. when user types "/" it may cause creating wrong folder path) later, can add more to the special_characters list
        special_characters = "\/"
        if any(c in special_characters for c in str(request.form.get("comment"))):
            flash('/ and \ symbols in comment are not allowed')
            return redirect(request.url)
        if any(c in special_characters for c in str(request.form.get("model"))):
            flash('/ and \ symbols in model are not allowed')
            return redirect(request.url)
        if any(c in special_characters for c in str(request.form.get("layout"))):
            flash('/ and \ symbols in layout are not allowed')
            return redirect(request.url)
        

        if request.form['cl_ol'] == 'close_loop' or request.form['cl_ol'] == 'open_loop': # for regulat measurement (not noise floor)
            # Ensure model was submitted
            if not request.form.get("model"):
                flash('Must specify Model')
                return redirect(request.url)

            # Ensure model was submitted
            if not request.form.get("layout"):
                flash('Must specify layout')
                return redirect(request.url)

            # Check power supply voltage was submitted
            if not request.form.get("v_ps"):
                flash('Must specify power supply voltage (Vps)')
                return redirect(request.url)
            
            # Check load resistor value was submitted
            if not request.form.get("r_load"):
                flash('Must specify load resistor')
                return redirect(request.url)    

            # Introduce working point variables dict
            curr_wp = {
                    "model": request.form.get("model"),
                    "layout": request.form.get("layout"),
                    "is_potted": 1 if request.form.get("potted")=="potted" else 0,
                    "cl_ol": request.form['cl_ol'],
                    "v_ps": float(request.form.get("v_ps")),
                    "i_lim_ps": 0,
                    "r_load": float(request.form.get("r_load")),
                    "dc": 0,
                    "mode": "none",
                    "power_in": 0,
                    "sas_ser": 1,
                    "sas_par": 100,
                    "i_out": 0,
                    "v_out": 0,
                    "v_in": 0,
                    "i_in": 0,
                    "eff": 0.98,
                    "user_comment": request.form.get("comment"),
                    "filename": "none",
                    "is_final": False,  # true will mean graph will be visible via dash viewing application
                    "inst_address": request.form.get("inst_address")
                }
        elif request.form['cl_ol'] == 'noise_floor': # if noise floor is measured, insert appropriate values into curr_wp (for plots names and table representation)
            curr_wp = {
                "model": 'Noise Floor',
                "layout": 'Noise Floor',
                "is_potted": 0,
                "cl_ol": request.form['cl_ol'],
                "v_ps": 0,
                "i_lim_ps": 0,
                "r_load": 0,
                "dc": 0,
                "mode": 'Noise Floor',
                "power_in": 0,
                "sas_ser": 1,
                "sas_par": 100,
                "i_out": 0,
                "v_out": 0,
                "v_in": 0,
                "i_in": 0,
                "eff": 0.98,
                "user_comment": request.form.get("comment"),
                "filename": "none",
                "is_final": False,  # true will mean graph will be visible via dash viewing application
                "inst_address": request.form.get("inst_address")
            }
        elif request.form['cl_ol'] == 'safety':
            # Ensure model was submitted
            if not request.form.get("model"):
                flash('Must specify Model')
                return redirect(request.url)

            # Ensure model was submitted
            if not request.form.get("layout"):
                flash('Must specify layout')
                return redirect(request.url)

            # Check power supply voltage was submitted
            if not request.form.get("v_ps"):
                flash('Must specify power supply voltage (Vps)')
                return redirect(request.url)
            
            # Introduce working point variables dict
            curr_wp = {
                "model": request.form.get("model"),
                "layout": request.form.get("layout"),
                "is_potted": 1 if request.form.get("potted")=="potted" else 0,
                "cl_ol": request.form['cl_ol'],
                "v_ps": float(request.form.get("v_ps")),
                "i_lim_ps": 0,
                "r_load": 0,
                "dc": 0,
                "mode": "none",
                "power_in": 0,
                "sas_ser": 1,
                "sas_par": 100,
                "i_out": 0,
                "v_out": 0,
                "v_in": 0,
                "i_in": 0,
                "eff": 0.98,
                "user_comment": request.form.get("comment"),
                "filename": "none",
                "is_final": False,  # true will mean graph will be visible via dash viewing application
                "inst_address": request.form.get("inst_address")
            }

        # Check inputs specific for close_loop:
        if request.form['cl_ol'] == 'close_loop':
            if not request.form.get("i_lim_ps"):
                flash('Must specify power supply current limit (I_lim_ps)')
                return redirect(request.url)
            
            # Calculate working point parameters
            curr_wp["i_lim_ps"] = float(request.form.get("i_lim_ps"))
            curr_wp["v_in"] = curr_wp["v_ps"] - (curr_wp["i_lim_ps"] - curr_wp["v_ps"] / curr_wp["sas_par"]) * curr_wp["sas_ser"]
            curr_wp["power_in"] = curr_wp["i_lim_ps"] * curr_wp["v_ps"] - pow((curr_wp["v_ps"] / curr_wp["sas_par"]), 2) * curr_wp["sas_par"] - pow((curr_wp["i_lim_ps"] - curr_wp["v_ps"] / curr_wp["sas_par"]), 2) * curr_wp["sas_ser"]
            curr_wp["v_out"] = pow(curr_wp["power_in"] * curr_wp["eff"] * curr_wp["r_load"], 0.5) 
            curr_wp["i_out"] = pow(curr_wp["power_in"] * curr_wp["eff"] / curr_wp["r_load"], 0.5)
            curr_wp["i_in"] = curr_wp["i_lim_ps"] - curr_wp["v_in"] / ( curr_wp["sas_par"] + curr_wp["sas_ser"] )
            
            # Determine operational mode
            if curr_wp["v_out"] / curr_wp["v_in"] > 1.02:
                curr_wp["dc"] = (curr_wp["v_out"] - curr_wp["v_in"]) / curr_wp["v_out"]
                curr_wp["mode"] = "Boost"
            elif curr_wp["v_out"] / curr_wp["v_in"] > 0.98:
                curr_wp["mode"] = "Buck-Boost"
                curr_wp["dc"] = curr_wp["v_out"] / curr_wp["v_in"]
            else:
                curr_wp["dc"] = curr_wp["v_out"] / curr_wp["v_in"]
                curr_wp["mode"] = "Buck"
        elif request.form['cl_ol'] == 'open_loop': # If open loop is selected, check inputs specific for open_loop:
            if not request.form.get("dc"):
                flash('Must specify duty cycle')
                return redirect(request.url)
            if not request.form.get("mode"):
                flash('Must specify working mode')
                return redirect(request.url)                 
            # Get user input of duty cycle and operational mode and save into curr_wp dict
            curr_wp["dc"] = float(request.form.get("dc"))
            curr_wp["mode"] = request.form.get("mode")
            
            # Perform calculations based on user-selected operational mode
            if curr_wp["mode"] == "Buck":
                curr_wp["v_out"] = curr_wp["v_ps"] * curr_wp["dc"]
            elif curr_wp["mode"] == "Boost":
                curr_wp["v_out"] = curr_wp["v_ps"] / (1 - curr_wp["dc"])
            elif curr_wp["mode"] == "Do_Nothing":
                curr_wp["v_out"] = 0
            # Complete remaining calculations for open loop operation
            if curr_wp["v_out"] > 0:
                curr_wp["power_in"] = pow(curr_wp["v_out"], 2) / curr_wp["r_load"] / curr_wp["eff"]
                curr_wp["i_out"] = curr_wp["v_out"] / curr_wp["r_load"]
                curr_wp["i_in"] = curr_wp["power_in"] / curr_wp["v_ps"]
            curr_wp["v_in"] = curr_wp["v_ps"]
        elif request.form['cl_ol'] == 'safety':
            curr_wp["v_in"] = curr_wp["v_ps"]
            curr_wp["i_out"] = 0
            curr_wp["i_in"] = 0.05
            curr_wp["mode"] = "Safety"
            curr_wp["v_out"] = 1.0
            curr_wp["dc"] = curr_wp["v_out"] / curr_wp["v_in"]
            curr_wp["power_in"] = curr_wp["i_in"] * curr_wp["v_in"]

        # Round all numbers in curr_wp dict to two decimal points
        for key in curr_wp:
            if type(curr_wp[key]) == float or type(curr_wp[key]) == int:
                curr_wp[key] = round(curr_wp[key], 2)

        # Store all user input form data in user session param (to be used after as a starting point when page is refreshed)
        session["curr_wp"] = curr_wp

        file = request.files['file']

        # Check if csv file selected and whether instrument http address is specified
        if not curr_wp['inst_address'] and 'file' not in request.files:
            flash('Please chose file or provide instrument IP address')
            return redirect(request.url)
        # If file is selected - use file upload as a raw data source
        elif 'file' in request.files and file.filename != '':
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
        # If data in -1 chamber format inserted
        elif request.form.get("minus_1_data"):
            
            txt_data = request.form.get("minus_1_data")
            
            validity_check = "TRACE	1001"
            if not validity_check in txt_data:
                flash('No correct -1 chamber data format detected')
                return redirect(request.url)

            if not request.form['cl_ol'] == 'noise':
                filename_head = curr_wp["model"] + '_' + ("Potted_" if curr_wp["is_potted"] else "Not_potted_") + curr_wp["layout"] + '_WP_' + curr_wp["cl_ol"] + '_' + curr_wp["mode"] + '_Power_' + str(curr_wp["power_in"]) + '_' + curr_wp["user_comment"]
            else:
                filename_head = curr_wp["model"] + '_' + curr_wp["user_comment"]
            filename_tail = '.txt'
            filename = os.path.join('%s%s' % (filename_head, filename_tail))

            # rename if filename already exists
            count = 0
            while os.path.exists(os.path.join(os.getcwd(), session_folder, filename)):
                count += 1
                filename = os.path.join('%s-%d%s' % (filename_head, count, filename_tail))
            file = open(os.path.join(os.getcwd(), session_folder, filename), 'w')
            file.write(txt_data)
            
            
            df = pd.read_csv(os.path.join(session_folder, filename), delim_whitespace=True, index_col=False, skiprows=26, skipfooter=15)
            df.columns = ["MHz", "dBuV"]
            #print(df.head(50))
            # Store working point details and file location in SQL Database
            try:
                db.execute("INSERT INTO graphs (session_id, model, layout, is_cl, v_in, v_out, i_in, i_load, dc, power, mode, comment, filename, timestamp, is_potted) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session_id,
                     curr_wp["model"], curr_wp["layout"], 1 if curr_wp["cl_ol"] == "close_loop" else  0, curr_wp["v_in"], curr_wp["v_out"], curr_wp["i_in"], curr_wp["i_out"], curr_wp["dc"],
                      curr_wp["power_in"], curr_wp["mode"], curr_wp["user_comment"], filename, datetime.datetime.now().strftime("%H:%M:%S_%d%m%Y"), curr_wp["is_potted"])
                flash("Result was successfully added")
            except:
                flash("Error in adding data to database")
            return redirect(request.url)
        # If no file was selected or no data in -1 chamber format inserted by user - try to download csv directly from spectrum analyzer
        elif curr_wp['inst_address']:
            #flash('Getting .csv from spectrum')
            csv_data = get_csv_from_spectrum(curr_wp['inst_address'])
            if csv_data == "Can't reach instrument":
                flash('Instrument not reachable at specified address')
                return redirect(request.url)
            if not request.form['cl_ol'] == 'noise':
                filename_head = curr_wp["model"] + '_' + ("Potted_" if curr_wp["is_potted"] else "Not_potted_") + curr_wp["layout"] + '_WP_' + curr_wp["cl_ol"] + '_' + curr_wp["mode"] + '_Power_' + str(curr_wp["power_in"]) + '_' + curr_wp["user_comment"]
            else:
                filename_head = curr_wp["model"] + '_' + curr_wp["user_comment"]
            filename_tail = '.csv'
            filename = os.path.join('%s%s' % (filename_head, filename_tail))
            
            # rename if filename already exists
            count = 0
            while os.path.exists(os.path.join(os.getcwd(), session_folder, filename)):
                count += 1
                filename = os.path.join('%s-%d%s' % (filename_head, count, filename_tail))
            file = open(os.path.join(os.getcwd(), session_folder, filename), 'w')
            file.write(csv_data)
            flash("Result was successfully added")
            # Store working point details and file location in SQL Database
            db.execute("INSERT INTO graphs (session_id, model, layout, is_cl, v_in, v_out, i_in, i_load, dc, power, mode, comment, filename, timestamp, is_potted) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session_id,
                     curr_wp["model"], curr_wp["layout"], 1 if curr_wp["cl_ol"] == "close_loop" else  0, curr_wp["v_in"], curr_wp["v_out"], curr_wp["i_in"], curr_wp["i_out"], curr_wp["dc"],
                      curr_wp["power_in"], curr_wp["mode"], curr_wp["user_comment"], filename, datetime.datetime.now().strftime("%H:%M:%S_%d%m%Y"), curr_wp["is_potted"])
            return redirect(request.url)


            
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        """ SECTION without get data from spectrum  
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
        """
        if file and allowed_file(file.filename):
            filename_head = secure_filename(file.filename)
            if not request.form['cl_ol'] == 'noise':
                filename_head = curr_wp["model"] + '_' + ("Potted_" if curr_wp["is_potted"] else "Not_potted_") + curr_wp["layout"] + '_WP_' + curr_wp["cl_ol"] + '_' + curr_wp["mode"] + '_Power_' + str(curr_wp["power_in"]) + '_' + curr_wp["user_comment"]
            else:
                filename_head = curr_wp["model"] + '_' + curr_wp["user_comment"]
            filename_tail = '.csv'
            filename = os.path.join('%s%s' % (filename_head, filename_tail))
            # rename if filename already exists
            count = 0
            while os.path.exists(os.path.join(os.getcwd(), session_folder, filename)):
                count += 1
                filename = os.path.join('%s-%d%s' % (filename_head, count, filename_tail))
            file.save(os.path.join(os.getcwd(), session_folder, filename))
            flash("Result was successfully added")
            # Store working point details and file location in SQL Database
            db.execute("INSERT INTO graphs (session_id, model, layout, is_cl, v_in, v_out, i_in, i_load, dc, power, mode, comment, filename, timestamp, is_potted) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session_id,
                     curr_wp["model"], curr_wp["layout"], 1 if curr_wp["cl_ol"] == "close_loop" else  0, curr_wp["v_in"], curr_wp["v_out"], curr_wp["i_in"], curr_wp["i_out"], curr_wp["dc"],
                      curr_wp["power_in"], curr_wp["mode"], curr_wp["user_comment"], filename, datetime.datetime.now().strftime("%H:%M:%S_%d%m%Y"), curr_wp["is_potted"])

            return redirect(request.url)
    
    # Join the base and the requested path
    # could have done os.path.join, but safe_join ensures that files are not fetched from parent folders of the base folder
    absPath = safe_join(os.getcwd(), session_folder, reqPath)
    
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
    
    # Read current session graphs data from SQL
    try:
        session_results_table = db.execute("SELECT * FROM graphs WHERE session_id=?", session_id)
    except:
        session_results_table = {}
    # Read session traces scores
    session_scores_table = []
    for dict in session_results_table:
        try:
            session_scores_table.append(db.execute("SELECT * FROM scores WHERE graph_id=?", dict["id"])[0])
        except:
            session_scores_table.append({})
    #print(session_results_table)
    # TODO add is_final flag (or leave final flag assesible from DASH)
    # TODO Consider plotting graphs only if button is pressed / V is marked on ALL/some graphs
    # TODO Create sessions page with option to resume specific session or just plot the CSVs from that session
    # TODO add multiple files upload page - upload offline or similar
    #print(session["curr_wp"]['cl_ol'])

    # Read session type from database
    try:
        session_type = db.execute("SELECT type FROM sessions WHERE id=?", session_id)
    except:
        session_type = 'none'
        flash("Error in reading session type from database")
    try:
        session_lab = db.execute("SELECT lab FROM sessions WHERE id=?", session_id)
    except:
        session_lab = 'none'
        flash("Error in reading session facility from database")
    #print(session_results_table)
    #print(session_scores_table)
    # Generate JSON graph from current session files object
    graph1JSON = generate_multiple_graphs(session_results_table, os.path.join(os.getcwd(), session_folder), session_type, session_lab, session_scores_table)
    return render_template("upload_online.html", graph1JSON=graph1JSON, data={'files': fileObjs,
                                                 'parentFolder': parentFolderPath}, curr_wp=session["curr_wp"], session_results_table=session_results_table, enumerate=enumerate, session_scores_table=session_scores_table)

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
        session["user_name"] = rows[0]["username"]
        # Create an empty dict for storing curr_wp data in user session file
        session["curr_wp"] = {}
        
        try:
            session["id"] = db.execute("SELECT id FROM sessions WHERE is_open=1 AND user_id=?", session['user_id'])[0]['id']
        except:
            return redirect("/")
        # Check if user has opened session to continue uploads
        try:
            session["session"] = db.execute("SELECT name FROM sessions WHERE is_open=1 AND user_id=?", session['user_id'])[0]['name']
        except:
            return redirect("/")

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
        cables_orientation = request.form.get("cables_orientation")
        cmc_box = request.form.get("cmc_box")
        if request.form.get("beads"):
            beads = request.form.get("beads")
        else:
            beads = "None"
        load = request.form.get("load")
        attenuator = request.form.get("6dB")
        if request.form.get("comment"):
            comment = request.form.get("comment")
        else:
            comment = "None"

        if request.form.get("clamp_in") and request.form.get("clamp_out"):
            clamp = "In and Out"
        elif request.form.get("clamp_in"):
            clamp = "In Only"
        elif request.form.get("clamp_out"):
            clamp = "Out Only"
        else:
            clamp = "None"

        special_characters = "\/"

        if (not session_name) or (not session_desc) or any(c in special_characters for c in session_name) or any(c in special_characters for c in session_desc):
            #print("enter if")
            flash("Please provide session name and description (/\ symbols are not allowed)")
            return render_template("new_session.html", user_sessions_table=db.execute("SELECT * FROM sessions WHERE user_id=?", session["user_id"]), enumerate=enumerate)

        if request.form.get("lab") == 'modiin':
            #print("Modiin")
            session_lab = "Modiin"
        elif request.form.get("lab") == 'hamada':
            #print("hamada")
            session_lab = "-1 Floor HaMada"
        elif request.form.get("lab") == 'qualitek':
            #print("qualitek")
            session_lab = "Qualitek"
        
        test_type = request.form.get("type")

        try:
            db.execute("INSERT INTO sessions (type, name, description, user_id, timestamp, is_open, folder, lab, cables_orient, cmc_box, clamps, beads, load_type, attenuator, setup_comment) VALUES(?, ?, ?, ?, DATETIME('now','localtime'), 1, 'tmp', ?, ?, ?, ?, ?, ?, ?, ?)", test_type, session_name, session_desc, session["user_id"], session_lab, cables_orientation, cmc_box, clamp, beads, load, attenuator, comment)
        except:
            apology("Can't open new session", 400)
        session["session"] = db.execute("SELECT name FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])[0]['name']
        db.execute("UPDATE sessions SET folder = ? WHERE user_id=? AND is_open=1", create_test_session_folder(), session["user_id"])
        try:
            session["id"] = db.execute("SELECT id FROM sessions WHERE is_open=1 AND user_id=?", session['user_id'])[0]['id']
        except:
            apology("Can't save session id", 400)
        return redirect("/upload_online")

@app.route("/resume_session", methods=["GET", "POST"])
@login_required
def resume_session():
    if request.method == "POST":
        try:
            db.execute("UPDATE sessions SET is_open = 1 WHERE id=?", request.form.get("resume_session"))
        except:
            apology("Can't resume session", 400)
        
        session["session"] = db.execute("SELECT name FROM sessions WHERE user_id=? AND is_open=1", session["user_id"])[0]['name']
        #db.execute("UPDATE sessions SET is_open=0 WHERE user_id=? AND is_open=1", session["user_id"])
        #session.pop("session")
        try:
            session["id"] = db.execute("SELECT id FROM sessions WHERE is_open=1 AND user_id=?", session['user_id'])[0]['id']
        except:
            apology("Can't resume session", 400)
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
    #basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Get username from SQL Database based on session user_id
    try:
        username = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])[0]["username"]
    except:
        apology("Can't read user id", 400)

    try:
        session_id = db.execute("SELECT id FROM sessions WHERE is_open=1 AND user_id=?", session['user_id'])[0]['id']
    except:
        apology("Can't read session id", 400)
    # Get user_folder absolute address
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    
    # Create a folder user private folder if not exists already
    if not os.path.exists(user_folder): 
        os.makedirs(user_folder)
    
    # Get session_folder absolute address
    #session_folder = os.path.join(app.config['UPLOAD_FOLDER'], username, session["session"] + "_" + datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], username, str(session_id))
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


@app.route('/toggle_final', methods=['GET', 'POST'])
@login_required
def toggle_final():
    if request.method == "POST":
        is_final = int(db.execute("SELECT is_final FROM graphs WHERE id=?", request.form.get("toggle"))[0]["is_final"])
        #print(is_final)
        try:
            db.execute("UPDATE graphs SET is_final = ? WHERE id=?", (0 if is_final else 1), request.form.get("toggle"))
            if is_final==0:
                flash("Successfully set as final")
            else:
                flash("Successfully removed from finals")
        except:
            flash("Can't set final flag")
    return redirect("/upload_online")

# Update trance details in database
@app.route('/update_database', methods=['GET', 'POST'])
@login_required
def update_database():
    if request.method == "POST":
        #is_final = int(db.execute("SELECT is_final FROM graphs WHERE id=?", request.form.get("toggle"))[0]["is_final"])
        #print(is_final)
        data_to_update = {
                "trace_id": request.form.get("trace_id"),
                "model": request.form.get("model_"),
                "layout": request.form.get("layout_"),
                "is_potted": 1 if request.form.get("potted_")=="potted" else 0,
                "is_cl": 1 if request.form.get("cl_ol")=="cl" else 0,
                "power": float(request.form.get("power_")),
                "v_in": float(request.form.get("v_in")),
                "v_out": float(request.form.get("v_out")),
                "i_in": float(request.form.get("i_in")),
                "i_out": float(request.form.get("i_out")),
                "dc": float(request.form.get("dc_")),
                "mode": request.form.get("mode_"),
                "comment": request.form.get("comment_")
            }
        
        original_data = db.execute("SELECT * FROM graphs WHERE id=?", data_to_update['trace_id'])
        
        try:
            #db.execute("UPDATE graphs SET model = data_to_update['model'], layout = data_to_update['layout'], is_potted = data_to_update['is_potted'], is_cl = data_to_update['is_cl'],  power = data_to_update['power'], v_in = data_to_update['v_in'], v_out = data_to_update['v_out'], i_in = data_to_update['i_in'], i_load = data_to_update['i_out'], dc = data_to_update['dc'], mode = data_to_update['mode'], comment = data_to_update['comment'] WHERE id=?", data_to_update['trace_id'])
            #db.execute("UPDATE graphs SET (model, layout, is_potted, is_cl,  power, v_in, v_out, i_in, i_load, dc, mode, comment) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) WHERE id=?", data_to_update['model'], data_to_update['layout'], data_to_update['is_potted'], data_to_update['is_cl'], data_to_update['power'], data_to_update['v_in'], data_to_update['v_out'], data_to_update['i_in'], data_to_update['i_out'], data_to_update['dc'], data_to_update['mode'], data_to_update['comment'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET model=? WHERE id=?", data_to_update['model'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET layout=? WHERE id=?", data_to_update['layout'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET is_potted=? WHERE id=?", data_to_update['is_potted'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET is_cl=? WHERE id=?", data_to_update['is_cl'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET power=? WHERE id=?", data_to_update['power'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET v_in=? WHERE id=?", data_to_update['v_in'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET v_out=? WHERE id=?", data_to_update['v_out'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET i_in=? WHERE id=?", data_to_update['i_in'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET i_load=? WHERE id=?", data_to_update['i_out'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET dc=? WHERE id=?", data_to_update['dc'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET mode=? WHERE id=?", data_to_update['mode'], data_to_update['trace_id'])
            db.execute("UPDATE graphs SET comment=? WHERE id=?", data_to_update['comment'], data_to_update['trace_id'])

            flash("Successfully updated trace #" + data_to_update['trace_id'] +" description in database!")
        except:
            flash("Can't update database, please contact Eyal/Ilya")
        #print(data_to_update)
        #print(db.execute("SELECT * FROM graphs WHERE id=?", data_to_update['trace_id']))
    return redirect("/upload_online")

@app.route('/update_sessions_database', methods=['GET', 'POST'])
@login_required
def update_session():
    if request.method == "POST":
        #is_final = int(db.execute("SELECT is_final FROM graphs WHERE id=?", request.form.get("toggle"))[0]["is_final"])
        #print(is_final)
        
        # Database-consistant Clamp naming convention  
        if request.form.get("clamp_in_") and request.form.get("clamp_out_"):
            clamp = "In and Out"
        elif request.form.get("clamp_in_"):
            clamp = "In Only"
        elif request.form.get("clamp_out_"):
            clamp = "Out Only"
        else:
            clamp = 'Not Specified'
        
        
        data_to_update = {
                "id": int(request.form.get("session_id")),
                "lab": request.form.get("lab_"),
                "type": request.form.get("type_"),
                "name": request.form.get("session_name_"),
                "description": request.form.get("session_description_"),
                "cables_orient": 'Not Specified' if request.form.get("cables_orientation")==None else request.form.get("cables_orientation"),
                "clamps": clamp,
                "cmc_box": 'Yes' if request.form.get("cmc_box_") else 0,
                "beads": 'Not Specified' if request.form.get("beads_")==None else request.form.get("beads_"),
                "load_type": 'Not Specified' if request.form.get("load")==None else request.form.get("load"),
                "attenuator": request.form.get("6dB_"),
                "setup_comment": 'Not Specified' if request.form.get("comment_")==None else request.form.get("comment_")
            }
        
        #print(data_to_update)
        #original_data = db.execute("SELECT * FROM sessions WHERE id=?", data_to_update['id'])
        #print(original_data)
        
        
        try:
            for key, value in data_to_update.items():
                db.execute(f"UPDATE sessions SET {key}=? WHERE id=?", value, data_to_update['id'])
            flash("Successfully updated session #" + str(data_to_update['id']) +" description in database!")
        except:
            flash("Can't update database, please contact Eyal/Ilya")
        


        #print(data_to_update)
        #print(db.execute("SELECT * FROM graphs WHERE id=?", data_to_update['trace_id']))
    return redirect("/upload_online")


@app.route('/delete_item', methods=['GET', 'POST'])
@login_required
def delete_item():
    if request.method == "POST":
        session_folder = db.execute("SELECT folder FROM sessions WHERE id=?", session["id"])[0]['folder']
        file_name = db.execute("SELECT filename FROM graphs WHERE id=?", request.form.get("delete"))[0]['filename']
        os.remove(os.path.join(os.getcwd(), session_folder, file_name))
        db.execute("DELETE FROM graphs WHERE id=?", request.form.get("delete"))
    return redirect("/upload_online")


@app.route('/delete_session', methods=['GET', 'POST'])
@login_required
def delete_session():
    if request.method == "POST":
        #print(request.form.get("delete_session"))
        session_folder = db.execute("SELECT folder FROM sessions WHERE id=?", request.form.get("delete_session"))[0]['folder']
        #print(session_folder)
        try:
            db.execute("DELETE FROM sessions WHERE id=?", request.form.get("delete_session"))
        except:
            flash("Can't delete session from db, please contact Eyal/Ilya")
        try:
            delete_folder(session_folder)
            flash("Successfully deleted session #" + str(request.form.get("delete_session")) +" and it's contents!")
        except:
            flash("Can't delete folder, please contact Eyal/Ilya")
        #file_name = db.execute("SELECT filename FROM graphs WHERE id=?", request.form.get("delete"))[0]['filename']
        #os.remove(os.path.join(os.getcwd(), session_folder, file_name))
        
    return redirect("/upload_online")

@app.route('/calculate_scores', methods=['GET', 'POST'])
@login_required
def calculate_scores():
    if request.method == "POST":
        
        # Read current session id
        try:
            session_type = db.execute("SELECT type FROM sessions WHERE user_id=? and is_open=1", session["user_id"])[0]["type"]
            session_lab = db.execute("SELECT lab FROM sessions WHERE user_id=? and is_open=1", session["user_id"])[0]["lab"]
        except:
            return apology("Can't read from DB", 400)
        #print(session_type)
        if session_type == 'RE' and (session_lab == 'Modiin' or session_lab == 'Qualitek'):
            session_id = db.execute("SELECT id FROM sessions WHERE user_id=? and is_open=1", session["user_id"])[0]["id"]
            session_folder = db.execute("SELECT folder FROM sessions WHERE id=?", session_id)[0]["folder"]
            
            #print(session_id)
            # Create list of dictionaries containing trace ids
            session_traces = db.execute("SELECT id, filename FROM graphs WHERE session_id=?", session_id)
            if not session_traces:
                flash("Please add traces before executing calculation")
                return redirect("/upload_online")
            # Calculate scores for this IDs and add to list
            try:
                session_traces_ids_w_scores = evaluate_scores(session_traces, session_folder)
            except:
                flash("Invalid data")
                return redirect("/upload_online")
            for dict in session_traces_ids_w_scores:
                if db.execute("SELECT * FROM scores WHERE graph_id=?", int(dict['id'])):
                    try:
                        #print("Enter first if")
                        db.execute("UPDATE scores SET '30-1000MHz'=? WHERE graph_id=?", float(dict['30-1000MHz_score']), int(dict['id']))
                        db.execute("UPDATE scores SET '30-60MHz'=? WHERE graph_id=?", float(dict['30-60MHz_score']), int(dict['id']))
                        db.execute("UPDATE scores SET '60-100MHz'=? WHERE graph_id=?", float(dict['60-100MHz_score']), int(dict['id']))
                        db.execute("UPDATE scores SET '100-200MHz'=? WHERE graph_id=?", float(dict['100-200MHz_score']), int(dict['id']))
                        db.execute("UPDATE scores SET '200-400MHz'=? WHERE graph_id=?", float(dict['200-400MHz_score']), int(dict['id']))
                        db.execute("UPDATE scores SET '400-1000MHz'=? WHERE graph_id=?", float(dict['400-1000MHz_score']), int(dict['id']))
                    except:
                        return apology("Can't update existing scores in Database", 400)
                else:
                    #print("Enter second if")
                    try:
                        db.execute("INSERT INTO scores (graph_id,'30-1000MHz','30-60MHz','60-100MHz','100-200MHz','200-400MHz','400-1000MHz') VALUES(?, ?, ?, ?, ?, ?, ?)", int(dict['id']), float(dict['30-1000MHz_score']), float(dict['30-60MHz_score']), float(dict['60-100MHz_score']), float(dict['100-200MHz_score']), float(dict['200-400MHz_score']), float(dict['400-1000MHz_score']))
                        #flash("Added new scores to database")
                    except:
                        return apology("Can't add new scores in Database", 400)
            flash("Updated/added scores successfully")
                #print(f"Session ID {dict['id']} has the following scores: Total Score -> {dict['30-1000MHz_score']}; 30-60MHz -> {dict['30-60MHz_score']}; 30-60MHz -> {dict['30-60MHz_score']}; 60-100MHz -> {dict['60-100MHz_score']}; 100-200MHz -> {dict['100-200MHz_score']}; 200-400MHz -> {dict['200-400MHz_score']}; 400-1000MHz -> {dict['400-1000MHz_score']}")
        else:
            return apology("Scores calculation is only supported in RE mode in Modiin and Qualitek currently", 400)
        #add_scores_to_database()

        #session_scores = db.execute("SELECT id, filename FROM graphs WHERE session_id=?", session_id)
        #print(session_traces_ids_w_scores)

        
        
    return redirect("/upload_online")

@app.route('/static/<path:filename>', methods=['GET', 'POST'])
@login_required
def download(filename):

    # Send file named as requested in "filename" from folder "static"
    return send_from_directory(directory='static', filename=filename)


if __name__ == '__main__':
    #app.run(host="0.0.0.0")
    app.run(port=5002, debug=True)

    #app.run(host="0.0.0.0", debug=True)