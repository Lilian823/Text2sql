import json
import os
import datetime

def ensure_directory(file_path):
    """确保文件目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_json(file_path):
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return None

def write_json(data, file_path):
    """将数据写入JSON文件"""
    # 确保目录存在
    ensure_directory(file_path)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"写入JSON文件失败: {e}")
        return False
