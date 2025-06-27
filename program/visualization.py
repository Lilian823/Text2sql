import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# 设置中文字体为黑体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def plot_pie_chart(df, column_name, title):
    if column_name not in df.columns:
        print(f"列 '{column_name}' 在 DataFrame 中未找到。")
        return
    
    counts = df[column_name].value_counts()
    plt.figure(figsize=(8, 6))
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90)
    plt.title(title)
    plt.axis('equal')
    plt.show()

def plot_bar_chart(df, x_column, y_column, title):
    if x_column not in df.columns or y_column not in df.columns:
        print(f"一或多列 '{x_column}' 和 '{y_column}' 在 DataFrame 中未找到。")
        return
    
    grouped = df.groupby(x_column)[y_column].mean().reset_index()
    plt.figure(figsize=(10, 6))
    plt.bar(grouped[x_column], grouped[y_column])
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(title)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_histogram(df, column_name, title):
    if column_name not in df.columns:
        print(f"列 '{column_name}' 在 DataFrame 中未找到。")
        return
    
    plt.figure(figsize=(10, 6))
    plt.hist(df[column_name], bins=10, edgecolor='black')
    plt.xlabel(column_name)
    plt.ylabel('频次')
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_line_chart(df, x_column, y_column, title):
    if x_column not in df.columns or y_column not in df.columns:
        print(f"一或多列 '{x_column}' 和 '{y_column}' 在 DataFrame 中未找到。")
        return
    
    plt.figure(figsize=(10, 6))
    plt.plot(df[x_column], df[y_column], marker='o')
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_scatter_plot(df, x_column, y_column, title):
    if x_column not in df.columns or y_column not in df.columns:
        print(f"一或多列 '{x_column}' 和 '{y_column}' 在 DataFrame 中未找到。")
        return
    
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_column], df[y_column], alpha=0.5)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_dynamic_chart(df, request_data):
    chart_type = request_data.get('chart_type', 'bar')
    title = request_data.get('title', '动态图表')
    
    if chart_type == 'bar':
        x_column = request_data.get('x_column')
        y_columns = request_data.get('y_columns', [])
        
        if not x_column or not y_columns:
            print("缺少必要的列名参数。")
            return
        
        for y_column in y_columns:
            plot_bar_chart(df, x_column, y_column, f"{title} - {y_column}")
    
    else:
        print(f"不支持的图表类型: {chart_type}")