import json
import logging
import sqlite3
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

class Text2SQLSystem:
    def __init__(self, db_path, model_name="tscholak/cxmefzzi"):
        """
        初始化智能问答系统
        :param db_path: 数据库文件路径
        :param model_name: Text2SQL模型名称
        """
        self.db_path = db_path
        self.model_name = model_name
        self.logger = self.setup_logger()
        self.monitor = SystemMonitor()
        self.dialog_context = []
        
        # 初始化Text2SQL模型
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.text2sql_pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer
            )
            self.logger.info(f"成功加载Text2SQL模型: {model_name}")
        except Exception as e:
            self.logger.error(f"模型加载失败: {str(e)}")
            raise

    def setup_logger(self):
        """配置日志系统"""
        logger = logging.getLogger('Text2SQL_System')
        logger.setLevel(logging.INFO)
        
        # 文件日志
        file_handler = logging.FileHandler('system_errors.log')
        file_handler.setLevel(logging.ERROR)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    def natural_language_understanding(self, question):
        """自然语言理解模块"""
        try:
            # 实际应用中可集成NER、意图识别等模型
            # 这里简化为返回结构化数据
            return {
                "question": question,
                "context": self.dialog_context
            }
        except Exception as e:
            self.logger.error(f"自然语言理解失败: {str(e)}")
            raise

    def generate_sql(self, nlu_result):
        """Text2SQL转换"""
        try:
            # 结合上下文生成SQL
            context = " ".join(self.dialog_context[-3:])  # 使用最近3轮对话作为上下文
            full_query = f"{context} {nlu_result['question']}" if context else nlu_result['question']
            
            # 使用模型生成SQL
            result = self.text2sql_pipeline(
                full_query,
                max_length=256,
                num_return_sequences=1
            )
            generated_sql = result[0]['generated_text'].strip()
            
            self.logger.info(f"生成SQL: {generated_sql}")
            self.monitor.log_event("sql_generation", metadata={"query": nlu_result['question'], "sql": generated_sql})
            return generated_sql
        except Exception as e:
            self.logger.error(f"SQL生成失败: {str(e)}")
            self.monitor.log_event("sql_generation_error", metadata={"error": str(e)})
            raise

    def execute_sql(self, sql):
        """执行SQL查询"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 处理不同操作类型
            if sql.strip().lower().startswith('select'):
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                return {
                    "type": "query",
                    "columns": columns,
                    "data": results
                }
            else:
                conn.commit()
                return {
                    "type": "operation",
                    "affected_rows": cursor.rowcount
                }
        except sqlite3.Error as e:
            self.logger.error(f"SQL执行错误: {str(e)} | SQL: {sql}")
            self.monitor.log_event("sql_execution_error", metadata={
                "error": str(e),
                "sql": sql
            })
            return {"error": f"数据库错误: {str(e)}"}
        finally:
            if conn:
                conn.close()

    def format_results(self, result):
        """结果格式化"""
        try:
            if "error" in result:
                return result["error"]
            
            if result["type"] == "query":
                df = pd.DataFrame(result["data"], columns=result["columns"])
                return df.to_markdown(index=False)
            else:
                return f"操作成功，影响行数: {result['affected_rows']}"
        except Exception as e:
            self.logger.error(f"结果格式化失败: {str(e)}")
            return "结果处理错误"

    def ask_question(self, question):
        """处理用户问题"""
        self.dialog_context.append(question)  # 添加上下文
        
        try:
            # 处理流程
            nlu_result = self.natural_language_understanding(question)
            sql = self.generate_sql(nlu_result)
            db_result = self.execute_sql(sql)
            formatted_result = self.format_results(db_result)
            
            # 记录成功处理
            self.monitor.log_event("query_success", metadata={
                "question": question,
                "sql": sql
            })
            
            return formatted_result
        except Exception as e:
            error_msg = f"系统处理错误: {str(e)}"
            self.logger.error(error_msg)
            self.monitor.log_event("system_error", metadata={
                "error": str(e),
                "question": question
            })
            return error_msg

    def test_system(self, test_file="test_dataset.json"):
        """系统测试与评估"""
        try:
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            
            y_true = []
            y_pred = []
            results = []
            
            for i, test_case in enumerate(test_data):
                question = test_case["question"]
                expected_sql = test_case["sql"]
                
                try:
                    nlu_result = self.natural_language_understanding(question)
                    generated_sql = self.generate_sql(nlu_result)
                    
                    # 执行生成的SQL和预期SQL
                    gen_result = self.execute_sql(generated_sql)
                    exp_result = self.execute_sql(expected_sql)
                    
                    # 对比结果
                    is_correct = str(gen_result) == str(exp_result)
                    y_true.append(1)
                    y_pred.append(1 if is_correct else 0)
                    
                    results.append({
                        "id": i+1,
                        "question": question,
                        "generated_sql": generated_sql,
                        "expected_sql": expected_sql,
                        "is_correct": is_correct,
                        "generated_result": str(gen_result)[:100] + "..." if gen_result else "",
                        "expected_result": str(exp_result)[:100] + "..." if exp_result else ""
                    })
                    
                    self.logger.info(f"测试用例 {i+1}/{len(test_data)}: {'通过' if is_correct else '失败'}")
                except Exception as e:
                    self.logger.error(f"测试用例 {i+1} 执行失败: {str(e)}")
                    y_true.append(1)
                    y_pred.append(0)
            
            # 计算指标
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            accuracy = sum(y_pred) / len(y_pred)
            
            # 生成报告
            report = {
                "test_cases": results,
                "metrics": {
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "accuracy": accuracy,
                    "total_cases": len(test_data),
                    "passed_cases": sum(y_pred)
                }
            }
            
            # 保存报告
            with open('test_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            # 监控记录
            self.monitor.log_event("system_test", metadata={
                "total_cases": len(test_data),
                "accuracy": accuracy
            })
            
            return report
        except Exception as e:
            self.logger.error(f"系统测试失败: {str(e)}")
            return {"error": f"测试失败: {str(e)}"}

class SystemMonitor:
    """系统监控组件"""
    def __init__(self):
        self.events = []
    
    def log_event(self, event_type, metadata=None):
        """记录系统事件"""
        event = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "event_type": event_type,
            "metadata": metadata or {}
        }
        self.events.append(event)
    
    def get_performance_metrics(self):
        """获取性能指标"""
        # 实际应用中可收集响应时间、成功率等指标
        return {
            "total_queries": len([e for e in self.events if e["event_type"] == "query_success"]),
            "error_rate": len([e for e in self.events if "error" in e["event_type"]]) / len(self.events) if self.events else 0
        }
    
    def get_error_logs(self):
        """获取错误日志"""
        return [e for e in self.events if "error" in e["event_type"]]

# 示例用法
if __name__ == "__main__":
    # 初始化系统
    qa_system = Text2SQLSystem("example.db")
    
    # 示例问题
    questions = [
        "销售金额最高的产品是什么？",
        "显示最近三个月的订单",
        "删除用户ID为123的记录"
    ]
    
    # 交互测试
    for q in questions:
        print(f"用户提问: {q}")
        response = qa_system.ask_question(q)
        print(f"系统回答:\n{response}\n{'-'*50}")
    
    # 执行系统测试
    test_report = qa_system.test_system()
    print("\n系统测试报告:")
    print(f"准确率: {test_report['metrics']['accuracy']:.2%}")
    print(f"F1值: {test_report['metrics']['f1_score']:.4f}")
    
    # 获取监控数据
    print("\n系统监控指标:")
    print(qa_system.monitor.get_performance_metrics())