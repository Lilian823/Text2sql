import json
import logging
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

class ErrorHandler:
    def __init__(self, nlu_sql_module, db_connector_module):
        """
        初始化错误处理中心
        :param nlu_sql_module: 代芷涵的自然语言处理与text2SQL模块实例
        :param db_connector_module: 熊益婕的数据库交互与结果解析模块实例
        """
        self.nlu_sql = nlu_sql_module
        self.db_connector = db_connector_module
        self.logger = self.setup_logger()
        self.monitor = SystemMonitor()
        
    def setup_logger(self):
        """配置统一的日志系统"""
        logger = logging.getLogger('Text2SQL_System')
        logger.setLevel(logging.INFO)
        
        # 统一的日志格式
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 文件日志（记录错误）
        file_handler = logging.FileHandler('system_errors.log')
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(log_format)
        
        # 性能日志
        perf_handler = logging.FileHandler('performance.log')
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(log_format)
        
        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_format)
        
        logger.addHandler(file_handler)
        logger.addHandler(perf_handler)
        logger.addHandler(console_handler)
        return logger

    def process_user_query(self, question, context=None):
        """
        处理用户查询的完整流程（集成两个队友的模块）
        返回格式: (success, result, error_details)
        """
        try:
            # 记录开始时间（性能监控）
            start_time = pd.Timestamp.now()
            
            # 调用代芷涵的模块
            nlu_result = self.nlu_sql.natural_language_understanding(question, context)
            sql_query = self.nlu_sql.generate_sql(nlu_result)
            
            # 调用熊益婕的模块
            db_result = self.db_connector.execute_sql(sql_query)
            formatted_result = self.db_connector.format_results(db_result)
            
            # 记录处理时间
            processing_time = (pd.Timestamp.now() - start_time).total_seconds()
            
            # 记录成功日志
            self.monitor.log_event("query_success", metadata={
                "question": question,
                "processing_time": processing_time
            })
            self.logger.info(f"查询处理成功: {question[:30]}... | 耗时: {processing_time:.2f}s")
            
            return True, formatted_result, None
        
        except NLUException as e:
            error_details = {
                "type": "NLU_ERROR",
                "message": str(e),
                "module": "natural_language_understanding"
            }
            self.logger.error(f"自然语言理解错误: {str(e)}")
            self.monitor.log_event("nlu_error", metadata=error_details)
            return False, "抱歉，我不太理解您的问题。请尝试换一种方式提问。", error_details
            
        except SQLGenerationException as e:
            error_details = {
                "type": "SQL_GENERATION_ERROR",
                "message": str(e),
                "input_question": question,
                "context": context
            }
            self.logger.error(f"SQL生成错误: {str(e)} | 问题: {question}")
            self.monitor.log_event("sql_generation_error", metadata=error_details)
            return False, "抱歉，我无法将这个请求转换为数据库查询。", error_details
            
        except DBConnectionException as e:
            error_details = {
                "type": "DB_CONNECTION_ERROR",
                "message": str(e),
                "sql": sql_query if 'sql_query' in locals() else "N/A"
            }
            self.logger.error(f"数据库连接错误: {str(e)}")
            self.monitor.log_event("db_connection_error", metadata=error_details)
            return False, "数据库连接出现问题，请稍后再试。", error_details
            
        except SQLExecutionException as e:
            error_details = {
                "type": "SQL_EXECUTION_ERROR",
                "message": str(e),
                "sql": sql_query,
                "db_type": self.db_connector.db_type
            }
            self.logger.error(f"SQL执行错误: {str(e)} | SQL: {sql_query}")
            self.monitor.log_event("sql_execution_error", metadata=error_details)
            return False, "数据库查询执行失败，请检查您的请求。", error_details
            
        except ResultFormattingException as e:
            error_details = {
                "type": "RESULT_FORMATTING_ERROR",
                "message": str(e),
                "raw_result": str(db_result)[:200] + "..." if 'db_result' in locals() else "N/A"
            }
            self.logger.error(f"结果格式化错误: {str(e)}")
            self.monitor.log_event("result_formatting_error", metadata=error_details)
            # 尝试返回原始数据
            try:
                raw_data = f"原始查询结果: {str(db_result)[:500]}..." if 'db_result' in locals() else "无可用数据"
                return False, f"结果处理遇到问题，但这是原始数据:\n{raw_data}", error_details
            except:
                return False, "结果处理遇到问题，且无法获取原始数据。", error_details
            
        except Exception as e:
            error_details = {
                "type": "UNEXPECTED_ERROR",
                "message": str(e)
            }
            self.logger.critical(f"未处理的系统错误: {str(e)}")
            self.monitor.log_event("system_failure", metadata=error_details)
            return False, "系统遇到意外错误，请联系管理员。", error_details

    def test_system(self, test_file="test_dataset.json"):
        """端到端系统测试与评估"""
        try:
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            
            results = []
            metrics = {
                "nlu_success": 0,
                "sql_generation_success": 0,
                "sql_execution_success": 0,
                "result_formatting_success": 0,
                "end_to_end_success": 0
            }
            
            for i, test_case in enumerate(test_data):
                test_result = {
                    "id": i+1,
                    "question": test_case["question"],
                    "expected_sql": test_case["sql"],
                    "generated_sql": "N/A",
                    "execution_result": "N/A",
                    "formatted_result": "N/A",
                    "errors": []
                }
                
                try:
                    # 测试自然语言理解
                    nlu_result = self.nlu_sql.natural_language_understanding(
                        test_case["question"], 
                        test_case.get("context")
                    )
                    metrics["nlu_success"] += 1
                    
                    # 测试SQL生成
                    generated_sql = self.nlu_sql.generate_sql(nlu_result)
                    test_result["generated_sql"] = generated_sql
                    metrics["sql_generation_success"] += 1
                    
                    # 测试SQL执行
                    db_result = self.db_connector.execute_sql(generated_sql)
                    test_result["execution_result"] = str(db_result)[:200] + "..." if db_result else "None"
                    metrics["sql_execution_success"] += 1
                    
                    # 测试结果格式化
                    formatted_result = self.db_connector.format_results(db_result)
                    test_result["formatted_result"] = str(formatted_result)[:200] + "..."
                    metrics["result_formatting_success"] += 1
                    
                    # 端到端正确性检查
                    expected_result = self.db_connector.execute_sql(test_case["sql"])
                    is_correct = self._compare_results(db_result, expected_result)
                    
                    if is_correct:
                        metrics["end_to_end_success"] += 1
                        test_result["is_correct"] = True
                    else:
                        test_result["is_correct"] = False
                        test_result["errors"].append("结果不匹配")
                    
                except Exception as e:
                    error_type = type(e).__name__
                    test_result["errors"].append(f"{error_type}: {str(e)}")
                    self.logger.error(f"测试用例 {i+1} 失败: {error_type} - {str(e)}")
                
                results.append(test_result)
            
            # 计算成功率
            total = len(test_data)
            metrics["nlu_accuracy"] = metrics["nlu_success"] / total
            metrics["sql_gen_accuracy"] = metrics["sql_generation_success"] / total
            metrics["sql_exec_accuracy"] = metrics["sql_execution_success"] / total
            metrics["formatting_accuracy"] = metrics["result_formatting_success"] / total
            metrics["end_to_end_accuracy"] = metrics["end_to_end_success"] / total
            
            # 生成报告
            report = {
                "test_cases": results,
                "module_metrics": metrics,
                "summary": {
                    "total_cases": total,
                    "end_to_end_success_rate": metrics["end_to_end_accuracy"]
                }
            }
            
            # 保存报告
            with open('system_test_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            # 记录测试结果
            self.monitor.log_event("system_test_completed", metadata={
                "total_cases": total,
                "end_to_end_accuracy": metrics["end_to_end_accuracy"]
            })
            
            return report
            
        except Exception as e:
            self.logger.error(f"系统测试失败: {str(e)}")
            return {"error": f"测试失败: {str(e)}"}

    def _compare_results(self, result1, result2):
        """比较两个数据库结果是否相等（考虑不同模块的输出格式）"""
        try:
            # 处理不同类型的结果
            if isinstance(result1, pd.DataFrame) and isinstance(result2, pd.DataFrame):
                return result1.equals(result2)
                
            elif isinstance(result1, dict) and isinstance(result2, dict):
                # 处理操作结果（如INSERT/UPDATE/DELETE）
                if "affected_rows" in result1 and "affected_rows" in result2:
                    return result1["affected_rows"] == result2["affected_rows"]
                return result1 == result2
                
            elif isinstance(result1, str) and isinstance(result2, str):
                # 处理格式化后的文本结果
                return result1.strip() == result2.strip()
                
            return str(result1) == str(result2)
        except:
            return False

    def get_performance_report(self):
        """生成性能报告"""
        events = self.monitor.get_recent_events(100)
        error_events = [e for e in events if "error" in e["event_type"] or "failure" in e["event_type"]]
        
        # 按模块分类错误
        module_errors = {
            "NLU": 0,
            "SQL_Generation": 0,
            "DB_Connection": 0,
            "SQL_Execution": 0,
            "Result_Formatting": 0,
            "Other": 0
        }
        
        for event in error_events:
            if "nlu_error" in event["event_type"]:
                module_errors["NLU"] += 1
            elif "sql_generation_error" in event["event_type"]:
                module_errors["SQL_Generation"] += 1
            elif "db_connection_error" in event["event_type"]:
                module_errors["DB_Connection"] += 1
            elif "sql_execution_error" in event["event_type"]:
                module_errors["SQL_Execution"] += 1
            elif "result_formatting_error" in event["event_type"]:
                module_errors["Result_Formatting"] += 1
            else:
                module_errors["Other"] += 1
        
        # 计算成功率
        total_events = len(events)
        success_events = len([e for e in events if "success" in e["event_type"]])
        success_rate = success_events / total_events if total_events > 0 else 0
        
        # 平均处理时间
        processing_times = [e["metadata"]["processing_time"] for e in events 
                            if "processing_time" in e.get("metadata", {})]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_queries": total_events,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time,
            "error_distribution": module_errors,
            "recent_errors": error_events[:5]  # 返回最近5个错误
        }

class SystemMonitor:
    """系统监控组件（增强版）"""
    def __init__(self, max_events=1000):
        self.events = []
        self.max_events = max_events
    
    def log_event(self, event_type, metadata=None):
        """记录系统事件"""
        event = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "event_type": event_type,
            "metadata": metadata or {}
        }
        self.events.append(event)
        
        # 保持事件列表不超过最大限制
        if len(self.events) > self.max_events:
            self.events.pop(0)
    
    def get_recent_events(self, count=50):
        """获取最近的事件"""
        return self.events[-count:] if len(self.events) > count else self.events.copy()

# 自定义异常类（与队友模块对齐）
class NLUException(Exception):
    """自然语言理解异常"""
    pass

class SQLGenerationException(Exception):
    """SQL生成异常"""
    pass

class DBConnectionException(Exception):
    """数据库连接异常"""
    pass

class SQLExecutionException(Exception):
    """SQL执行异常"""
    pass

class ResultFormattingException(Exception):
    """结果格式化异常"""
    pass