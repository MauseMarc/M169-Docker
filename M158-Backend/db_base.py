import mariadb

CONN_PARAMS = {
    "user": "Gamemaster",
    "password": "timo12345",
    "host": "localhost",
    "database": "momdb"
}

def get_db():
    conn = mariadb.connect(**CONN_PARAMS)
    return conn