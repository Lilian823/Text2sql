import json
from typing import Self
import pandas as pd # type: ignore
from .database_interaction import execute_query
from .data_processing import generate_textual_summary, translate_column
from ..data_to_image.visualization import plot_bar_chart, plot_line_chart, plot_pie_chart
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
        'medical.database_schema': 'medical_checkup',
        '`database_schema`': '`medical_checkup`',
        'medical.patient_records': 'medical_checkup',
        'patient_records': 'medical_checkup',
        'FROM medical.patient_records': 'FROM medical_checkup',
        'FROM patient_records': 'FROM medical_checkup'
        }
    
        corrected_sql = sql_query
        for wrong, right in replacements.items():
            corrected_sql = corrected_sql.replace(wrong, right)
    
        if 'FROM medical_checkup' not in corrected_sql and 'FROM `medical_checkup`' not in corrected_sql:
            from_index = corrected_sql.upper().find('FROM')
            if from_index != -1:
                corrected_sql = corrected_sql[:from_index+4] + ' medical_checkup' + corrected_sql[from_index+4:]
    
        return corrected_sql
    
    def execute_query(self, sql_query):
        if not sql_query: # type: ignore
            return None
        corrected_sql = self.correct_table_name(sql_query) # type: ignore
        self.df = execute_query(corrected_sql, "mysql")
        
        if self.df is not None:
            for col in self.df.columns:
                if col in ['fasting_glucose', 'age', 'bmi']:
                    try:
                        self.df[col] = pd.to_numeric(self.df[col], errors='ignore')
                    except:
                        pass
        return self.df

    def generate_summary(self):
        if self.df is not None and not self.df.empty:
            self.text_summary = generate_textual_summary(self.df)
            return self.text_summary
        return "无法生成摘要: 无数据或查询失败"
    def need_chart(self):
        # 如果数据为空或只有一行/一列，不需要图表
        if self.df is None or self.df.empty:
            return False
        if self.df.shape[0] == 1 or self.df.shape[1] == 1:
            return False
        columns = self.df.columns.tolist()
        # 如果有明显的分组、数值型数据，建议使用图表
        if {'gender', 'count'}.issubset(columns):
            return True
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(self.df[col])]
        # 如果没有数值型列，且大部分数据为字符串，则不建议用图表
        if len(numeric_cols) == 0:
            # 检查每列的数据类型，如果大部分为字符串则不需要图表
            str_col_count = sum(
                pd.api.types.is_string_dtype(self.df[col]) for col in columns
            )
            if str_col_count / len(columns) > 0.7:
                return False
        if len(numeric_cols) >= 1 and self.df.shape[0] > 1:
            return True
        return False
    def generate_charts(self):
        if self.df is None or self.df.empty:
            self.charts = {}
            return self.charts
    
        columns = self.df.columns.tolist()
        self.charts = {}

        # 1. 优先处理分组统计（gender + count）
        if {'gender', 'count'}.issubset(columns):
            pie_chart = plot_pie_chart(
                self.df, 
                'gender', 
                values='count',
                title="性别分布比例"
            )
            if pie_chart:
                self.charts['pie'] = pie_chart
            return self.charts

        # 2. 智能选择图表类型
        # x轴候选（优先级：姓名 > 性别 > 其他分类列）
        x_candidates = [
            col for col in columns 
            if col in ['patient_name', '患者姓名', 'gender', '性别']
            or (
                not pd.api.types.is_numeric_dtype(self.df[col]) 
                and 2 <= self.df[col].nunique() <= 15
            )
        ]
        
        # y轴候选（数值型列）
        y_candidates = [
            col for col in columns 
            if pd.api.types.is_numeric_dtype(self.df[col])
            and col not in ['patient_id', 'count']
        ]

        # 生成柱状图
        if x_candidates and y_candidates and len(self.df) <= 20:
            x_col = x_candidates[0]
            y_col = y_candidates[0]
            
            bar_chart = plot_bar_chart(
                self.df,
                x_col,
                [y_col],
                title=f"{translate_column(y_col)}分布",
                xlabel=translate_column(x_col),
                ylabel=translate_column(y_col)
            )
            if bar_chart:
                self.charts['bar'] = bar_chart

        # 生成折线图（时间序列）
        if 'checkup_date' in columns and pd.api.types.is_datetime64_any_dtype(self.df['checkup_date']):
            num_cols = [col for col in y_candidates if col != 'checkup_date']
            if num_cols:
                line_chart = plot_line_chart(
                    self.df.sort_values('checkup_date'),
                    'checkup_date',
                    num_cols[:2],
                    title="时间趋势分析"
                )
                if line_chart:
                    self.charts['line'] = line_chart

        return self.charts
    
    def process(self):
        sql_query = self.load_sql()
        if not sql_query:
            return {"status": "error", "message": "无可用SQL查询"}
        
        self.execute_query(sql_query)
        summary = self.generate_summary()
        self.generate_charts()
        
        preview_data = []
        if self.df is not None and not self.df.empty:
            preview_df = self.df.head(10).copy()
            preview_df.columns = [translate_column(col) for col in preview_df.columns]
            preview_data = preview_df.to_dict(orient='records')
        
        return {
            "status": "success",
            "summary": summary,
            "charts": list(self.charts.keys()),
            "dataframe": preview_data
        }
