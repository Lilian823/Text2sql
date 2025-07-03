import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt  # type: ignore
import matplotlib  # type: ignore
matplotlib.use('Agg')
import pandas as pd  # type: ignore
from flask import Flask, request, jsonify, send_from_directory
from Text2SqlwithContext.src.basic_function.set_env import update_env_vars
from Text2SqlwithContext.src.sql_to_data.sql_processor import SQLProcessor
from Text2SqlwithContext.src.nlp_to_sql.json_handler import read_json, write_json
from Text2SqlwithContext.src.nlp_to_sql.sql_generator import generate_sql_from_nl
from Text2SqlwithContext.src.nlp_to_sql.context_manager import ContextualConversation
from flask_cors import CORS
from Text2SqlwithContext.src.sql_to_data.database_interaction import init_connection_pool
import mysql.connector  # type: ignore


load_dotenv(dotenv_path=Path(__file__).resolve().parent / 'Text2SqlwithContext' / '.env')

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'web.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    if filename.endswith('.css') or filename.endswith('.js'):
        return send_from_directory('.', filename)
    else:
        return '', 404

context_manager = ContextualConversation()
session_id = "user_session"

def get_project_root():
    return Path(__file__).resolve().parent

def run_sql_processor_and_collect_message(sql_file_path):
    messages = []
    messages.append("开始执行SQL并分析结果...")

    import json
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql_json = json.load(f)
    generated_sql = sql_json.get("generated_sql", "")
    if isinstance(generated_sql, str) and generated_sql.strip().startswith("生成错误"):
        error_msg = f"加载SQL查询: {generated_sql}"
        print(error_msg, file=sys.stderr)
        return '', '', {}, error_msg

    processor = SQLProcessor(sql_file_path)
    result = processor.process()
    if result['status'] == 'error':
        messages.append(f"处理失败: {result['message']}")
        if 'sql_error' in result:
            print(f"SQL执行错误: {result['sql_error']}", file=sys.stderr)
        return '', '\n'.join(messages), {}, result['message']
    messages.append("医疗数据分析摘要:")
    messages.append(str(result['summary']))
    chart_urls = {}
    if processor.charts:
        messages.append("生成的数据可视化图表:")
        output_dir = Path(__file__).parent / "Text2SqlwithContext" / "integration" / "output"
        os.makedirs(output_dir, exist_ok=True)
        for chart_type, fig in processor.charts.items():
            if fig:
                plt.figure(fig.number)
                chart_path = output_dir / f"{chart_type}_chart.png"
                plt.savefig(str(chart_path))
                plt.close()
                chart_urls[chart_type] = f"/api/chart/{chart_type}_chart.png"
    else:
        messages.append("未生成任何图表")
    
    messages.append("数据预览 (前10行):")
    
    if result['dataframe']:
        preview_df = pd.DataFrame(result['dataframe'])
        messages.append(preview_df.to_string(index=False))
    else:
        messages.append("无数据可显示")
    messages.append("\n分析完成!")
    return result.get('generated_sql', ''), '\n'.join(messages), chart_urls, ''

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    user_query = data.get('question', '')
    session_id = data.get('conversation_id', 'user_session')
    if not user_query.strip():
        return jsonify({"error": "问题不能为空", "sql": "", "result": [], "conversation_id": session_id})

    project_root = get_project_root()
    db_schema_path = project_root/ "Text2SqlwithContext" / "integration" / "input" / "db_schema.json"
    try:
        with open(db_schema_path, "r", encoding="utf-8") as f:
            db_schema = f.read()
    except Exception as e:
        return jsonify({"error": f"数据库结构文件读取失败: {e}", "sql": "", "result": [], "conversation_id": session_id})
    enhanced_query = context_manager.enhance_query(session_id, user_query)
    query_data = {
        "query_id": "q_user",
        "natural_language_query": enhanced_query,
        "database_schema": db_schema
    }
    result = generate_sql_from_nl(query_data)
    sql = result.get("generated_sql", "")
    project_root = get_project_root()
    output_dir = project_root / "Text2SqlwithContext" / "integration" / "sql"
    os.makedirs(output_dir, exist_ok=True)
    sql_output_path = output_dir / "results.json"
    results = {"generated_sql": sql}
    write_json(results, str(sql_output_path))
    try:
        sql, message, chart_urls, error = run_sql_processor_and_collect_message(str(sql_output_path))
        if error and error.startswith("加载SQL查询: 生成错误"):
            return jsonify({
                "sql": "",
                "result": [],
                "message": "",
                "conversation_id": session_id,
                "error": error,
                "chart_urls": {}
            })
        return jsonify({
            "sql": sql,
            "result": [],
            "message": message,
            "conversation_id": session_id,
            "error": error,
            "chart_urls": chart_urls
        })
    except Exception as e:
        error_msg = str(e)
        return jsonify({
            "sql": "",
            "result": [],
            "message": "",
            "conversation_id": session_id,
            "error": error_msg,
            "chart_urls": {}
        })

@app.route('/api/connect_db', methods=['POST'])
def connect_db():
    seed_dir = os.path.join('Text2SqlwithContext', 'seed')
    sql_files = [f for f in os.listdir(seed_dir) if f.endswith('.sql')]
    if not sql_files:
        print("数据库导入失败：未找到SQL文件", file=sys.stderr)
        return jsonify({'success': False, 'error': '数据库导入失败'})
    import_results = []
    try:
        pool = init_connection_pool('mysql')
        connection = pool.get_connection()
        cursor = connection.cursor()
        for sql_file in sql_files:
            sql_path = os.path.join(seed_dir, sql_file)
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            for statement in [s.strip() for s in sql_content.split(';') if s.strip()]:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    connection.rollback()
                    print(f"数据库导入异常: {e}", file=sys.stderr)
                    return jsonify({'success': False, 'error': '数据库导入失败', 'detail': str(e)})
            connection.commit()
            import_results.append(f"{sql_file} 导入成功")
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'message': '，'.join(import_results)})
    except Exception as e:
        print(f"数据库导入异常: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': '数据库导入失败', 'detail': str(e)})

@app.route('/api/chart/<filename>')
def get_chart(filename):
    output_dir = Path(__file__).parent / "Text2SqlwithContext" / "integration" / "output"
    return send_from_directory(str(output_dir), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)