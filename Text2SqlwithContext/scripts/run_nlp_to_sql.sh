#!/bin/bash
# 运行NLP到SQL转换

# 激活虚拟环境
venv\Scripts\activate

# 设置PYTHONPATH以便正确导入模块
export PYTHONPATH=$(pwd):$PYTHONPATH

# 运行程序
python -m src.nlp_to_sql.main

echo "NLP到SQL转换完成!"
