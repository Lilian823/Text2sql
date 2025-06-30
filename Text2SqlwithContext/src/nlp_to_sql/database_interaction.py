import mysql.connector # type: ignore
from mysql.connector import Error # type: ignore
import os
from src.nlp_to_sql.config import get_db_config
import pandas as pd # type: ignore

def create_db_connection(db_type='mysql'):
    db_config = get_db_config()
    config = db_config.get(db_type, {})
    
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        print("Successfully connected to the MySQL database.")
    except Error as err:
        print(f"Error: '{err}'")
    
    return connection

def execute_query(query, db_type='mysql'):
    connection = create_db_connection(db_type)
    cursor = connection.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return pd.DataFrame(result)
    except Error as err:
        print(f"Error executing query: '{err}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

def execute_non_query(query, db_type='mysql'):
    connection = create_db_connection(db_type)
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        return True
    except Error as err:
        print(f"Error executing non-query: '{err}'")
        return False
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()