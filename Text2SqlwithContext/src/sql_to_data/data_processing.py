# data_processing.py
import pandas as pd # type: ignore

# 医疗指标翻译字典 - 集中定义
MEDICAL_TRANSLATION = {
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
    'checkup_date': '检查日期'  # 添加检查日期字段
}

def translate_column(col):
    """翻译医疗指标名称"""
    return MEDICAL_TRANSLATION.get(col, col)

def generate_textual_summary(df):
    """生成精简医疗数据摘要"""
    if df is None or df.empty:
        return "无有效数据"
    
    # 标识类列名单
    ID_COLS = ['patient_id', 'patient_name', 'id']
    
    summary = "## 核心分析结果\n\n"
    summary += f"- **涉及记录数**: {len(df)} 条\n"
    
    # 数值型指标分析
    num_summary = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) and col not in ID_COLS:
            # 计算关键指标
            mean_value = df[col].mean()
            min_value = df[col].min()
            max_value = df[col].max()
            
            # 获取单位信息
            unit = ""
            if "glucose" in col: unit = "mmol/L"
            elif "cholesterol" in col: unit = "mmol/L"
            elif "pressure" in col: unit = "mmHg"
            
            num_summary.append(f"- **{translate_column(col)}**: "
                               f"平均{mean_value:.1f}{unit} "
                               f"(范围: {min_value:.1f}-{max_value:.1f}{unit})")
    
    if num_summary:
        summary += "\n**数值指标分析**:\n" + "\n".join(num_summary)
    
    # 分类数据统计（排除标识列）
    cat_summary = []
    for col in df.columns:
        if col in ID_COLS: 
            # 特殊处理姓名类字段
            if col == 'patient_name':
                names = df[col].unique()
                if len(names) <= 10:
                    cat_summary.append(f"- **涉及患者**: {', '.join(names)}")
                else:
                    cat_summary.append(f"- **涉及患者**: {len(names)}人")
            continue
            
        if pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            unique_vals = df[col].unique()
            if len(unique_vals) <= 5:
                cat_summary.append(f"- **{translate_column(col)}**: {', '.join(map(str, unique_vals))}")
            else:
                # 对于医生建议等长文本，只取前3条
                if col == 'doctor_advice':
                    samples = df[col].dropna().head(3).tolist()
                    cat_summary.append(f"- **{translate_column(col)}示例**:")
                    for i, advice in enumerate(samples, 1):
                        cat_summary.append(f"  {i}. {advice[:30]}...")
                else:
                    cat_summary.append(f"- **{translate_column(col)}**: {len(unique_vals)}种分类")
    
    if cat_summary:
        summary += "\n\n**分类数据统计**:\n" + "\n".join(cat_summary)
    
    return summary