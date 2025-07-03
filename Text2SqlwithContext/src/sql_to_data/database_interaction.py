from binascii import Error
from mysql.connector import pooling # type: ignore
import pandas as pd # type: ignore
from Text2SqlwithContext.src.basic_function.config import get_db_config

# 全局连接池（单例）
_connection_pool = None

def init_connection_pool(db_type='mysql'):
    global _connection_pool
    if _connection_pool is None:
        db_config = get_db_config(db_type)
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="medical_pool",
            pool_size=5,  # 连接池大小
            **db_config
        )
        # elif db_type == 'postgresql':
        #     import psycopg2
        #     from psycopg2 import pool
        #     # 创建ThreadedConnectionPool
        #     _connection_pool = pool.ThreadedConnectionPool(
        #         minconn=5,   # 最小连接数
        #         maxconn=20,  # 最大连接数
        #         host=db_config['host'],
        #         user=db_config['user'],
        #         password=db_config['password'],
        #         database=db_config['database']
        #     )
        # elif db_type == 'sqlserver':
        #     import pyodbc
        #     # 实现SQL Server连接池类
        #     class SQLServerConnectionPool:
        #         def __init__(self, max_size=10):
        #             self.pool = []
        #             self.max_size = max_size
        #             for _ in range(5):
        #                 conn = pyodbc.connect(
        #                     f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        #                     f"SERVER={db_config['host']};"
        #                     f"DATABASE={db_config['database']};"
        #                     f"UID={db_config['user']};"
        #                     f"PWD={db_config['password']}"
        #                 )
        #                 self.pool.append(conn)
        #                 
        #         def get_connection(self):
        #             if self.pool:
        #                 return self.pool.pop()
        #             elif len(self.pool) < self.max_size:
        #                 # 创建新连接
        #                 conn = pyodbc.connect(...)
        #                 return conn
        #             else:
        #                 raise RuntimeError("连接池耗尽")
        #                 
        #         def release_connection(self, conn):
        #             if conn.connected:
        #                 self.pool.append(conn)
        #                 
        #     _connection_pool = SQLServerConnectionPool()
    return _connection_pool

def execute_query(query: str, db_type: str = 'mysql') -> pd.DataFrame:
    try:
        pool = init_connection_pool(db_type)
        connection = pool.get_connection()  # 从池中获取连接
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        return pd.DataFrame(result)
    except Error as err:
        print(f"执行查询时出错: {err}")
        return pd.DataFrame()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
