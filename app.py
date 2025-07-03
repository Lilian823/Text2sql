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


# 加载.env环境变量
load_dotenv(dotenv_path=Path(__file__).resolve().parent / 'Text2SqlwithContext' / '.env')

app = Flask(__name__)
CORS(app)

# 初始化上下文管理器
@app.route('/')
def index():
    # 假设 web.html 在项目根目录下
    return send_from_directory('.', 'web.html')

# 静态文件路由，支持直接访问 .css 和 .js 文件
@app.route('/<path:filename>')
def serve_static_files(filename):
    # 只允许访问根目录下的 .css 和 .js 文件
    if filename.endswith('.css') or filename.endswith('.js'):
        return send_from_directory('.', filename)
    else:
        # 其他文件类型不允许
        return '', 404

# 初始化上下文管理器
context_manager = ContextualConversation()
session_id = "user_session"

def get_project_root():
    return Path(__file__).resolve().parent

# 整合main.py的核心功能，返回所有文字信息用于系统消息

def run_sql_processor_and_collect_message(sql_file_path):
    messages = []
    messages.append("="*80)
    messages.append("开始执行SQL并分析结果...")
    messages.append("="*80)
    processor = SQLProcessor(sql_file_path)
    result = processor.process()
    if result['status'] == 'error':
        # 增加详细错误信息到 messages
        messages.append(f"处理失败: {result['message']}")
        # 如果有 SQL 错误详情，追加显示
        if 'sql_error' in result:
            messages.append(f"SQL执行错误: {result['sql_error']}")
        # 返回所有消息内容
        return '', '\n'.join(messages), {}, result['message']
    messages.append("="*80)
    messages.append("医疗数据分析摘要:")
    messages.append("="*80)
    messages.append(str(result['summary']))
    chart_urls = {}
    if processor.charts:
        messages.append("="*80)
        messages.append("生成的数据可视化图表:")
        messages.append("="*80)
        # 用绝对路径创建目录（确保在Text2SqlwithContext/integration/output）
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
    messages.append("="*80)
    messages.append("数据预览 (前10行):")
    messages.append("="*80)
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

    # 生成SQL
    # 这里假设有 db_schema.json，实际可根据你的业务调整
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
    # 保存SQL到json文件到 Text2SqlwithContext/integration/sql
    project_root = get_project_root()
    output_dir = project_root / "Text2SqlwithContext" / "integration" / "sql"
    os.makedirs(output_dir, exist_ok=True)
    sql_output_path = output_dir / "results.json"
    results = {"generated_sql": sql}
    write_json(results, str(sql_output_path))
    # 执行SQL并收集所有文字信息和图表
    sql, message, chart_urls, error = run_sql_processor_and_collect_message(str(sql_output_path))
    return jsonify({
        "sql": sql,
        "result": [],
        "message": message,
        "conversation_id": session_id,
        "error": error,
        "chart_urls": chart_urls
    })


# 新的连接数据库逻辑：查找 seed 目录下的 sql 文件
@app.route('/api/connect_db', methods=['POST'])
def connect_db():
    seed_dir = os.path.join('Text2SqlwithContext', 'seed')
    sql_files = [f for f in os.listdir(seed_dir) if f.endswith('.sql')]
    if not sql_files:
        # 终端详细输出
        print("数据库导入失败：未找到SQL文件", file=sys.stderr)
        # 状态栏只返回简洁信息
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
                    # 终端详细输出
                    print(f"数据库导入异常: {e}", file=sys.stderr)
                    # 状态栏只返回简洁信息，消息框显示详细错误
                    return jsonify({'success': False, 'error': '数据库导入失败', 'detail': str(e)})
            connection.commit()
            import_results.append(f"{sql_file} 导入成功")
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'message': '，'.join(import_results)})
    except Exception as e:
        # 终端详细输出
        print(f"数据库导入异常: {e}", file=sys.stderr)
        # 状态栏只返回简洁信息，消息框显示详细错误
        return jsonify({'success': False, 'error': '数据库导入失败', 'detail': str(e)})

@app.route('/api/chart/<filename>')
def get_chart(filename):
    # 修改为绝对路径查找
    output_dir = Path(__file__).parent / "Text2SqlwithContext" / "integration" / "output"
    return send_from_directory(str(output_dir), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)