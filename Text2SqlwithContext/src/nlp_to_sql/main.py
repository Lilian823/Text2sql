from src.nlp_to_sql.config import INPUT_QUERY_PATH, OUTPUT_SQL_PATH
from src.nlp_to_sql.json_handler import read_json, write_json
from src.nlp_to_sql.sql_generator import generate_sql_from_nl
from src.nlp_to_sql.context_manager import ContextualConversation
import os
import json

context_manager = ContextualConversation()
session_id = "user_session"  # 可根据实际需求动态生成

def process_query_multi_turn():
    print("欢迎使用text2sql系统，输入 exit 退出。")
    while True:
        nl_query = input("\n请输入想要查询的内容：\n")
        if nl_query.strip().lower() in ["exit", "quit"]:
            print("对话结束。")
            break
        if not nl_query.strip():
            print("查询内容不能为空，请输入有效的内容。")
            continue

        db_schema_path = "integration/input/db_schema.json"
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
        if "生成错误" in str(result.get("generated_sql", "")):
            clarification = result.get("generated_sql")
            print(f"{clarification}")
            # 记录历史
            context_manager.add_history(session_id, nl_query, "", result)
            continue

        # 不需要澄清，生成SQL并导出
        if result.get("status") == "success":
            print("生成的SQL:", result.get("generated_sql"))
            output_dir = os.path.dirname("integration/sql/generated_sql.json")
            generated_sql_path = os.path.join(output_dir, "generated_sql.json")
            results_path = os.path.join(output_dir, "results.json")
            # 写入 generated_sql.json
            if write_json(result, generated_sql_path):
                print("结果已保存到: generated_sql.json")
            else:
                print("结果保存失败")
            # 写入 results.json，只保留 generated_sql 字段
            results = {
                "generated_sql": result.get("generated_sql", ""),
            }
            if write_json(results, results_path):
                print("仅SQL结果已保存到: results.json")
            else:
                print("仅SQL结果保存失败")
            # 记录历史
            context_manager.add_history(session_id, nl_query, result.get("generated_sql", ""), result)
            while True:
                follow_up = input("如需对SQL进行进一步限制或补充，请输入（直接回车跳过）：\n")
                if not follow_up.strip():
                    break
                # 上下文增强
                enhanced_follow_up = context_manager.enhance_query(session_id, follow_up)
                follow_up_data = {
                    "query_id": "q_user_followup",
                    "natural_language_query": enhanced_follow_up,
                    "database_schema": db_schema,
                    "previous_sql": result.get("generated_sql", "")
                }
                follow_up_result = generate_sql_from_nl(follow_up_data)
                if follow_up_result.get("status") == "success":
                    print("完善后的SQL:", follow_up_result.get("generated_sql"))
                    # 仅当生成的SQL没有包含“生成错误”时才写入results文件
                    generated_sql = follow_up_result.get("generated_sql", "")
                    if write_json(follow_up_result, "integration/sql/generated_sql.json"):
                        print("结果已保存到: generated_sql.json")
                    else:
                        print("结果保存失败")
                    if "生成错误" not in str(generated_sql):
                        results = {
                            "generated_sql": generated_sql,
                        }
                        if write_json(results, results_path):
                            print("仅SQL结果已保存到: results.json")
                        else:
                            print("仅SQL结果保存失败")
                    else:
                        print("生成的SQL包含错误，未保存到results.json")
                    context_manager.add_history(session_id, follow_up, generated_sql, follow_up_result)
                    result = follow_up_result  # 更新result以便多轮补充
                    break
                else:
                    print("生成SQL失败:", result.get("error"))
                    context_manager.add_history(session_id, nl_query, "", result)

if __name__ == "__main__":
    process_query_multi_turn()
