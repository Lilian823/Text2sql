import re
import json
from datetime import datetime
from collections import deque
from typing import Dict, List, Tuple, Optional
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, TokenList
from sqlparse.tokens import Keyword, DML

class ContextualConversation:
    """
    上下文关联核心模块
    实现多轮对话管理、指代消解和上下文整合功能
    """
    
    def __init__(self, max_history: int = 5, session_timeout: int = 1800):
        """
        初始化上下文管理器
        
        参数:
            max_history: 每个会话保存的最大历史记录数
            session_timeout: 会话超时时间（秒）
        """
        self.sessions: Dict[str, dict] = {}
        self.max_history = max_history
        self.session_timeout = session_timeout
        self.entity_map = {}  # 实体映射表（用于指代消解）
        
    def create_session(self, session_id: str) -> dict:
        """
        创建新的会话
        
        参数:
            session_id: 会话唯一标识
            
        返回:
            新创建的会话对象
        """
        self.sessions[session_id] = {
            "history": deque(maxlen=self.max_history),
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "entities": {}  # 当前会话的实体映射
        }
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        获取会话对象，如果不存在则创建
        
        参数:
            session_id: 会话唯一标识
            
        返回:
            会话对象或None(如果会话过期)
        """
        self.clean_expired_sessions()
        
        if session_id not in self.sessions:
            return self.create_session(session_id)
        
        # 更新最后活动时间
        self.sessions[session_id]["last_activity"] = datetime.now()
        return self.sessions[session_id]
    
    def clean_expired_sessions(self):
        """清理过期的会话"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            elapsed = (now - session["last_activity"]).total_seconds()
            if elapsed > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
    
    def add_history(self, session_id: str, user_query: str, generated_sql: str, result: dict):
        """
        添加对话历史记录
        
        参数:
            session_id: 会话ID
            user_query: 用户原始查询
            generated_sql: 生成的SQL语句
            result: 查询结果
        """
        session = self.get_session(session_id)
        if not session:
            return
        
        # 更新实体映射
        self._update_entities(session_id, user_query, generated_sql)
        
        # 添加历史记录
        session["history"].append({
            "timestamp": datetime.now(),
            "user_query": user_query,
            "generated_sql": generated_sql,
            "result": result
        })
    
    def get_context_summary(self, session_id: str) -> str:
        """
        获取上下文摘要（用于提示工程）
        
        参数:
            session_id: 会话ID
            
        返回:
            上下文摘要字符串
        """
        session = self.get_session(session_id)
        if not session or not session["history"]:
            return "这是对话的开始，没有历史上下文。"
        
        context_lines = []
        
        # 添加实体摘要
        if session["entities"]:
            entity_summary = ", ".join([f"{k}:{v}" for k, v in session["entities"].items()])
            context_lines.append(f"当前对话涉及的实体: {entity_summary}")
        
        # 添加最近的历史记录
        context_lines.append("最近的对话历史:")
        for i, entry in enumerate(reversed(session["history"])):
            context_lines.append(f"  [{i+1}] 用户: {entry['user_query']}")
            context_lines.append(f"      SQL: {entry['generated_sql']}")
        
        return "\n".join(context_lines)
    
    def resolve_references(self, session_id: str, query: str) -> str:
        """
        处理指代消解（将"这个"、"它"等代词替换为具体实体）
        
        参数:
            session_id: 会话ID
            query: 用户查询
            
        返回:
            替换代词后的查询
        """
        session = self.get_session(session_id)
        if not session or not session["entities"]:
            return query
        
        # 检测常见代词
        pronouns = ["这个", "这些", "它", "它们", "其", "该"]
        
        for pronoun in pronouns:
            if pronoun in query:
                # 尝试替换为最近提到的实体
                if session["entities"]:
                    last_entity = list(session["entities"].keys())[-1]
                    query = query.replace(pronoun, last_entity)
        
        return query
    
    def enhance_query(self, session_id: str, query: str) -> str:
        """
        增强用户查询，整合上下文信息
        
        参数:
            session_id: 会话ID
            query: 用户原始查询
            
        返回:
            增强后的查询（包含上下文提示）
        """
        resolved_query = self.resolve_references(session_id, query)
        context_summary = self.get_context_summary(session_id)
        
        return f"""
        基于以下对话上下文:
        {context_summary}
        
        用户的新问题是:
        {resolved_query}
        
        请综合考虑上下文信息生成SQL。
        """
    
    def detect_context_shift(self, session_id: str, current_query: str) -> bool:
        """
        检测上下文是否发生主题切换
        
        参数:
            session_id: 会话ID
            current_query: 当前查询
            
        返回:
            True 如果检测到主题切换
        """
        session = self.get_session(session_id)
        if not session or len(session["history"]) < 2:
            return False
        
        # 提取最近查询的主题关键词
        last_query = session["history"][-1]["user_query"]
        last_keywords = self._extract_keywords(last_query)
        
        # 提取当前查询的主题关键词
        current_keywords = self._extract_keywords(current_query)
        
        # 计算关键词相似度
        common_keywords = set(last_keywords) & set(current_keywords)
        similarity = len(common_keywords) / max(len(last_keywords), 1)
        
        return similarity < 0.3
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取查询中的关键词（简化实现）"""
        # 过滤停用词
        stopwords = {"的", "是", "在", "和", "有", "查询", "显示", "获取"}
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        return [word for word in words if word not in stopwords]
    
    def _update_entities(self, session_id: str, user_query: str, sql: str):
        """使用专业 SQL 解析库结构化维护实体和表关系，支持多表和嵌套查询"""

        session = self.get_session(session_id)
        if not session:
            return

        def extract_tables_and_columns(parsed):
            tables = set()
            columns = set()

            def is_subselect(parsed):
                if not parsed.is_group:
                    return False
                for item in parsed.tokens:
                    if item.ttype is DML and item.value.upper() == 'SELECT':
                        return True
                return False

            def extract_from_token(token):
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        extract_from_token(identifier)
                elif isinstance(token, Identifier):
                    # 处理表名和别名
                    tables.add(token.get_real_name())
                elif token.ttype is Keyword:
                    pass
                elif token.is_group:
                    for t in token.tokens:
                        extract_from_token(t)

            def extract_select_columns(token):
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        columns.add(identifier.get_real_name() or identifier.get_name())
                elif isinstance(token, Identifier):
                    columns.add(token.get_real_name() or token.get_name())
                elif token.is_group:
                    for t in token.tokens:
                        extract_select_columns(t)

            for statement in parsed:
                from_seen = False
                select_seen = False
                for token in statement.tokens:
                    if token.is_group and is_subselect(token):
                        # 递归处理子查询
                        sub_tables, sub_columns = extract_tables_and_columns([token])
                        tables.update(sub_tables)
                        columns.update(sub_columns)
                    if token.ttype is DML and token.value.upper() == 'SELECT':
                        select_seen = True
                    if select_seen and token.ttype is Keyword and token.value.upper() == 'FROM':
                        from_seen = True
                        select_seen = False
                    elif select_seen and not token.is_whitespace:
                        extract_select_columns(token)
                    elif from_seen and not token.is_whitespace:
                        extract_from_token(token)
                        from_seen = False
            return tables, columns

        parsed = sqlparse.parse(sql)
        tables, columns = extract_tables_and_columns(parsed)

        # 从用户查询中提取实体名词
        nouns = self._extract_nouns(user_query)

        # 结构化维护实体关系
        if "entities" not in session or not isinstance(session["entities"], dict):
            session["entities"] = {}

        # 维护表-字段映射
        for table in tables:
            if table not in session["entities"]:
                session["entities"][table] = {"count": 1, "columns": set()}
            else:
                session["entities"][table]["count"] += 1
            session["entities"][table]["columns"].update(columns)

        # 维护名词实体出现次数
        for noun in nouns:
            if noun not in session["entities"]:
                session["entities"][noun] = {"count": 1, "columns": set()}
            else:
                session["entities"][noun]["count"] += 1

        # 将 set 转为 list 以便序列化
        for entity in session["entities"]:
            if isinstance(session["entities"][entity].get("columns", None), set):
                session["entities"][entity]["columns"] = list(session["entities"][entity]["columns"])
    
    def _extract_nouns(self, text: str) -> List[str]:
        """从中文文本中提取名词，适配 medical_checkup 表及医学体检相关字段"""
        # 只匹配 medical_checkup 表及其字段
        medical_fields = [
            "体检表", "medical_checkup", "id", "patient_id", "patient_name", "gender", "age", "checkup_date", "height", "weight", "bmi", "blood_pressure", "fasting_glucose", "total_cholesterol", "triglycerides", "hdl", "ldl", "alt", "ast", "wbc", "rbc", "hemoglobin", "urine_protein", "ecg_result", "ultrasound_result", "doctor_advice", "created_at",
            "编号", "姓名", "性别", "年龄", "体检日期", "身高", "体重", "体质指数", "血压", "空腹血糖", "总胆固醇", "甘油三酯", "高密度脂蛋白", "低密度脂蛋白", "谷丙转氨酶", "谷草转氨酶", "白细胞计数", "红细胞计数", "血红蛋白", "尿蛋白", "心电图结果", "超声检查结果", "医生建议", "创建时间"
        ]
        # 构造正则，优先匹配字段名
        field_pattern = r"|".join([re.escape(f) for f in medical_fields if f])
        noun_patterns = [
            rf'({field_pattern})',  # 只匹配表和字段
        ]
        nouns = []
        for pattern in noun_patterns:
            matches = re.findall(pattern, text)
            nouns.extend(matches)
        # 去重，保持顺序
        seen = set()
        result = []
        for n in nouns:
            if n and n not in seen:
                seen.add(n)
                result.append(n)
        return result
    
    def clear_session(self, session_id: str):
        """清除指定会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def save_to_file(self, file_path: str):
        """将会话状态保存到文件"""
        serializable = {}
        for session_id, session in self.sessions.items():
            serializable[session_id] = {
                "history": list(session["history"]),
                "created_at": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "entities": session["entities"]
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, file_path: str):
        """从文件加载会话状态"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for session_id, session_data in data.items():
                self.sessions[session_id] = {
                    "history": deque(session_data["history"], maxlen=self.max_history),
                    "created_at": datetime.fromisoformat(session_data["created_at"]),
                    "last_activity": datetime.fromisoformat(session_data["last_activity"]),
                    "entities": session_data["entities"]
                }
        except FileNotFoundError:
            print(f"警告: 会话文件 {file_path} 不存在")
        except json.JSONDecodeError:
            print(f"错误: 会话文件 {file_path} 格式无效")