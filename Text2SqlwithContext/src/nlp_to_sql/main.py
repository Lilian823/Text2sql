from src.nlp_to_sql.config import INPUT_QUERY_PATH, OUTPUT_SQL_PATH
from src.nlp_to_sql.json_handler import read_json, write_json
from src.nlp_to_sql.sql_generator import generate_sql_from_nl
from src.nlp_to_sql.context_manager import ContextualConversation

context_manager = ContextualConversation()
session_id = "user_session"  # 可根据实际需求动态生成

# def process_query():
#     """
#     处理自然语言查询并生成SQL
    
#     Returns:
#         bool: 处理是否成功
#     """
#     print("开始处理自然语言查询...")
    
#     # 读取输入查询
#     query_data = read_json(INPUT_QUERY_PATH)
#     if not query_data:
#         print(f"无法读取查询文件: {INPUT_QUERY_PATH}")
#         return False
    
#     print(f"成功读取查询: {query_data.get('natural_language_query', '')[:50]}...")
    
#     # 生成SQL
#     result = generate_sql_from_nl(query_data)
    
#     # 保存结果
#     if write_json(result, OUTPUT_SQL_PATH):
#         print(f"SQL生成成功，结果已保存到: {OUTPUT_SQL_PATH}")
#         if result.get("status") == "success":
#             print(f"生成的SQL: {result.get('generated_sql')}")
#         else:
#             print(f"生成SQL失败: {result.get('error')}")
#         return True
#     else:
#         print("保存结果失败")
#         return False
    
def process_query_interactive():
    print("请输入自然语言查询：")
    nl_query = input()
    print("请输入数据库结构描述：")
    db_schema = input()
    query_id = "q_user"

    # 1. 上下文增强
    enhanced_query = context_manager.enhance_query(session_id, nl_query)

    query_data = {
        "query_id": query_id,
        "natural_language_query": enhanced_query,  # 用增强后的查询
        "database_schema": db_schema
    }

    # 2. 生成SQL
    result = generate_sql_from_nl(query_data)
    print("生成结果：")
    if result.get("status") == "success":
        print("生成的SQL:", result.get("generated_sql"))
    else:
        print("生成SQL失败:", result.get("error"))

    # 3. 记录历史
    context_manager.add_history(session_id, nl_query, result.get("generated_sql", ""), result)

    # 4. 保存结果
    if write_json(result, OUTPUT_SQL_PATH):
        print(f"结果已保存到: {OUTPUT_SQL_PATH}")
    else:
        print("结果保存失败")

if __name__ == "__main__":
    process_query_interactive()
