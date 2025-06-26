import os
from dotenv import load_dotenv # type: ignore

print("当前工作目录:", os.getcwd())
load_dotenv(os.path.join(os.getcwd(), ".env"))
print("所有环境变量:", os.environ)  # 检查是否包含你的密钥
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))