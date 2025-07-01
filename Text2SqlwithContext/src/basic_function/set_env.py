import os

def update_env_vars(env_path=".env"):
    # 读取原有内容
    env_dict = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_dict[k] = v

    # 交互获取新值
    openai_api_key = input("请输入新的 OPENAI_API_KEY：").strip()
    medical_db_password = input("请输入新的 MEDICAL_DB_PASSWORD：").strip()

    # 只更新这两项
    env_dict["OPENAI_API_KEY"] = openai_api_key
    env_dict["MEDICAL_DB_PASSWORD"] = medical_db_password

    # 写回文件
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")

    print(f"{env_path} 文件已更新！")

if __name__ == "__main__":
    update_env_vars()