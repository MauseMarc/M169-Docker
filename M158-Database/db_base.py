# import sqlite3
# DB_PATH = "../database/test.db"

# def get_db():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     return conn


import mariadb

CONN_PARAMS = {
    "user": "Gamemaster",
    "password": "timo12345",
    "host": "localhost",
    "database": "momdb"
}

def get_db():
    conn = mariadb.connect(**CONN_PARAMS)