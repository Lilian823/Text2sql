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
            connection.close()  # 实际是返还给连接池
