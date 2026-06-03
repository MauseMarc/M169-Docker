import pandas as pd
from database.db_base import *

co = sqlite3.connect(DB_PATH, isolation_level=None, detect_types=sqlite3.PARSE_COLNAMES)


def get_table_list():
    with co:
        cursor = co.cursor()
        cursor.execute("SELECT name FROM sqlite_master;")
        thing = cursor.fetchall()
        table_list = []
        for entry in thing:
            if "sqlite" not in entry[0]:
                table_list.append(entry[0])
        return table_list

def clean_database(table_list):
    for table in table_list:
        with co:
            cursor = co.cursor()
            cursor.execute(f"DELETE FROM {table}")

def export_data_csv():
    table_list = get_table_list()
    for table in table_list:
        db_df = pd.read_sql_query(f"SELECT * FROM {table}", co)
        db_df.to_csv(f"./Data/{table}.csv", index=False)



def import_data_csv():
    clean_database(get_table_list())
    table_list = get_table_list()
    for table in table_list:
        df = pd.read_csv(f"./Data/{table}.csv")
        df.to_sql(table, co, if_exists='append', index=False)



# export_data_csv()

