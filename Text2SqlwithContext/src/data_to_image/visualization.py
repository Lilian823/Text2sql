import matplotlib.pyplot as plt # type: ignore
import numpy as np
import pandas as pd # type: ignore
from src.sql_to_data.data_processing import translate_column

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def plot_bar_chart(df, x_column, y_columns,xlabel=None,ylabel=None,title=None,figsize=(10, 6)):
    """绘制柱状图，支持多个Y列"""
    # 输入验证
    if df is None or df.empty or not isinstance(df, pd.DataFrame):
        return None
    
    # 排除无效列
    valid_y = [col for col in y_columns if col not in ['patient_name', 'patient_id']]
    if not valid_y or x_column not in df.columns:
        return None
    
    # 创建图形对象
    fig = plt.figure(figsize=figsize)
    plt.xlabel(translate_column(x_column))
    plt.ylabel(translate_column(y_columns))
    try:
        # 限制最多显示15个条目
        if len(df) > 15:
            df = df.head(15).copy()
        
        # 准备坐标
        x = np.arange(len(df[x_column]))
        bar_width = 0.8 / len(valid_y)
        
        # 绘制每个Y列的柱状图
        for i, y_col in enumerate(valid_y):
            if y_col not in df.columns:
                continue
                
            # 计算位置偏移
            offset = (i - len(valid_y)/2) * bar_width + bar_width/2
            plt.bar(x + offset, df[y_col], width=bar_width, label=translate_column(y_col))
        
        # 设置图表属性
        plt.xlabel(translate_column(x_column))
        plt.ylabel('指标值')
        plt.title(f"{translate_column(x_column)}指标对比", fontsize=14)
        plt.xticks(x, df[x_column], rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        return fig
    except Exception as e:
        plt.close(fig)
        print(f"生成柱状图时出错: {str(e)}")
        return None

def plot_line_chart(df, x_column, y_columns,title=None, figsize=(10, 6)):
    """绘制折线图，支持多个Y列"""
    # 输入验证
    if df is None or df.empty or not isinstance(df, pd.DataFrame):
        return None
    
    # 排除无效列
    valid_y = [col for col in y_columns if col not in ['patient_name', 'patient_id']]
    if not valid_y or x_column not in df.columns:
        return None
    
    # 创建图形对象
    fig = plt.figure(figsize=figsize)
    
    try:
        # 绘制每条折线
        for y_col in valid_y:
            if y_col not in df.columns:
                continue
            plt.plot(df[x_column], df[y_col], marker='o', label=translate_column(y_col))
        
        # 设置图表属性
        plt.xlabel(translate_column(x_column))
        plt.ylabel('指标值')
        plt.title("医疗指标趋势变化", fontsize=14)
        plt.legend()
        plt.grid(True)
        
        # 如果X轴是日期，优化显示
        if pd.api.types.is_datetime64_any_dtype(df[x_column]):
            plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        return fig
    except Exception as e:
        plt.close(fig)
        print(f"生成折线图时出错: {str(e)}")
        return None

def plot_pie_chart(df, column_name, figsize=(8, 8),title = None, values=None):
    """绘制饼图，支持自定义值列（如count）"""
    if df is None or df.empty or not isinstance(df, pd.DataFrame):
        return None
    
    if column_name in ['patient_name', 'patient_id']:
        return None
        
    if column_name not in df.columns:
        return None
    
    fig = plt.figure(figsize=figsize)
    
    try:
        # 新增：支持自定义值列（如count）
        if values and values in df.columns:
            sizes = df[values]
            labels = df[column_name]
        else:
            # 默认行为：计算value_counts
            counts = df[column_name].value_counts()
            if len(counts) > 8:
                others_count = counts[8:].sum()
                counts = counts.head(7)
                counts["其他"] = others_count
            sizes = counts
            labels = counts.index
        
        # 确保至少有两个类别
        if len(sizes) < 2:
            plt.close(fig)
            return None
            
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct*total/100.0))
                return f'{pct:.1f}%\n({val}人)'
            return my_autopct
        
        plt.pie(sizes, 
                labels=labels, 
                autopct=make_autopct(sizes),
                startangle=90)
        
        plt.title(f"{translate_column(column_name)}分布", fontsize=14)
        plt.axis('equal')
        
        return fig
    except Exception as e:
        plt.close(fig)
        print(f"生成饼图时出错: {str(e)}")
        return None
