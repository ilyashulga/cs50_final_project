import os
import urllib.parse

from flask import redirect, render_template, request, session, safe_join
from functools import wraps
import json
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pyvisa
import requests
import math


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

def generate_multiple_graphs(session_results_table, session_folder, session_type, session_lab, session_scores_table):
    """Generate multiple lines chart from csv files in folder location"""
    fig = go.Figure()
    #print (session_type)
    #print(session_type[0]['type'])
    if session_type[0]['type'] == 'RE':
        # Read Limits.csv content with pandas into dataframe and add to graphs figure (RE Limits)
        try:
            df = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "Limits.csv"))
        except:
            return apology("Error in reading limits.csv file", 400)

        df.columns = ['Frequency[MHz]','CISPR11_RE_CLASS_B_Group_1', 'CISPR11_RE_CLASS_B_Group_1_Important', 'CISPR11_RE_CLASS_A_Group_1_up_to_20kVA']
        graph_name = 'Limit: CISPR11 RE CLASS B Group 1'
        fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_RE_CLASS_B_Group_1"], name=graph_name, mode="lines"))
        graph_name = 'Limit (important): CISPR11 RE CLASS B Group 1'
        fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_RE_CLASS_B_Group_1_Important"], name=graph_name, mode="lines"))
        graph_name = 'Limit: CISPR11 RE CLASS A Group 1 <20kVA'
        fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_RE_CLASS_A_Group_1_up_to_20kVA"], name=graph_name, mode="lines", visible='legendonly'))
        graph_title = 'Radiated Emission'
        y_axis_units = 'dBuV/m'
    elif session_type[0]['type'] == 'CE':
        # Read Limits.csv content with pandas into dataframe and add to graphs figure (CE Limits)
        try:
            df = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "Limits_CE.csv"))
        except:
            return apology("Error in reading Limits_CE.csv file", 400)
        df.columns = ['Frequency[MHz]','CISPR11_CE_CLASS_B_Group_1_AVG', 'CISPR11_CE_CLASS_A_Group_1_AVG']
        graph_name = 'Limit: AVG CISPR11 CE CLASS B Group 1'
        fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_CE_CLASS_B_Group_1_AVG"], name=graph_name, mode="lines", visible='legendonly'))
        graph_name = 'Limit: AVG CISPR11 CE CLASS A Group 1'
        fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["CISPR11_CE_CLASS_A_Group_1_AVG"], name=graph_name, mode="lines"))
        graph_title = 'Conducted Emission'
        y_axis_units = 'dBuV'
    elif session_type[0]['type'] == 'Loop_Antenna':
        # Later will need to add Limits for Loop Antenna type tests
        graph_title = 'LF Radiated Emission (Loop Antenna)'
        y_axis_units = 'dBuA/m'
    if session_results_table:
        # Iterate over files passed as a file object
        for index, result in enumerate(session_results_table):
            # Introduce index for every result
            i = 0
            # Read each csv content with pandas into dataframe starting from row 18 or 45 (otherwise pandas can't read properly the data)
            if result["filename"].endswith('.csv'):
                try:
                    #print(session_lab[0]['lab'])
                    #df = pd.read_csv(os.path.join(session_folder, result["filename"]), skiprows=(45 if session_lab[0]['lab'] == '-1 Floor HaMada' else 18))
                    df = pd.read_csv(os.path.join(session_folder, result["filename"]), skiprows=18)
                    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor'] # Naming in case of data has 4 rows
                    #print(df.head())
                except:
                    df = pd.read_csv(os.path.join(session_folder, result["filename"]), skiprows=45)
                    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor','','',''] # Naming in case of data has 7 rows
                #print(df.head())
                # Change column names in dataframe to more intuitive
                
                #try: 
                #    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor','','',''] # Naming in case of data has 7 rows
                #except:
                #    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor'] # Naming in case of data has 4 rows
                # Iterate over each file's rows and make required calculations/substitutions
                for row in range(len(df)):
                    df.at[row,'Max(Ver,Hor)'] = max(df.at[row,'Hor'], df.at[row,'Ver'])
                    df.at[row,'Frequency[MHz]'] = df.at[row,'Frequency[MHz]']/1000000
            else:
                df = pd.read_csv(os.path.join(session_folder, os.path.join(session_folder, result["filename"])), delim_whitespace=True, index_col=False, skiprows=26, skipfooter=15)
                df.columns = ['Frequency[MHz]','Max(Ver,Hor)']
                #print(df.head(50))
            # create xy chart using plotly library
            if result["model"] != 'Noise Floor':
                #graph_name = str(index) + "." + result["model"] + " " + ("Potted" if result["is_potted"] else "Not_Potted") + " " + result["layout"] + " " + result["comment"] + " " + result["mode"] + " " + ("CL" if result["is_cl"]==1 else "OL") + " Vin=" + str(result["v_in"]) + "[V]" + " Iout=" + str(result["i_load"]) + "[A]" + " DC=" + str(result["dc"]) + " P=" + str(result["power"]) + "[W]"
                try:
                    score = "Score: " + str(session_scores_table[index]['30-1000MHz'])
                except:
                    score = ""
                graph_name = str(index) + "." + score + " " + result["model"] + " " + result["layout"] + " " + result["mode"] + " " + result["comment"] + " P=" + str(result["power"]) + "[W]"
            else:
                graph_name = str(index) + "." + result["model"] + " " + result["comment"]
            fig.add_trace(go.Scatter(x=df["Frequency[MHz]"], y=df["Max(Ver,Hor)"], name=graph_name, mode="lines", visible='legendonly'))    
            #fig.add_trace(go.line(df, x='Frequency[MHz]', y='Max(Ver,Hor)', log_x=True, template="plotly_white"))
    # Change x-axis to log scale
    fig.update_xaxes(type="log")
    fig.update_xaxes(title_text='Frequency [MHz]',
                        title_font = {"size": 22},
                        title_standoff = 0)
    fig.update_yaxes(title_text = y_axis_units,
                        title_font = {"size": 22},
                        title_standoff = 5)
    fig.update_layout(#autosize=False,
                        hoverdistance=-1,
                        hoverlabel_namelength=-1, # Needed to not shorten the name of the trace on hoover (together with hoverinfo='text' in fig.add_trace(go.Scatter... above)
                        hovermode="x unified",
                        #hovermode="x",
                        minreducedwidth=250,
                        minreducedheight=500,
                        #width=1500,
                        height=1000,
                        legend=dict(
                            #yanchor="top",
                            y=-0.1,
                            #xanchor="left",
                            #x=0.01,
                            orientation='h'
                            ),
                        title={
                            'text': graph_title,
                            'y':0.95,
                            'x':0.5,
                            'xanchor': 'center',
                            'yanchor': 'top'
                            },
                        font=dict(
                            family="Courier New",
                            size=16 
                            )

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
    #print(inst.query("*IDN?"))

def close_connection(rm, inst):
    rm.close()
    inst.close()

def delete_folder(folder_path):
    absPath = safe_join(os.getcwd(), folder_path)
    # Iterate over the files and subdirectories in the folder
    for filename in os.listdir(absPath):
        file_path = os.path.join(absPath, filename)
    
        # Check if the item is a file
        if os.path.isfile(file_path):
            # Delete the file
            os.remove(file_path)

    os.rmdir(absPath)

def get_csv_from_spectrum(inst_ip):
    #for ping in range(1,255):
    address = inst_ip + "TransferData/GetTrace/"

    # Send HTTP GET request to server and attempt to receive a response with CSV file
    data = {'submit': 'All Traces'}
    try:
        response = requests.post(url=address, data=data)
    except:
        return "Can't reach instrument"

    # If the HTTP GET request can be served
    if response.status_code == 200:
        return response.text
    else:
        error = "http error:" + str(response.status_code)
        return "Can't reach instrument"

def evaluate_scores(traces, session_folder):
    #print(traces)
    if traces:
        for dict in traces:
            
            dict["30-60MHz_sum"] = 0
            dict["30-60MHz_count"] = 0
            dict["60-100MHz_sum"] = 0
            dict["60-100MHz_count"] = 0
            dict["100-200MHz_sum"] = 0
            dict["100-200MHz_count"] = 0
            dict["200-400MHz_sum"] = 0
            dict["200-400MHz_count"] = 0
            dict["400-1000MHz_sum"] = 0
            dict["400-1000MHz_count"] = 0

            if dict["filename"].endswith('.csv'):
                try:
                    df = pd.read_csv(os.path.join(session_folder, dict["filename"]), skiprows=18)
                    # Change column names in dataframe to more intuitive
                    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor'] # Naming in case of data has 4 rows
                    #print(df.head())
                except:
                    df = pd.read_csv(os.path.join(session_folder, dict["filename"]), skiprows=45)
                    # Change column names in dataframe to more intuitive
                    df.columns = ['Frequency[MHz]','Max(Ver,Hor)', 'Ver', 'Hor','','',''] # Naming in case of data has 7 rows
                    #print(df.head())
                    
                for row in range(len(df)):
                    df.at[row,'Max(Ver,Hor)'] = max(df.at[row,'Hor'], df.at[row,'Ver'])
                    df.at[row,'Frequency[MHz]'] = df.at[row,'Frequency[MHz]']/1000000
                    if df.at[row,'Frequency[MHz]'] >= 30 and df.at[row,'Frequency[MHz]'] < 60:
                        dict["30-60MHz_sum"] = dict["30-60MHz_sum"] + 10**(df.at[row,'Max(Ver,Hor)']/20)
                        dict["30-60MHz_count"] = dict["30-60MHz_count"] + 1
                    elif df.at[row,'Frequency[MHz]'] >= 60 and df.at[row,'Frequency[MHz]'] < 100:
                        dict["60-100MHz_sum"] = dict["60-100MHz_sum"] + 10**(df.at[row,'Max(Ver,Hor)']/20)
                        dict["60-100MHz_count"] = dict["60-100MHz_count"] + 1
                    elif df.at[row,'Frequency[MHz]'] >= 100 and df.at[row,'Frequency[MHz]'] < 200:
                        dict["100-200MHz_sum"] = dict["100-200MHz_sum"] + 10**(df.at[row,'Max(Ver,Hor)']/20)
                        dict["100-200MHz_count"] = dict["100-200MHz_count"] + 1
                    elif df.at[row,'Frequency[MHz]'] >= 200 and df.at[row,'Frequency[MHz]'] < 400:
                        dict["200-400MHz_sum"] = dict["200-400MHz_sum"] + 10**(df.at[row,'Max(Ver,Hor)']/20)
                        dict["200-400MHz_count"] = dict["200-400MHz_count"] + 1
                    elif df.at[row,'Frequency[MHz]'] >= 400 and df.at[row,'Frequency[MHz]'] < 1000:
                        dict["400-1000MHz_sum"] = dict["400-1000MHz_sum"] + 10**(df.at[row,'Max(Ver,Hor)']/20)
                        dict["400-1000MHz_count"] = dict["400-1000MHz_count"] + 1
                    
                    
                #print(df.head())
            
            dict["30-60MHz_AVG_uV"] = dict["30-60MHz_sum"] / dict["30-60MHz_count"]
            dict["30-60MHz_AVG_dBuV"] = 20*math.log10(dict["30-60MHz_AVG_uV"])
            dict["60-100MHz_AVG_uV"] = dict["60-100MHz_sum"] / dict["60-100MHz_count"]
            dict["60-100MHz_AVG_dBuV"] = 20*math.log10(dict["60-100MHz_AVG_uV"])
            dict["100-200MHz_AVG_uV"] = dict["100-200MHz_sum"] / dict["100-200MHz_count"]
            dict["100-200MHz_AVG_dBuV"] = 20*math.log10(dict["100-200MHz_AVG_uV"])
            dict["200-400MHz_AVG_uV"] = dict["200-400MHz_sum"] / dict["200-400MHz_count"]
            dict["200-400MHz_AVG_dBuV"] = 20*math.log10(dict["200-400MHz_AVG_uV"])
            dict["400-1000MHz_AVG_uV"] = dict["400-1000MHz_sum"] / dict["400-1000MHz_count"]
            dict["400-1000MHz_AVG_dBuV"] = 20*math.log10(dict["400-1000MHz_AVG_uV"])
            dict["30-1000MHz_AVG_uV"] = ( dict["30-60MHz_AVG_uV"] + dict["60-100MHz_AVG_uV"] + dict["100-200MHz_AVG_uV"] + dict["200-400MHz_AVG_uV"] + dict["400-1000MHz_AVG_uV"] ) / 5
            #print(dict["400-1000MHz_sum"])
            #print(dict["400-1000MHz_count"])
            #print(dict['30-60MHz_AVG_uV'])
            #print(dict['400-1000MHz_AVG_uV'])
            #print(dict['30-60MHz_AVG_dBuV'])
            #print(dict['400-1000MHz_AVG_dBuV'])
        # Read Limits.csv content with pandas into dataframe and add to graphs figure (RE Limits)
        try:
            df = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "Limits.csv"))
            df.columns = ['Frequency[MHz]','CISPR11_RE_CLASS_B_Group_1', 'CISPR11_RE_CLASS_B_Group_1_Important', 'CISPR11_RE_CLASS_A_Group_1_up_to_20kVA']
        except:
            return apology("Error in reading limits.csv file", 400)
        
        #max_30_60MHz = max([d["30-60MHz_AVG_uV"] for d in traces])
        #max_60_100MHz = max([d["60-100MHz_AVG_uV"] for d in traces])
        #max_100_200MHz = max([d["100-200MHz_AVG_uV"] for d in traces])
        #max_200_400MHz = max([d["200-400MHz_AVG_uV"] for d in traces])
        #max_400_1000MHz = max([d["400-1000MHz_AVG_uV"] for d in traces])
        #max_30_1000MHz = max([d["30-1000MHz_AVG_uV"] for d in traces])

        max_limit = {
                    "30-60MHz_sum": 0,
                    "30-60MHz_count": 0,
                    "30-60MHz_AVG_dBuV": 0,
                    "60-100MHz_sum": 0,
                    "60-100MHz_count": 0,
                    "60-100MHz_AVG_dBuV": 0,
                    "100-200MHz_sum": 0,
                    "100-200MHz_count": 0,
                    "100-200MHz_AVG_dBuV": 0,
                    "200-400MHz_sum": 0,
                    "200-400MHz_count": 0,
                    "200-400MHz_AVG_dBuV": 0,
                    "400-1000MHz_sum": 0,
                    "400-1000MHz_count": 0,
                    "200-400MHz_AVG_dBuV": 0,
                    "30-1000MHz_sum": 0,
                    "30-1000MHz_count": 0,
                    "30-1000MHz_AVG_dBuV": 0
                    }
        for row in range(len(df)):
            if df.at[row,'Frequency[MHz]'] >= 30 and df.at[row,'Frequency[MHz]'] < 60:
                max_limit["30-60MHz_sum"] = max_limit["30-60MHz_sum"] + 10**(df.at[row,'CISPR11_RE_CLASS_B_Group_1']/20)
                max_limit["30-60MHz_count"] = max_limit["30-60MHz_count"] + 1
            elif df.at[row,'Frequency[MHz]'] >= 60 and df.at[row,'Frequency[MHz]'] < 100:
                max_limit["60-100MHz_sum"] = max_limit["60-100MHz_sum"] + 10**(df.at[row,'CISPR11_RE_CLASS_B_Group_1']/20)
                max_limit["60-100MHz_count"] = max_limit["60-100MHz_count"] + 1
            elif df.at[row,'Frequency[MHz]'] >= 100 and df.at[row,'Frequency[MHz]'] < 200:
                max_limit["100-200MHz_sum"] = max_limit["100-200MHz_sum"] + 10**(df.at[row,'CISPR11_RE_CLASS_B_Group_1']/20)
                max_limit["100-200MHz_count"] = max_limit["100-200MHz_count"] + 1
            elif df.at[row,'Frequency[MHz]'] >= 200 and df.at[row,'Frequency[MHz]'] < 400:
                max_limit["200-400MHz_sum"] = max_limit["200-400MHz_sum"] + 10**(df.at[row,'CISPR11_RE_CLASS_B_Group_1']/20)
                max_limit["200-400MHz_count"] = max_limit["200-400MHz_count"] + 1
            elif df.at[row,'Frequency[MHz]'] >= 400 and df.at[row,'Frequency[MHz]'] < 1000:
                max_limit["400-1000MHz_sum"] = max_limit["400-1000MHz_sum"] + 10**(df.at[row,'CISPR11_RE_CLASS_B_Group_1']/20)
                max_limit["400-1000MHz_count"] = max_limit["400-1000MHz_count"] + 1
        
        max_limit["30-60MHz_AVG_dBuV"] = max_limit["30-60MHz_sum"] / max_limit["30-60MHz_count"]
        max_limit["60-100MHz_AVG_dBuV"] = max_limit["60-100MHz_sum"] / max_limit["60-100MHz_count"]
        max_limit["100-200MHz_AVG_dBuV"] = max_limit["100-200MHz_sum"] / max_limit["100-200MHz_count"]
        max_limit["200-400MHz_AVG_dBuV"] = max_limit["200-400MHz_sum"] / max_limit["200-400MHz_count"]
        max_limit["400-1000MHz_AVG_dBuV"] = max_limit["400-1000MHz_sum"] / max_limit["400-1000MHz_count"]
        max_limit["30-1000MHz_AVG_dBuV"] = (max_limit["30-60MHz_AVG_dBuV"] + max_limit["60-100MHz_AVG_dBuV"] + max_limit["100-200MHz_AVG_dBuV"] + max_limit["200-400MHz_AVG_dBuV"] + max_limit["30-1000MHz_AVG_dBuV"]) / 5
        
        min_30_60MHz = min([d["30-60MHz_AVG_uV"] for d in traces])
        min_60_100MHz = min([d["60-100MHz_AVG_uV"] for d in traces])
        min_100_200MHz = min([d["100-200MHz_AVG_uV"] for d in traces])
        min_200_400MHz = min([d["200-400MHz_AVG_uV"] for d in traces])
        min_400_1000MHz = min([d["400-1000MHz_AVG_uV"] for d in traces])
        min_30_1000MHz = min([d["30-1000MHz_AVG_uV"] for d in traces])


        for dict in traces:
            normalized_value = 100 - ((dict["30-60MHz_AVG_uV"] - min_30_60MHz) / (max_limit["30-60MHz_AVG_dBuV"] - min_30_60MHz)) * 100
            dict["30-60MHz_score"] = round(normalized_value, 0)
            normalized_value = 100 - ((dict["60-100MHz_AVG_uV"] - min_60_100MHz) / (max_limit["60-100MHz_AVG_dBuV"] - min_60_100MHz)) * 100
            dict["60-100MHz_score"] = round(normalized_value, 0)
            normalized_value = 100 - ((dict["100-200MHz_AVG_uV"] - min_100_200MHz) / (max_limit["100-200MHz_AVG_dBuV"] - min_100_200MHz)) * 100
            dict["100-200MHz_score"] = round(normalized_value, 0)
            normalized_value = 100 - ((dict["200-400MHz_AVG_uV"] - min_200_400MHz) / (max_limit["200-400MHz_AVG_dBuV"] - min_200_400MHz)) * 100
            dict["200-400MHz_score"] = round(normalized_value, 0)
            normalized_value = 100 - ((dict["400-1000MHz_AVG_uV"] - min_400_1000MHz) / (max_limit["400-1000MHz_AVG_dBuV"] - min_400_1000MHz)) * 100
            dict["400-1000MHz_score"] = round(normalized_value, 0)
            normalized_value = 100 - ((dict["30-1000MHz_AVG_uV"] - min_30_1000MHz) / (max_limit["30-1000MHz_AVG_dBuV"] - min_30_1000MHz)) * 100
            dict["30-1000MHz_score"] = round(normalized_value, 0)
            #print(dict["30-1000MHz_score"])
    else:
        return apology("No traces in this session", 400)
        #print(traces)

    return traces