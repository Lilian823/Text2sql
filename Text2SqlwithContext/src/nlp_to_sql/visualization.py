import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from data_processing import translate_column

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def plot_bar_chart(df, x_column, y_columns, figsize=(10, 6)):
    """绘制柱状图，支持多个Y列"""
    # 排除无效列
    valid_y = [col for col in y_columns if col not in ['patient_name', 'patient_id']]
    if not valid_y or x_column not in df.columns:
        return None
    
    # 创建图形对象
    fig = plt.figure(figsize=figsize)
    
    # 限制最多显示15个条目
    if len(df) > 15:
        df = df.head(15)
    
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
    
    return fig  # 返回图形对象

def plot_line_chart(df, x_column, y_columns, figsize=(10, 6)):
    """绘制折线图，支持多个Y列"""
    # 排除无效列
    valid_y = [col for col in y_columns if col not in ['patient_name', 'patient_id']]
    if not valid_y or x_column not in df.columns:
        return None
    
    # 创建图形对象
    fig = plt.figure(figsize=figsize)
    
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
    return fig  # 返回图形对象

def plot_pie_chart(df, column_name, figsize=(8, 8)):
    """绘制饼图"""
    # 检查列是否有效
    if column_name in ['patient_name', 'patient_id', 'doctor_advice']:
        return None
    if column_name not in df.columns:
        return None
    
    # 创建图形对象
    fig = plt.figure(figsize=figsize)
    
    # 计算各类别数量
    counts = df[column_name].value_counts()
    
    # 合并小类别为"其他"
    if len(counts) > 8:
        others_count = counts[8:].sum()
        counts = counts.head(7)
        counts["其他"] = others_count
    
    # 添加百分比标签的函数
    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return f'{pct:.1f}%\n({val}人)'
        return my_autopct
    
    # 绘制饼图
    plt.pie(counts, 
            labels=counts.index, 
            autopct=make_autopct(counts),
            startangle=90)
    
    # 设置标题
    plt.title(f"{translate_column(column_name)}分布", fontsize=14)
    plt.axis('equal')
    
    return fig  # 返回图形对象