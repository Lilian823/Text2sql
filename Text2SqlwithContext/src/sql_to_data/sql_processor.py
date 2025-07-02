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
    def __init__(self, sql_file_path='integration/sql/results.json'):
        self.sql_file_path = sql_file_path
        self.df = None
        self.text_summary = ""
        self.charts = {}
        self.query_title = ""
        
    def load_sql(self):
        try:
            with open(self.sql_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(f"加载SQL查询: {data.get('generated_sql', '无SQL查询')}")
                self.query_title = data.get('natural_language_query', '医疗查询分析').replace('\n', ' ').strip()
                return data.get('generated_sql')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"SQL处理错误: {str(e)}")
            return None
    
    def correct_table_name(self, sql_query):
        # 所有表名映射到带库名的格式
        replacements = {
            'table_name': 'medical.medical_checkup',
            'database_schema': 'medical.medical_checkup',
            'medical.database_schema': 'medical.medical_checkup',
            '`database_schema`': '`medical`.`medical_checkup`',
            'medical.patient_records': 'medical.medical_checkup',
            'patient_records': 'medical.medical_checkup',
            'FROM medical.patient_records': 'FROM medical.medical_checkup',
            'FROM patient_records': 'FROM medical.medical_checkup',
            'patients': 'medical.patients',
            'FROM patients': 'FROM medical.patients',
            'patient_metrics': 'medical.patient_metrics',
            'FROM patient_metrics': 'FROM medical.patient_metrics'
        }
    
        corrected_sql = sql_query
        for wrong, right in replacements.items():
            corrected_sql = corrected_sql.replace(wrong, right)
    
        # 特殊处理：如果SQL中未指定库名，自动添加
        tables_in_db = ['medical_checkup', 'patients', 'patient_metrics']
        for table in tables_in_db:
            if f'FROM {table}' in corrected_sql and f'FROM medical.{table}' not in corrected_sql:
                corrected_sql = corrected_sql.replace(f'FROM {table}', f'FROM medical.{table}')
    
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
    
    def generate_charts(self):
        if self.df is None or self.df.empty:
            self.charts = {}
            return self.charts

        columns = self.df.columns.tolist()
        self.charts = {}

        # 1. 处理 patient_metrics 表的折线图
        if {'metric_name', 'metric_value', 'checkup_date'}.issubset(columns):
            # 按指标分组绘制
            metrics = self.df['metric_name'].unique()
            for metric in metrics[:3]:  # 最多绘制3个指标的图表
                metric_df = self.df[self.df['metric_name'] == metric].sort_values('checkup_date')
                if len(metric_df) > 1:  # 只有多于1个数据点时才绘制折线图
                    line_chart = plot_line_chart(
                        metric_df,
                        'checkup_date',
                        ['metric_value'],
                        title=f"{translate_column(metric)}趋势变化"
                    )
                    if line_chart:
                        self.charts[f'line_{metric}'] = line_chart
            return self.charts

        # 2. 处理 patients 表的饼图
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

        # 3. 处理 medical_checkup 表的图表
        # x轴候选（优先级：姓名 > 性别 > 其他分类列）
        x_candidates = [
            col for col in columns 
            if col in ['patient_name', 'name', 'gender', '性别']
            or (
                not pd.api.types.is_numeric_dtype(self.df[col]) 
                and 2 <= self.df[col].nunique() <= 15
            )
        ]
    
        # y轴候选（数值型列）
        y_candidates = [
            col for col in columns 
            if pd.api.types.is_numeric_dtype(self.df[col])
            and col not in ['patient_id', 'count', 'id']
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
            if num_cols and len(self.df) > 1:  # 只有多于1个数据点时才绘制折线图
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
