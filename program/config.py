import os

def get_db_config():
    return {
        'mysql': {
            'host': 'localhost',
            'user': 'root', 
            'password': os.getenv('MEDICAL_DB_PASSWORD'), 
            'database': 'medical' 
        },
        'sqlite': {
            'database': 'path/to/your/database.db'
        },
        'postgresql': {
            'host': 'localhost',
            'user': 'your_postgresql_username',
            'password': 'your_postgresql_password',
            'database': 'your_postgresql_database'
        },
        'sqlserver': {
            'host': 'localhost',
            'user': 'your_sqlserver_username',
            'password': 'your_sqlserver_password',
            'database': 'your_sqlserver_database'
        }
    }