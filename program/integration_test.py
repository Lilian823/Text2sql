import json
from database_interaction import execute_query, execute_non_query
from data_processing import generate_textual_summary
from visualization import plot_pie_chart, plot_bar_chart, plot_histogram, plot_line_chart, plot_scatter_plot

def test_database_interaction():
    test_cases = [
        {"db_type": "mysql", "query": "SELECT * FROM medical_checkup LIMIT 10;", "expected_records": 10},
        {"db_type": "mysql", "query": "SELECT count(*) FROM medical_checkup;", "expected_columns": ["count(*)"]},
        {"db_type": "sqlite", "query": "SELECT * FROM medical_checkup LIMIT 10;", "expected_records": 10},
        {"db_type": "sqlite", "query": "SELECT count(*) FROM medical_checkup;", "expected_columns": ["count(*)"]},
        {"db_type": "postgresql", "query": "SELECT * FROM medical_checkup LIMIT 10;", "expected_records": 10},
        {"db_type": "postgresql", "query": "SELECT count(*) FROM medical_checkup;", "expected_columns": ["count(*)"]},
        {"db_type": "sqlserver", "query": "SELECT TOP 10 * FROM medical_checkup;", "expected_records": 10},
        {"db_type": "sqlserver", "query": "SELECT COUNT(*) FROM medical_checkup;", "expected_columns": ["COUNT(*)"]}
    ]
    
    for i, test_case in enumerate(test_cases):
        db_type = test_case["db_type"]
        query = test_case["query"]
        expected_records = test_case.get("expected_records")
        expected_columns = test_case.get("expected_columns")
        
        df = execute_query(query, db_type)
        
        assert df is not None, f"测试用例 {i+1} 失败: 没有返回数据。"
        if expected_records is not None:
            assert len(df) == expected_records, f"测试用例 {i+1} 失败: 预期 {expected_records} 条记录，得到 {len(df)} 条。"
        if expected_columns is not None:
            assert all(col in df.columns for col in expected_columns), f"测试用例 {i+1} 失败: 预期列 {expected_columns}，得到 {df.columns.tolist()}。"
        
        print(f"测试用例 {i+1} 通过。")

def test_data_processing():
    query = "SELECT * FROM medical_checkup LIMIT 10;"
    df = execute_query(query, "mysql")
    
    summary = generate_textual_summary(df)
    print("文本摘要:")
    print(summary)
    
    assert "总记录数:" in summary, "数据处理测试失败: 缺少总记录数。"
    assert "age 平均值:" in summary, "数据处理测试失败: 缺少年龄平均值。"
    assert "bmi 平均值:" in summary, "数据处理测试失败: 缺少BMI平均值。"
    assert "fasting_glucose 平均值:" in summary, "数据处理测试失败: 缺少空腹血糖平均值。"
    assert "total_cholesterol 平均值:" in summary, "数据处理测试失败: 缺少总胆固醇平均值。"
    
    print("数据处理测试通过。")

def test_visualization():
    query = "SELECT * FROM medical_checkup LIMIT 10;"
    df = execute_query(query, "mysql")
    
    plot_pie_chart(df, 'gender', '性别分布')
    plot_bar_chart(df, 'age', 'bmi', '各年龄段平均BMI')
    plot_histogram(df, 'age', '年龄分布')
    plot_line_chart(df, 'age', 'bmi', '年龄与BMI关系')
    plot_scatter_plot(df, 'age', 'bmi', '年龄与BMI散点图')
    
    print("可视化测试通过。")

if __name__ == "__main__":
    test_database_interaction()
    test_data_processing()
    test_visualization()
    print("所有集成测试通过。")