from sqlite3 import connect
import pandas as pd

# Configure standard SQLite3
db = connect("plotter.db")

# Read database sessions table content into pandas dataframe for easy manipulation
df = pd.read_sql("SELECT sessions.id, sessions.folder FROM graphs JOIN users ON sessions.user_id = users.id JOIN sessions ON graphs.session_id = sessions.id", db)

# Iterate over each row of a dataframe (database)
for row in range(len(df)):
    new_folder = df.at[row,'folder'].replace('/home/ilya.s/EMC_Plotter_DB.git/cs50_final_project/','')
    db.execute("UPDATE sessions SET folder = ? where id = ?", (str(new_folder), int(df.at[row,'id'])))

# Read updated database and print it in terminal for verification by user
df = pd.read_sql("SELECT sessions.id, sessions.folder FROM graphs JOIN users ON sessions.user_id = users.id JOIN sessions ON graphs.session_id = sessions.id", db)
print("Database folder name convetrion fixed to: user_data/username/session.name")
print("See updated table hear below:")
print(df.head())

# Save database changes
db.commit()

