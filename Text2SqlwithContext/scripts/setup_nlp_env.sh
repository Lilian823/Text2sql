#!/bin/bash
# 创建虚拟环境并安装依赖

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建必要的目录
mkdir integration\input integration\sql integration\results

echo "NLP到SQL环境设置完成!"
