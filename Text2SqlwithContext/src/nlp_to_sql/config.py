import os
from dotenv import load_dotenv # type: ignore

# 加载环境变量
#load_dotenv()
load_dotenv(os.path.join(os.getcwd(), ".env"))

# API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")

# 文件路径
INPUT_QUERY_PATH = os.path.join(os.getcwd(), "integration/input/user_query.json")
OUTPUT_SQL_PATH = os.path.join(os.getcwd(), "integration/sql/generated_sql.json")

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
