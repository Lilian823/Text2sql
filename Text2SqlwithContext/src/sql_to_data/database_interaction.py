import sqlite3
import pyodbc
import psycopg2
import psycopg2.pool
import pandas as pd
from mysql.connector import pooling
from mysql.connector import Error as MySQLError
from .config import get_db_config
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局连接池字典
_connection_pools = {
    'mysql': None,
    'postgresql': None,
    'sqlite': None,  # SQLite不直接使用连接池
    'sqlserver': None
}

def init_connection_pool(db_type='mysql'):
    """初始化数据库连接池"""
    global _connection_pools
    
    # 如果已经初始化，直接返回
    if _connection_pools.get(db_type) is not None:
        return _connection_pools[db_type]
    
    # 获取数据库配置
    config = get_db_config(db_type)
    
    if db_type == 'mysql':
        # 初始化MySQL连接池
        try:
            pool = pooling.MySQLConnectionPool(
                pool_name="mysql_pool",
                pool_size=5,
                **{k: v for k, v in config.items() if k != 'use_pure'}
            )
            logger.info("MySQL连接池初始化成功")
            _connection_pools[db_type] = pool
            return pool
        except MySQLError as e:
            logger.error(f"MySQL连接池初始化失败: {e}")
            raise
    
    elif db_type == 'postgresql':
        # 初始化PostgreSQL连接池
        try:
            pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                host=config['host'],
                user=config['user'],
                password=config['password'],
                dbname=config['database'],
                port=config.get('port', 5432)
            )
            logger.info("PostgreSQL连接池初始化成功")
            _connection_pools[db_type] = pool
            return pool
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL连接池初始化失败: {e}")
            raise
    
    elif db_type == 'sqlserver':
        # 初始化SQL Server连接池
        try:
            # SQL Server连接字符串
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={config['host']};"
                f"DATABASE={config['database']};"
                f"UID={config['user']};"
                f"PWD={config['password']};"
                f"Encrypt=no;"
            )
            
            # SQL Server连接池类
            class SQLServerPool:
                def __init__(self):
                    self.connections = []
                
                def get_connection(self):
                    """从连接池获取连接"""
                    if self.connections:
                        return self.connections.pop()
                    else:
                        return pyodbc.connect(conn_str)
                
                def release(self, conn):
                    """释放连接回连接池"""
                    self.connections.append(conn)
            
            pool = SQLServerPool()
            logger.info("SQL Server连接池初始化成功")
            _connection_pools[db_type] = pool
            return pool
        
        except pyodbc.Error as e:
            logger.error(f"SQL Server连接池初始化失败: {e}")
            raise
    
    elif db_type == 'sqlite':
        # SQLite不维护连接池，直接连接到数据库文件
        _connection_pools[db_type] = True  # 标记为已初始化
        logger.info("SQLite连接初始化成功")
        return True
    
    else:
        logger.error(f"不支持的数据库类型: {db_type}")
        raise ValueError(f"Unsupported database type: {db_type}")

def execute_query(query: str, db_type: str = 'mysql') -> pd.DataFrame:
    """执行SQL查询并返回DataFrame结果"""
    try:
        # 获取连接池
        pool = init_connection_pool(db_type)
        connection = None
        
        if db_type == 'mysql':
            # MySQL查询执行
            connection = pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            result = cursor.fetchall()
        
        elif db_type == 'postgresql':
            # PostgreSQL查询执行
            connection = pool.getconn()
            cursor = connection.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        elif db_type == 'sqlserver':
            # SQL Server查询执行
            connection = pool.get_connection()
            cursor = connection.cursor()
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        elif db_type == 'sqlite':
            # SQLite查询执行
            config = get_db_config(db_type)
            connection = sqlite3.connect(config['database'])
            connection.row_factory = sqlite3.Row  # 使查询结果可转为字典
            cursor = connection.cursor()
            cursor.execute(query)
            result = [dict(row) for row in cursor.fetchall()]
        
        else:
            logger.error(f"不支持的数据库类型: {db_type}")
            return pd.DataFrame()
        
        return pd.DataFrame(result)
    
    except Exception as err:
        logger.error(f"执行查询时出错: {err}")
        return pd.DataFrame()
    
    finally:
        # 释放数据库连接
        if db_type == 'mysql':
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
        
        elif db_type == 'postgresql':
            if connection:
                connection.commit()
                pool.putconn(connection)
        
        elif db_type == 'sqlserver':
            if connection:
                # 释放回连接池，不实际关闭连接
                pool.release(connection)
        
        elif db_type == 'sqlite':
            if connection:
                connection.close()
