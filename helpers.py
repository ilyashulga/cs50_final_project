import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
import json
import pandas as pd
import plotly
import plotly.express as px


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def generate_graph(df):
    """Generate graph in JSON format to be sent to JINJA and embedded inside html"""
    # Iterate over each row in Dataframe, calculate Max(Column 2, Column 3) or Max(Ver,Hor) on each row and insert into Column 1 or Max(Ver,Hor) column
    for row in range(len(df)):
        df.at[row,'Max(Ver,Hor)'] = max(df.at[row,'Hor'], df.at[row,'Ver'])
        df.at[row,'Frequency[MHz]'] = df.at[row,'Frequency[MHz]']/1000000
    
    # create xy chart using plotly library    
    fig = px.line(df, x='Frequency[MHz]', y='Max(Ver,Hor)', log_x=True)

    # Convery plotly fig to JSON object
    graphJSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

    return graphJSON

