import json
from database_interaction import execute_query, execute_non_query
from data_processing import generate_textual_summary
from visualization import plot_dynamic_chart

def process_sql_request(sql_json):
    request_data = json.loads(sql_json)
    db_type = request_data.get('db_type', 'mysql')
    
    # 处理查询请求
    if 'query' in request_data:
        query = request_data['query']
        
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            success = execute_non_query(query, db_type)
            print("查询执行成功。" if success else "查询执行失败。")
        else:
            df = execute_query(query, db_type)
            if df is not None and not df.empty:
                process_dataframe(df, request_data)
            else:
                print("没有找到数据或查询执行过程中发生错误。")
    else:
        print("无效的请求格式")

def process_dataframe(df, request_data):
    """处理数据框并生成所需的输出"""
    # 文本摘要
    textual_summary = generate_textual_summary(df)
    print(textual_summary)
    
    # 动态图表
    if 'dynamic_chart' in request_data:
        dynamic_chart_data = request_data['dynamic_chart']
        plot_dynamic_chart(df, dynamic_chart_data)

if __name__ == "__main__":
    # 示例JSON输入来自成员A
    example_sql_json = '''
    {
        "db_type": "mysql",
        "query": "SELECT patient_name, age, bmi FROM medical_checkup WHERE patient_name IN ('张三', '李四', '王五');",
        "dynamic_chart": {
            "chart_type": "bar",
            "x_column": "patient_name",
            "y_columns": ["age", "bmi"],
            "title": "张三、李四和王五的年龄和BMI对比"
        }
    }
    '''
    process_sql_request(example_sql_json)