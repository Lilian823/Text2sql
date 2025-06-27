import pymysql
import sqlite3
import psycopg2
import pyodbc
import pandas as pd
from config import get_db_config
import os

def connect_to_database(db_type='mysql'):
    db_config = get_db_config()[db_type]
    try:
        if db_type == 'mysql':
            connection = pymysql.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=os.getenv('MEDICAL_DB_PASSWORD'),
                database=db_config['database']
            )
        elif db_type == 'sqlite':
            connection = sqlite3.connect(db_config['database'])
        elif db_type == 'postgresql':
            connection = psycopg2.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
        elif db_type == 'sqlserver':
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={db_config['host']};"
                f"DATABASE={db_config['database']};"
                f"UID={db_config['user']};"
                f"PWD={db_config['password']}"
            )
            connection = pyodbc.connect(connection_string)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        print(f"Successfully connected to the {db_type} database.")
        return connection
    except Exception as e:
        print(f"Error connecting to the {db_type} database: {e}")
        return None

def execute_query(query, db_type='mysql'):
    connection = connect_to_database(db_type)
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            
            # Get column names
            if db_type == 'mysql' or db_type == 'postgresql':
                columns = [desc[0] for desc in cursor.description]
            elif db_type == 'sqlite':
                columns = [description[0] for description in cursor.description]
            elif db_type == 'sqlserver':
                columns = [column[0] for column in cursor.description]
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            df = pd.DataFrame(result, columns=columns)
            return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        connection.close()

def execute_non_query(query, db_type='mysql'):
    connection = connect_to_database(db_type)
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            connection.commit()
        return True
    except Exception as e:
        print(f"Error executing non-query: {e}")
        return False
    finally:
        connection.close()