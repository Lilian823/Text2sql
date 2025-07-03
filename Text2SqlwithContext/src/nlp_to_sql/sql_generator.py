from Text2SqlwithContext.src.nlp_to_sql.llm_client import call_llm_model
import datetime
import uuid

def generate_sql_from_nl(query_data):
    """
    从自然语言查询生成SQL
    
    Args:
        query_data (dict): 包含查询信息的字典
        
    Returns:
        dict: 包含生成SQL和元数据的字典
    """
    # 提取查询信息
    query_id = query_data.get("query_id", str(uuid.uuid4()))
    natural_language_query = query_data.get("natural_language_query")
    schema_info = query_data.get("database_schema")
    
    # 调用大模型生成SQL
    result = call_llm_model(natural_language_query, schema_info)
    
    # 准备输出数据
    output = {
        "query_id": query_id,
        "natural_language_query": natural_language_query,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    # 添加SQL生成结果
    if result["success"]:
        output["generated_sql"] = result["generated_sql"]
        output["status"] = "success"
        output["metadata"] = result["metadata"]
    else:
        output["status"] = "error"
        # 只返回中文print内容作为error
        # 假设 result["error"] 里包含了终端print的中文内容
        # 若不是，请确保llm_client返回的error字段就是print的中文内容
        output["error"] = result["error"]  # 只保留中文错误信息
        output["metadata"] = result["metadata"]
    
    return output
