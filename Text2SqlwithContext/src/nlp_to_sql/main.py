import os
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from sql_processor import SQLProcessor
from src.nlp_to_sql.json_handler import read_json, write_json
from src.nlp_to_sql.sql_generator import generate_sql_from_nl
from src.nlp_to_sql.context_manager import ContextualConversation
from src.nlp_to_sql.config import get_db_config

# 初始化上下文管理器
context_manager = ContextualConversation()
session_id = "user_session"  # 可根据实际需求动态生成

def get_project_root():
    """获取项目根目录路径 (Text2SqlWithContext)"""
    return Path(__file__).resolve().parent.parent.parent

def run_sql_processor(sql_file_path):
    """执行SQL并展示结果"""
    print("\n" + "="*80)
    print("开始执行SQL并分析结果...")
    print("="*80)
    
    processor = SQLProcessor(sql_file_path)
    result = processor.process()
    
    if result['status'] == 'error':
        print(f"处理失败: {result['message']}")
        return
    
    # 输出文本摘要
    print("\n" + "="*80)
    print("医疗数据分析摘要:")
    print("="*80)
    print(result['summary'])
    
    # 显示图表
    if processor.charts:
        print("\n" + "="*80)
        print("生成的数据可视化图表:")
        print("="*80)
        for chart_type, fig in processor.charts.items():
            if fig:  # 确保图表有效
                print(f"\n显示图表: {chart_type}图")
                plt.figure(fig.number)
                plt.show()
    else:
        print("\n未生成任何图表")
    
    # 数据预览 - 显示中文列名
    print("\n" + "="*80)
    print("数据预览 (前10行):")
    print("="*80)
    
    if result['dataframe']:
        # 创建临时DataFrame用于美观显示
        preview_df = pd.DataFrame(result['dataframe'])
        print(preview_df.to_string(index=False))
    else:
        print("无数据可显示")
    
    print("\n分析完成!")

def process_query_multi_turn():
    """处理多轮对话的SQL生成过程"""
    project_root = get_project_root()
    
    # 构建正确的文件路径
    db_schema_path = project_root / "integration" / "input" / "db_schema.json"
    sql_output_path = project_root / "integration" / "sql" / "generated_sql.json"
    
    # 确保输出目录存在
    sql_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("欢迎使用text2sql系统，输入 exit 退出。")
    
    while True:
        nl_query = input("\n请输入想要查询的内容：\n")
        if nl_query.strip().lower() in ["exit", "quit"]:
            print("对话结束。")
            break
        if not nl_query.strip():
            print("查询内容不能为空，请输入有效的内容。")
            continue

        try:
            with open(db_schema_path, "r", encoding="utf-8") as f:
                db_schema = f.read()
            if not db_schema.strip():
                print("数据库结构文件为空，请检查文件内容。")
                continue
        except Exception as e:
            print(f"读取数据库结构文件失败: {e}")
            continue

        # 上下文增强
        enhanced_query = context_manager.enhance_query(session_id, nl_query)
        query_data = {
            "query_id": "q_user",
            "natural_language_query": enhanced_query,
            "database_schema": db_schema
        }

        # 先判断是否需要澄清
        result = generate_sql_from_nl(query_data)
        if "需要澄清" in str(result.get("generated_sql", "")):
            clarification = result.get("generated_sql")
            print(f"{clarification}")
            # 记录历史
            context_manager.add_history(session_id, nl_query, "", result)
            continue

        # 不需要澄清，生成SQL并导出
        if result.get("status") == "success":
            generated_sql = result.get("generated_sql")
            print("生成的SQL:", generated_sql)
            
            # 保存SQL到文件
            save_result = write_json(result, sql_output_path)
            if save_result:
                print(f"结果已保存到: {sql_output_path}")
                
                # 立即执行SQL并展示结果
                run_sql_processor(sql_output_path)
            else:
                print("结果保存失败")
            
            # 记录历史
            context_manager.add_history(session_id, nl_query, generated_sql, result)
            
            while True:
                follow_up = input("\n如需对SQL进行进一步限制或补充，请输入（直接回车跳过）：\n")
                if not follow_up.strip():
                    break
                
                # 上下文增强
                enhanced_follow_up = context_manager.enhance_query(session_id, follow_up)
                follow_up_data = {
                    "query_id": "q_user_followup",
                    "natural_language_query": enhanced_follow_up,
                    "database_schema": db_schema,
                    "previous_sql": generated_sql
                }
                
                follow_up_result = generate_sql_from_nl(follow_up_data)
                if follow_up_result.get("status") == "success":
                    new_sql = follow_up_result.get("generated_sql")
                    print("完善后的SQL:", new_sql)
                    
                    # 更新SQL文件
                    save_result = write_json(follow_up_result, sql_output_path)
                    if save_result:
                        print(f"结果已更新保存到: {sql_output_path}")
                        
                        # 重新执行SQL并展示结果
                        run_sql_processor(sql_output_path)
                    else:
                        print("结果保存失败")
                    
                    context_manager.add_history(session_id, follow_up, new_sql, follow_up_result)
                    result = follow_up_result
                    generated_sql = new_sql
                else:
                    print("完善SQL失败:", follow_up_result.get("error"))
                    context_manager.add_history(session_id, follow_up, "", follow_up_result)
                    break
        else:
            print("生成SQL失败:", result.get("error"))
            context_manager.add_history(session_id, nl_query, "", result)

if __name__ == "__main__":
    process_query_multi_turn()
