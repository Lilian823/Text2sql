import matplotlib.pyplot as plt # type: ignore
import numpy as np
import pandas as pd # type: ignore
from Text2SqlwithContext.src.sql_to_data.data_processing import translate_column

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def plot_bar_chart(df, x_column, y_columns,xlabel=None,ylabel=None,title=None, figsize=(10, 6)):
    """绘制柱状图，支持多个Y列"""
    # 输入验证
    if df is None or df.empty or not isinstance(df, pd.DataFrame):
        return None

    # 检查姓名列是否存在，若存在则强制设为X轴
    name_columns = ['patient_name', 'name', '姓名']  # 可能的姓名列名
    for col in name_columns:
        if col in df.columns and col != x_column:
            x_column = col  # 优先使用姓名列
            break
    
    # 排除无效列
    valid_y = [col for col in y_columns if col not in ['patient_name', 'patient_id']]
    if not valid_y or x_column not in df.columns:
        return None
    
    # 创建图形对象
    fig = plt.figure(figsize=figsize)
    
    try:
        # 限制最多显示15个条目
        if len(df) > 15:
            df = df.head(15).copy()
        
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
    # 1. 输入验证增强
    if df is None or df.empty or not isinstance(df, pd.DataFrame):
        print("错误：输入数据为空或非DataFrame")
        return None
    
    # 排除无效列（保留原逻辑，扩展黑名单）
    invalid_cols = ['patient_name', 'patient_id', 'id', 'record_id']
    valid_y = [col for col in y_columns if col not in invalid_cols and col in df.columns]
    if not valid_y or x_column not in df.columns:
        print(f"错误：有效Y列({valid_y})或X列({x_column})不存在")
        return None
    
    # 2. 数据预处理
    try:
        df = df.sort_values(x_column).copy()  # 强制排序避免折线乱序
        if pd.api.types.is_datetime64_any_dtype(df[x_column]):
            df[x_column] = pd.to_datetime(df[x_column])  # 确保日期类型统一
    except Exception as e:
        print(f"数据预处理失败: {str(e)}")
        return None
    
    # 3. 动态单位处理（需确保get_medical_unit函数已定义）
    units = {col: get_medical_unit(col) for col in valid_y}  # 示例: {'glucose': 'mmol/L'}
    
    # 4. 创建图形对象（支持多子图分开展示不同单位指标）
    fig = plt.figure(figsize=figsize)
    try:
        # 情况1：所有指标单位相同 → 单图展示
        if len(set(units.values())) == 1:
            ax = fig.add_subplot(111)
            for y_col in valid_y:
                ax.plot(df[x_column], df[y_col], 
                       marker='o', 
                       label=f"{translate_column(y_col)} ({units[y_col]})")
            ax.set_ylabel(f"指标值 ({list(units.values())[0]})")
            
        # 情况2：指标单位不同 → 多子图展示
        else:
            axes = [fig.add_subplot(len(valid_y), 1, i+1) for i in range(len(valid_y))]
            for ax, y_col in zip(axes, valid_y):
                ax.plot(df[x_column], df[y_col], 
                       marker='o', 
                       color='tab:blue',  # 统一颜色便于对比
                       label=translate_column(y_col))
                ax.set_ylabel(f"{translate_column(y_col)} ({units[y_col]})")
                ax.grid(True)
                ax.legend()
        
        # 5. 公共属性设置
        plt.suptitle(title if title else "医疗指标趋势分析", fontsize=14)
        plt.xlabel(translate_column(x_column))
        
        # 日期格式优化
        if pd.api.types.is_datetime64_any_dtype(df[x_column]):
            fig.autofmt_xdate(rotation=45)
            plt.gca().xaxis.set_major_formatter(
                mdates.DateFormatter('%Y-%m-%d'))  # 统一日期格式
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        plt.close(fig)
        print(f"绘图过程中出错: {str(e)}")
        return None

def plot_pie_chart(df, column_name, figsize=(8, 8),title=None, values=None):
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
