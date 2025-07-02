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
        messages.append(f"处理失败: {result['message']}")
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
        for chart_type, fig in processor.charts.items():
            if fig:
                plt.figure(fig.number)
                chart_path = f"integration/output/{chart_type}_chart.png"
                plt.savefig(chart_path)
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
    # 查找 .sql 文件
    sql_files = [f for f in os.listdir(seed_dir) if f.endswith('.sql')]
    if sql_files:
        # 找到至少一个 sql 文件，返回连接成功
        return jsonify({'success': True, 'message': f'已找到数据库文件: {sql_files[0]}'})
    else:
        # 未找到，返回未连接
        return jsonify({'success': False, 'error': '未找到数据库 SQL 文件，请检查数据库文件是否正确配置'})

@app.route('/api/chart/<filename>')
def get_chart(filename):
    return send_from_directory('integration/output', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)