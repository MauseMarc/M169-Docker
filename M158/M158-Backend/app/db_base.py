import mariadb
import os

db_host = os.environ['DB_HOST']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = os.environ['DB_NAME']
db_port = os.environ['DB_PORT']


CONN_PARAMS = {
    'host': db_host,
    'user': db_user,
    'password': db_password,
    'database': db_name,
    'port': db_port
}


def get_db():
    conn = mariadb.connect(**CONN_PARAMS)
    return conn
