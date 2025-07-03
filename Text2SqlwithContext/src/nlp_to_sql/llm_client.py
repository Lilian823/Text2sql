import openai # type: ignore
from Text2SqlwithContext.src.basic_function.config import OPENAI_API_KEY, OPENAI_API_BASE, MODEL_NAME
import time

# 配置OpenAI客户端指向DeepSeek API
openai.api_key = OPENAI_API_KEY
openai.base_url = OPENAI_API_BASE

def call_llm_model(natural_language_query, schema_info=None):
    """
    调用DeepSeek模型通过OpenAI接口将自然语言转换为SQL
    
    Args:
        natural_language_query (str): 用户的自然语言查询
        schema_info (dict, optional): 数据库结构信息
        
    Returns:
        dict: 包含生成的SQL和元数据的字典
    """
    start_time = time.time()
    
    # 构建系统提示
    system_prompt = (
        "你是一个专业的SQL专家，擅长将自然语言转换为准确的供mysql使用的查询语句。多表的关系和结构已经给出。如果表意明确，请仅返回适用于MYSQL语句，不要包含任何解释或额外文本或额外的格式处理。如果表意模糊，请返回“生成错误”，并生成给用户提示信息。如果需要结合上下文生成新的SQL，请在生成的SQL中包含上下文信息。请确保生成的SQL语句符合MYSQL语法规范。"
    )
    
    # 构建用户提示
    user_prompt = f"请将以下自然语言描述转换为SQL查询：\n\n{natural_language_query}"
    
    # 如果提供了数据库结构信息，添加到提示中
    if schema_info:
        user_prompt += f"\n\n数据库结构信息：\n{schema_info}"
    
    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1  # 低温度以获得更确定性的结果
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # 计算处理时间（毫秒）
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "generated_sql": sql_query,
            "success": True,
            "metadata": {
                "model": MODEL_NAME,
                "processing_time_ms": processing_time
            }
        }
        
    except Exception as e:
        return {
            "generated_sql": None,
            "success": False,
            "error": str(e),
            "metadata": {
                "model": MODEL_NAME
            }
        }