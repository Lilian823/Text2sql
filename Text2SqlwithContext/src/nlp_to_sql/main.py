from src.nlp_to_sql.config import INPUT_QUERY_PATH, OUTPUT_SQL_PATH
from src.nlp_to_sql.json_handler import read_json, write_json
from src.nlp_to_sql.sql_generator import generate_sql_from_nl
from src.nlp_to_sql.context_manager import ContextualConversation

context_manager = ContextualConversation()
session_id = "user_session"  # 可根据实际需求动态生成

def process_query_multi_turn():
    print("欢迎使用自然语言转SQL系统，输入 exit 退出。")
    while True:
        nl_query = input("\n请输入自然语言查询：\n")
        if nl_query.strip().lower() in ["exit", "quit"]:
            print("对话结束。")
            break
        if not nl_query.strip():
            print("查询内容不能为空，请输入有效的自然语言查询。")
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
        if result.get("generated_sql")== "need_clarification":
            clarification = result.get("clarification_question", "您的问题表达不明确，请补充说明：")
            print(f"澄清：{clarification}")
            # 记录历史
            context_manager.add_history(session_id, nl_query, "", result)
            continue

        # 不需要澄清，生成SQL并导出
        if result.get("status") == "success" :
            print("生成的SQL:", result.get("generated_sql"))
            if write_json(result, "integration/sql/generated_sql.json"):
                print("结果已保存到: generated_sql.json")
            else:
                print("结果保存失败")
            # 记录历史
            context_manager.add_history(session_id, nl_query, result.get("generated_sql", ""), result)
            break
        else:
            print("生成SQL失败:", result.get("error"))
            context_manager.add_history(session_id, nl_query, "", result)

if __name__ == "__main__":
    process_query_multi_turn()
