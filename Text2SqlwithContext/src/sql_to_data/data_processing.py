# data_processing.py
import pandas as pd # type: ignore
from typing import Dict, Optional

# 医疗指标翻译字典 - 集中定义
MEDICAL_TRANSLATION: Dict[str, str] = {
    'patient_id': '患者ID',
    'patient_name': '患者姓名',
    'age': '年龄',
    'fasting_glucose': '空腹血糖',
    'gender': '性别',
    'height': '身高',
    'weight': '体重',
    'bmi': '体质指数',
    'blood_pressure': '血压',
    'total_cholesterol': '总胆固醇',
    'triglycerides': '甘油三酯',
    'hdl': '高密度脂蛋白',
    'ldl': '低密度脂蛋白',
    'alt': '谷丙转氨酶',
    'ast': '谷草转氨酶',
    'wbc': '白细胞计数',
    'rbc': '红细胞计数',
    'hemoglobin': '血红蛋白',
    'urine_protein': '尿蛋白',
    'ecg_result': '心电图结果',
    'ultrasound_result': '超声检查结果',
    'doctor_advice': '医生建议',
    'checkup_date': '检查日期',
    # 添加更多医疗指标翻译...
}

# 医疗指标单位字典
MEDICAL_UNITS: Dict[str, str] = {
    'glucose': 'mmol/L',
    'cholesterol': 'mmol/L',
    'pressure': 'mmHg',
    'height': 'cm',
    'weight': 'kg',
    'temperature': '°C'
}

def translate_column(col: str) -> str:
    """翻译医疗指标名称
    
    Args:
        col: 需要翻译的列名
        
    Returns:
        翻译后的中文列名，如果未找到翻译则返回原列名
    """
    if not isinstance(col, str):
        return str(col)
    return MEDICAL_TRANSLATION.get(col, col)

def get_medical_unit(col_name: str) -> str:
    """获取医疗指标的单位
    
    Args:
        col_name: 列名
        
    Returns:
        该指标对应的单位，默认为空字符串
    """
    if not isinstance(col_name, str):
        return ""
    
    col_name = col_name.lower()
    for key, unit in MEDICAL_UNITS.items():
        if key in col_name:
            return unit
    return ""

def generate_textual_summary(df: Optional[pd.DataFrame]) -> str:
    """生成精简医疗数据摘要
    
    Args:
        df: 输入的DataFrame数据
        
    Returns:
        格式化后的文本摘要
    """
    # 输入验证
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return "## 核心分析结果\n\n- **无有效数据**"
    
    try:
        if set(df.columns) == {'gender', 'count'}:
            total = df['count'].sum()
            summary = "## 核心分析结果\n\n"
            for _, row in df.iterrows():
                percentage = (row['count'] / total) * 100
                summary += (
                    f"- **{translate_column(row['gender'])}**: "
                    f"{row['count']}人 ({percentage:.1f}%)\n"
                )
            return summary
        # 标识类列名单
        ID_COLS = ['patient_id', 'patient_name', 'id']
        
        summary = "## 核心分析结果\n\n"
        summary += f"- **涉及记录数**: {len(df)} 条\n"
        
        # 数值型指标分析
        num_summary = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col not in ID_COLS:
                # 计算关键指标（处理可能的空值）
                col_data = df[col].dropna()
                if len(col_data) == 0:
                    continue
                    
                mean_value = col_data.mean()
                min_value = col_data.min()
                max_value = col_data.max()
                
                # 获取单位信息
                unit = get_medical_unit(col)
                
                num_summary.append(
                    f"- **{translate_column(col)}**: "
                    f"平均{mean_value:.1f}{unit} "
                    f"(范围: {min_value:.1f}-{max_value:.1f}{unit})"
                )
        
        if num_summary:
            summary += "\n**数值指标分析**:\n" + "\n".join(num_summary)
        
        # 分类数据统计（排除标识列）
        cat_summary = []
        for col in df.columns:
            if col in ID_COLS: 
                # 特殊处理姓名类字段
                if col == 'patient_name':
                    names = df[col].dropna().unique()
                    if len(names) == 0:
                        continue
                    if len(names) <= 10:
                        cat_summary.append(f"- **涉及患者**: {', '.join(map(str, names))}")
                    else:
                        cat_summary.append(f"- **涉及患者**: {len(names)}人")
                continue
                
            if pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 0:
                    continue
                    
                if len(unique_vals) <= 5:
                    cat_summary.append(f"- **{translate_column(col)}**: {', '.join(map(str, unique_vals))}")
                else:
                    # 对于医生建议等长文本
                    if col == 'doctor_advice':
                        samples = df[col].dropna().head(20).tolist()
                        if samples:
                            cat_summary.append(f"- **{translate_column(col)}示例**:")
                            for i, advice in enumerate(samples, 1):
                                cat_summary.append(f"  {i}. {advice[:30]}{'...' if len(advice) > 30 else ''}")
                    else:
                        cat_summary.append(f"- **{translate_column(col)}**: {len(unique_vals)}种分类")
        
        if cat_summary:
            summary += "\n\n**分类数据统计**:\n" + "\n".join(cat_summary)
        
        return summary
    
    except Exception as e:
        error_msg = f"生成摘要时出错: {str(e)}"
        print(error_msg)
        return f"## 核心分析结果\n\n- **{error_msg}**"

def safe_translate_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """安全地翻译DataFrame的列名
    
    Args:
        df: 原始DataFrame
        
    Returns:
        列名翻译后的新DataFrame
    """
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    
    try:
        translated_df = df.copy()
        translated_df.columns = [translate_column(col) for col in df.columns]
        return translated_df
    except Exception as e:
        print(f"翻译列名时出错: {str(e)}")
        return df.copy()
