import json
from typing import Self
import pandas as pd # type: ignore

from src.nlp_to_sql.database_interaction import execute_query
from src.sql_to_data.data_processing import generate_textual_summary, translate_column
from src.data_to_image.visualization import plot_bar_chart, plot_line_chart, plot_pie_chart
import warnings
import matplotlib.pyplot as plt # type: ignore
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
class SQLProcessor:
    def __init__(self, sql_file_path='integration/sql/generated_sql.json'):
        self.sql_file_path = sql_file_path
        self.df = None
        self.text_summary = ""
        self.charts = {}
        self.query_title = ""
        
    def load_sql(self):
        try:
            with open(self.sql_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.query_title = data.get('natural_language_query', '医疗查询分析').replace('\n', ' ').strip()
                return data.get('generated_sql')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"SQL处理错误: {str(e)}")
            return None
    
    def correct_table_name(self, sql_query):
        replacements = {
        'table_name': 'medical_checkup',
        'database_schema': 'medical_checkup',
        'FROM medical.database_schema': 'FROM medical_checkup',
        'FROM `database_schema`': 'FROM medical_checkup'
        }
    
        corrected_sql = sql_query
        for wrong, right in replacements.items():
            corrected_sql = corrected_sql.replace(wrong, right)
    
        return corrected_sql
    
    def execute_query(self, sql_query):
        if not sql_query: # type: ignore
            return None
        corrected_sql = self.correct_table_name(sql_query) # type: ignore
        self.df = execute_query(corrected_sql, "mysql")
        
        # 自动转换数值型字段
        if self.df is not None:
            for col in self.df.columns:
                if col in ['fasting_glucose', 'age', 'bmi']:  # 明确指定应转换的字段
                    try:
                        self.df[col] = pd.to_numeric(self.df[col], errors='ignore')
                    except:
                        pass
        return self.df

    def generate_summary(self):
        """
        如果DataFrame存在且非空，则生成文本摘要。

        返回:
            str: 如果DataFrame存在且非空，返回生成的文本摘要；
             否则返回无法生成摘要的错误信息。
        """
        if self.df is not None and not self.df.empty:
            self.text_summary = generate_textual_summary(self.df)
            return self.text_summary
        return "无法生成摘要: 无数据或查询失败"
    
    def generate_charts(self):
        if self.df is None or self.df.empty or len(self.df) < 3:
            self.charts = {}
            return self.charts
        columns = self.df.columns.tolist()
        
        # 1. 柱状图 - 当有合适的X轴和Y轴数据时
        x_col = next((col for col in ['patient_name', 'patient_id'] if col in columns), None)
        if x_col:
            num_cols = [col for col in columns 
                       if pd.api.types.is_numeric_dtype(self.df[col]) 
                       and col not in ['patient_name', 'patient_id']
                       and not self.df[col].isnull().all()]
            
            if num_cols and len(self.df) <= 20:  # 限制数据量
                self.charts['bar'] = plot_bar_chart(self.df, x_col, num_cols[:3])
        
        # 2. 折线图 - 仅在日期字段和数值字段有效时
        if 'checkup_date' in columns and pd.api.types.is_datetime64_any_dtype(self.df['checkup_date']):
            num_cols = [col for col in columns 
                       if pd.api.types.is_numeric_dtype(self.df[col]) 
                       and col not in ['patient_name', 'patient_id']
                       and not self.df[col].isnull().all()]
            
            if num_cols and len(self.df) >= 5:  # 至少5个数据点
                # 确保日期排序
                sorted_df = self.df.sort_values('checkup_date')
                self.charts['line'] = plot_line_chart(sorted_df, 'checkup_date', num_cols[:2])
        
        # 3. 饼图 - 仅当分类数据合适时
        cat_cols = [col for col in columns 
                   if not pd.api.types.is_numeric_dtype(self.df[col]) 
                   and col not in ['patient_name', 'patient_id', 'doctor_advice', 'ecg_result', 'ultrasound_result']
                   and 2 <= self.df[col].nunique() <= 8]
        
        if cat_cols:
            # 选择最合适的分类列（类别数量适中）
            best_col = min(cat_cols, key=lambda col: abs(5 - self.df[col].nunique()))
            self.charts['pie'] = plot_pie_chart(self.df, best_col)
        
        return self.charts
    
    def process(self):
        sql_query = self.load_sql()
        if not sql_query:
            return {"status": "error", "message": "无可用SQL查询"}
        
        self.execute_query(sql_query)
        summary = self.generate_summary()
        self.generate_charts()
        
        # 准备数据预览（翻译列名）
        preview_data = []
        if self.df is not None and not self.df.empty:
            preview_df = self.df.head(10).copy()
            # 翻译列名
            preview_df.columns = [translate_column(col) for col in preview_df.columns]
            preview_data = preview_df.to_dict(orient='records')
        
        return {
            "status": "success",
            "summary": summary,
            "charts": list(self.charts.keys()),
            "dataframe": preview_data
        }