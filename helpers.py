import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
import json
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pyvisa


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


def generate_graph(df, graph_title):
    """Generate graph in JSON format to be sent to JINJA and embedded inside html"""
    # Iterate over each row in Dataframe, calculate Max(Column 2, Column 3) or Max(Ver,Hor) on each row and insert into Column 1 or Max(Ver,Hor) column
    for row in range(len(df)):
        df.at[row,'Max(Ver,Hor)'] = max(df.at[row,'Hor'], df.at[row,'Ver'])
        df.at[row,'Frequency[MHz]'] = df.at[row,'Frequency[MHz]']/1000000
    
    # create xy chart using plotly library    
    fig = px.line(df, x='Frequency[MHz]', y='Max(Ver,Hor)', log_x=True, template="plotly_white", title='%s' % graph_title)

    # Convery plotly fig to JSON object
    graphJSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def generate_multiple_graphs(session_results_table, session_folder):
    """Generate multiple lines chart from csv files in folder location"""
    fig = go.Figure()
    
    # Read Limits.csv content with pandas into dataframe and add to graphs figure
    try:
        df = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "limits.csv"))
    except:
        return apology("Error in reading limits.csv file", 400)

    df.columns = ['Frequency[MHz]','CISPR11_RE_CLASS_B_Group_1', 'CISPR11_RE_CLASS_B_Group_1_Important']
    graph_name = 'Limit: CISPR11 RE CLASS B Group 1'
    fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_RE_CLASS_B_Group_1"], name=graph_name, mode="lines"))
    graph_name = 'Limit (important): CISPR11 RE CLASS B Group 1'
    fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_RE_CLASS_B_Group_1_Important"], name=graph_name, mode="lines"))
    if session_results_table:
        # Iterate over files passed as a file object
        for index, result in enumerate(session_results_table):
            # Introduce index for every result
            i = 0
            # Read each csv content with pandas into dataframe starting from row 18 (otherwise pandas can't read properly the data)
            try:
                df = pd.read_csv(os.path.join(session_folder, result["filename"]), skiprows=18)
            except:
                return apology("Error in reading CSV files", 400)
            #print(df.head())
            # Change column names in dataframe to more intuitive
            df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor']
            # Iterate over each file's rows and make required calculations/substitutions
            for row in range(len(df)):
                df.at[row,'Max(Ver,Hor)'] = max(df.at[row,'Hor'], df.at[row,'Ver'])
                df.at[row,'Frequency[MHz]'] = df.at[row,'Frequency[MHz]']/1000000
            # create xy chart using plotly library
            graph_name = str(index) + "." + result["model"] + " " + result["layout"] + " " + result["comment"] + " " + result["mode"] + " " + ("CL" if result["is_cl"]==1 else "OL") + " Vin=" + str(result["v_in"]) + "[V]" + " Iout=" + str(result["i_load"]) + "[A]" + " DC=" + str(result["dc"]) + " P=" + str(result["power"]) + "[W]"
            fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["Max(Ver,Hor)"], name=graph_name, mode="lines", visible='legendonly'))    
            #fig.add_trace(go.line(df, x='Frequency[MHz]', y='Max(Ver,Hor)', log_x=True, template="plotly_white"))
    # Change x-axis to log scale
    fig.update_xaxes(type="log")
    fig.update_xaxes(title_text='Frequency [MHz]',
                        title_font = {"size": 20},
                        title_standoff = 0)
    fig.update_yaxes(title_text='dBuV/m',
                        title_font = {"size": 20},
                        title_standoff = 5)
    fig.update_layout(#autosize=False,
                        minreducedwidth=250,
                        minreducedheight=1500,
                        #width=1500,
                        #height=1000,
                        legend=dict(
                            #yanchor="top",
                            y=-0.3,
                            #xanchor="left",
                            #x=0.01,
                            orientation='h'
                            ),
                        title={
                            'text': "Radiated Emission",
                            'y':0.9,
                            'x':0.5,
                            'xanchor': 'center',
                            'yanchor': 'top'}
                        )
    
    # Convery plotly fig to JSON object
    graphJSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def getIconClassForFilename(fName):
    fileExt = Path(fName).suffix
    fileExt = fileExt[1:] if fileExt.startswith(".") else fileExt
    fileTypes = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg", "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql", "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    fileIconClass = f"bi bi-filetype-{fileExt}" if fileExt in fileTypes else "bi bi-file-earmark"
    return fileIconClass


def open_connection(ip):

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource("TCPIP0::" + ip + "::inst0::INSTR")
    print(inst.query("*IDN?"))

def close_connection(rm, inst):
    rm.close()
    inst.close()


