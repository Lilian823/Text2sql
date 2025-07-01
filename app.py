import sys
import os

# 添加 src 目录到 sys.path，确保可以找到 main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, 'Text2SqlwithContext', 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from flask import Flask, request, jsonify, send_from_directory
from Text2SqlwithContext.src.main import run_sql_processor

app = Flask(__name__)

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    user_query = data.get('question', '')
    session_id = data.get('conversation_id', 'user_session')
    if not user_query.strip():
        return jsonify({"error": "问题不能为空", "sql": "", "result": [], "conversation_id": session_id})

    # 直接调用 main.py 的 run_sql_processor 处理自然语言，生成 SQL 和图表
    # 假设 run_sql_processor 返回 (sql, message, chart_url, error)
    sql, message, chart_url, error = run_sql_processor(user_query, session_id)

    return jsonify({
        "sql": sql,
        "result": [],
        "message": message,
        "conversation_id": session_id,
        "error": error,
        "chart_url": chart_url
    })

@app.route('/api/upload_sql', methods=['POST'])
def upload_sql():
    file = request.files.get('sql_file')
    if not file:
        return jsonify({'success': False, 'error': '未收到文件'})
    try:
        save_path = os.path.join('integration', 'input', 'db_schema.sql')
        file.save(save_path)
        # 可选：此处可自动触发表结构重载逻辑
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chart/<filename>')
def get_chart(filename):
    return send_from_directory('integration/output', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)