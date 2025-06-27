import pandas as pd

def generate_textual_summary(df):
    summary = f"总记录数: {len(df)}\n"
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            mean_value = df[col].mean()
            std_dev = df[col].std()
            min_value = df[col].min()
            max_value = df[col].max()
            summary += f"{col} 平均值: {mean_value:.2f}, 标准差: {std_dev:.2f}, 最小值: {min_value:.2f}, 最大值: {max_value:.2f}\n"
        elif pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            unique_values = df[col].unique()
            value_counts = df[col].value_counts().head(5)  # Show top 5 categories
            summary += f"{col} 类别统计:\n"
            for category, count in value_counts.items():
                summary += f"  {category}: {count} 次\n"
    
    return summary