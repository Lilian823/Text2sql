import os
from dotenv import load_dotenv # type: ignore

# 加载环境变量
#load_dotenv()
load_dotenv(os.path.join(os.getcwd(), ".env"))

# API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")
MEDICAL_DB_PASSWORD = os.getenv("MEDICAL_DB_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "medical")
SQLITE_PATH = os.getenv("SQLITE_PATH", "medical.db")
SQLSERVER_USER = os.getenv("SQLSERVER_USER", "sa")
SQLSERVER_PASSWORD = os.getenv("SQLSERVER_PASSWORD")
SQLSERVER_DB = os.getenv("SQLSERVER_DB", "medical")
SQLSERVER_SERVER = os.getenv("SQLSERVER_SERVER", "localhost")

# 文件路径
INPUT_QUERY_PATH = os.path.join(os.getcwd(), "integration/input/user_query.json")
OUTPUT_SQL_PATH = os.path.join(os.getcwd(), "integration/sql/generated_sql.json")

def get_db_config(db_type):
    """获取数据库连接配置"""
    return {
        'mysql': {
            'host': 'localhost',
            'user': 'root', 
            'password': MEDICAL_DB_PASSWORD,
            'database': 'medical',
            'use_pure': True 
        },
        'sqlite': {
            'database': SQLITE_PATH
        },
        'postgresql': {
            'host': 'localhost',
            'user': POSTGRES_USER,
            'password': POSTGRES_PASSWORD,
            'database': POSTGRES_DB,
            'port': 5432
        },
        'sqlserver': {
            'host': SQLSERVER_SERVER,
            'user': SQLSERVER_USER,
            'password': SQLSERVER_PASSWORD,
            'database': SQLSERVER_DB,
            'port': 1433
        }
    }[db_type]
