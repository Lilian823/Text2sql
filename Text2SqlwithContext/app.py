from flask import Flask, request, jsonify
from src.nlp_to_sql.context_manager import ContextualConversation
from src.nlp_to_sql.sql_generator import generate_sql_from_nl
import json
import sys
sys.path.append('./program')  # 确保可以导入program文件夹下的模块
from program.main import process_sql_request

app = Flask(__name__)
context_manager = ContextualConversation()

# 你可以将 db_schema 直接在后端读取，也可以让前端传递
def get_db_schema():
    db_schema_path = "integration/input/db_schema.json"
    try:
        with open(db_schema_path, "r", encoding="utf-8") as f:
            db_schema = f.read()
        return db_schema
    except Exception as e:
        return ""

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    user_query = data.get('question', '')
    session_id = data.get('conversation_id', 'user_session')
    db_schema = get_db_schema()

    if not user_query.strip():
        return jsonify({"error": "问题不能为空", "sql": "", "result": [], "conversation_id": session_id})

    # 上下文增强
    enhanced_query = context_manager.enhance_query(session_id, user_query)
    query_data = {
        "query_id": "q_user",
        "natural_language_query": enhanced_query,
        "database_schema": db_schema
    }

    # 生成SQL
    result = generate_sql_from_nl(query_data)
    sql = result.get("generated_sql", "")
    error = result.get("error", "")
    message = result.get("message", "")

    # 记录历史
    context_manager.add_history(session_id, user_query, sql, result)

    # 如果SQL生成成功，进一步分析数据库并返回可视化数据
    visualization = None
    query_result = []
    if result.get("status") == "success" and sql:
        # 构造 program/main.py 需要的 json 输入
        sql_json = json.dumps({
            "db_type": "mysql",  # 可根据实际情况调整
            "query": sql
        }, ensure_ascii=False)
        # 捕获 program/main.py 的输出
        import io
        import contextlib
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            process_sql_request(sql_json)
        output_text = output_buffer.getvalue()
        # 这里假设 program/main.py 的 process_sql_request 会打印文本摘要和可视化信息
        # 你可以根据实际返回结构进一步解析
        message += "\n" + output_text
        # 可选：你可以将可视化数据结构化返回给前端
        # query_result = ...

    return jsonify({
        "sql": sql,
        "result": query_result,  # 可视化/表格数据
        "message": message,
        "conversation_id": session_id,
        "error": error
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)