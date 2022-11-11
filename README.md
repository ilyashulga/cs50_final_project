# EMC Plotter DB v.0.1 ALPHA
#### Video Demo: https://youtu.be/by_l7aCjBEA
#### Description:
This Web-based APP is designed to help hardware engineers to manage and evaluate EMC Testing results for their products. 

#### Current version supports the following features:
1. Authentication (Login + Registration of new users)
2. Each registered user gets access to his own "space" on server where he/she can upload testing results (csv raw data from spectrum analyzer) - users_data/username/
3. This csv raw data can be uploaded from local computer or directly pulled from spectrum analyzer (Keysight) via HTTP Post request - need to provide instrument http address in corresponting field
4. Devices support: Power Optimizer (MPPT) Buck/Boost
5. 4 means that the details fields are constructed to be relevant for MPPT Buck-Boost converters testing (Working point information - Duty Cycle, Vin, Iin etc.)
5. The results are divided into "Sessions". Each session usually is simply another day of lab testing (since lab visits are usually separated by several days)
6. Each sesssion consists of multiple graphs together with UUT (Unit Under Test) and working point details added by user. This binds into single "result"
7. All Sessions and "Results" are stored with corresponding details in SQL Database (plotter.db) 
8. User benefits from easy results comparing feature and has access to all his sessions and graphs from the past that a well organized with all needed details to be able to interpret that specific result and compare it to the recent ones
9. All original raw data is stored (without modifications)


#### Required RAW Data format:
1. RAW DATA .csv file downloaded from EMI Receiver (Keysight N9038A MXE or similar model)
2. Trace 2 should be MaxHold of Vertical Antenna Polarization Measurement (table full 360 deg rotation)
3. Trace 3 should be MaxHold of Horizontal Antenna Polarization Measurement (table full 360 deg rotation)
4. The plotted graphs magnitude are Max(Vertical, Horizontal) - this simplifies comparison of different results

#### Dataset examples (to play with the app)
 - Please check out raw data csv files examples in "Dataset_examples" folder that can be used as a data for evaluating the app performance without taking actual measurements

#### Code Details:
Python Packages used:
1. cs50 - SQL Database interation
2. python3-Flask - Web-Based app skeleton
3. Flask-Session - Storing user session data (mainly the session id, user form data entries, last working point info)
4. requests - Pulling data directly from Keysight EMI Recveiver (using HPPT POST Request)
5. plotly - Plotting and comparing session graphs
6. pandas - Reading raw data cvs content and manipulation
7. datetime - Time stamps
8. pathlib - safely storing user data on disk and enable cross-platform desing
9. json - convert plotly graph object to JSON forman (for HTML Embedding)

Other languages:
1. Javascript - html form manimulation and other front end stuff
2. HTML with some CSS styling
3. JINJA - pass data from python to html
4. SQL - storage of users and user data

App.py:
    All backend code is concentrated here. 

helpers.py:
    Functions that was desided to keep in separate file for cleaner look

#### SQL Database Structure:
1. Users table:

    | id (unique) | username | hash | type |
    | ---         | ---      | ---  | ---  |
    | INTEGER     | TEXT     | TEXT | TEXT |

2. Sessions table:
    
    | id (unique) | user_id | name | description | timestamp | folder |
    | ---         | ---     | ---  | ---         | ---       | ---    |
    | INTEGER     | INTEGER | TEXT | TEXT        | TEXT      | TEXT   |
 

3. Graphs table:
    
    | id (unique) | session_id | model | layout | is_cl   | v_in    | v_out   | i_in  | i_load | dc    | power   | mode | comment | filename | timestamp | is_final |
    |     ---     | ---        | ---   | ---    | ---     | ---     | ---     | ---   | ---    | ---   | ---     | ---  | ---     | ---      | ---       | --- |
    | INTEGER     | INTEGER    | TEXT  | TEXT   | INTEGER | INTEGER | INTEGER | FLOAT | FLOAT  | FLOAT | INTEGER | TEXT | TEXT    | TEXT     |           | INTEGER  |



