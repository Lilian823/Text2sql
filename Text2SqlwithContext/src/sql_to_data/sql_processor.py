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

        # 初始化charts字典
        self.charts = {}
        columns = self.df.columns.tolist()

        # 折线图
        if 'metric_value' in columns and 'checkup_date' in columns:
            # 获取指标名称（如果存在）
            metric_name = "指标值"
            if 'metric_name' in columns and not self.df['metric_name'].empty:
                # 取第一个非空的指标名称（直接使用，不翻译）
                metric_name = self.df['metric_name'].dropna().iloc[0] if not self.df['metric_name'].dropna().empty else "指标值"
            
            # 获取单位
            unit = None
            if 'unit' in columns and not self.df['unit'].empty:
                # 取第一个非空的单位
                unit = self.df['unit'].dropna().iloc[0] if not self.df['unit'].dropna().empty else None
            
            # 生成标题
            title = f"{metric_name}趋势分析" + (f' ({unit})' if unit else '')
            
            # 准备数据
            line_data = self.df[['checkup_date', 'metric_value']].copy()
            
            # 确保日期类型正确
            if not pd.api.types.is_datetime64_any_dtype(line_data['checkup_date']):
                try:
                    line_data['checkup_date'] = pd.to_datetime(line_data['checkup_date'])
                except:
                    pass
            
            # 生成折线图
            fig = plot_line_chart(
                line_data.sort_values('checkup_date'),
                x_column='checkup_date',
                y_columns=['metric_value'],
                title=title,
                xlabel='检查日期',  # 直接使用中文，不翻译
                ylabel=metric_name  # 直接使用指标名称
            )
            if fig:
                self.charts['line'] = fig

        # 柱状图
        # x轴候选（优先级：姓名 > 性别 > 其他分类列）
        x_candidates = [
            col for col in columns 
            if col in ['patient_name', 'name', 'gender', '性别']
            or (not pd.api.types.is_numeric_dtype(self.df[col]) 
                and 2 <= self.df[col].nunique() <= 15)
        ]
    
        y_candidates = [
            col for col in columns 
            if pd.api.types.is_numeric_dtype(self.df[col])
            and col not in ['patient_id', 'count', 'id']
        ]

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

        return self.charts  # 统一返回
    
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
