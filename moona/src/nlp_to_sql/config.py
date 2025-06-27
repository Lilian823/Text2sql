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