# -*- coding: utf-8 -*-
"""
Iqra 超级智能系统
深度推理、自我反思、主动学习
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable


class DeepReasoning:
    """深度推理系统 - 链式思考"""
    
    def __init__(self):
        self.reasoning_chain = []
        self.confidence_threshold = 0.7
    
    def analyze(self, query: str, context: dict = None) -> dict:
        """分析用户意图并生成推理链"""
        self.reasoning_chain = []
        
        # 步骤1: 意图识别
        intent = self._identify_intent(query)
        self.reasoning_chain.append({"step": 1, "type": "intent", "result": intent})
        
        # 步骤2: 上下文分析
        if context:
            context_analysis = self._analyze_context(context)
            self.reasoning_chain.append({"step": 2, "type": "context", "result": context_analysis})
        
        # 步骤3: 工具选择推理
        tool_reasoning = self._reason_tools(query, intent)
        self.reasoning_chain.append({"step": 3, "type": "tools", "result": tool_reasoning})
        
        # 步骤4: 执行策略
        strategy = self._formulate_strategy(intent, tool_reasoning)
        self.reasoning_chain.append({"step": 4, "type": "strategy", "result": strategy})
        
        return {
            "intent": intent,
            "reasoning_chain": self.reasoning_chain,
            "strategy": strategy,
            "confidence": self._calculate_confidence()
        }
    
    def _identify_intent(self, query: str) -> dict:
        """识别用户意图"""
        intents = {
            "search": ["搜索", "查找", "查询", "找一下", "搜一下", "查一下"],
            "file_operation": ["文件", "读取", "写入", "保存", "打开", "编辑", "删除"],
            "code_execution": ["运行", "执行", "代码", "脚本", "python", "shell"],
            "browser": ["浏览器", "网页", "打开网站", "访问", "浏览"],
            "schedule": ["定时", "提醒", "计划", "任务", "cron", "schedule"],
            "memory": ["记住", "记忆", "保存", "记录", "recall", "remember"],
            "session": ["会话", "对话", "新建", "切换", "session"],
            "business": ["订单", "产品", "客户", "财务", "销售", "库存"],
            "analysis": ["分析", "统计", "报表", "趋势", "预测"],
            "general": ["帮助", "说明", "介绍", "是什么", "怎么做"]
        }
        
        detected = []
        query_lower = query.lower()
        
        for intent_type, keywords in intents.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                detected.append({"type": intent_type, "score": score, "keywords": keywords})
        
        # 按分数排序
        detected.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "primary": detected[0]["type"] if detected else "general",
            "all_detected": detected,
            "complexity": self._assess_complexity(query)
        }
    
    def _assess_complexity(self, query: str) -> str:
        """评估查询复杂度"""
        # 简单启发式
        if len(query) < 10:
            return "simple"
        elif any(word in query for word in ["然后", "接着", "之后", "再", "并且", "同时"]):
            return "complex"
        elif "?" in query or "？" in query:
            return "moderate"
        else:
            return "moderate"
    
    def _analyze_context(self, context: dict) -> dict:
        """分析上下文"""
        return {
            "has_history": bool(context.get("history")),
            "history_length": len(context.get("history", [])),
            "current_topic": context.get("topic", "general"),
            "user_preferences": context.get("preferences", {})
        }
    
    def _reason_tools(self, query: str, intent: dict) -> dict:
        """推理需要使用的工具"""
        intent_type = intent["primary"]
        
        tool_mapping = {
            "search": ["multi_search", "web_search"],
            "file_operation": ["file_read", "file_write", "file_search", "dir_list"],
            "code_execution": ["run_code", "exec"],
            "browser": ["browser_navigate", "browser_screenshot", "browser_extract"],
            "schedule": ["schedule_task", "schedule_list"],
            "memory": ["memory_save", "memory_load", "memory_list"],
            "session": ["session_create", "session_list", "session_switch"],
            "business": ["query_products", "query_orders", "query_customers"],
            "analysis": ["analyze_sales", "detect_anomalies", "predict_inventory"],
            "general": ["web_search"]
        }
        
        return {
            "recommended_tools": tool_mapping.get(intent_type, ["web_search"]),
            "fallback_tools": ["web_search", "exec"],
            "parallel_possible": intent.get("complexity") == "complex"
        }
    
    def _formulate_strategy(self, intent: dict, tool_reasoning: dict) -> dict:
        """制定执行策略"""
        complexity = intent.get("complexity", "moderate")
        
        if complexity == "simple":
            return {
                "approach": "direct",
                "steps": ["execute_primary_tool"],
                "reasoning": "简单查询，直接执行"
            }
        elif complexity == "complex":
            return {
                "approach": "sequential",
                "steps": ["analyze", "plan", "execute_step_by_step", "verify"],
                "reasoning": "复杂查询，需要分步执行和验证"
            }
        else:
            return {
                "approach": "standard",
                "steps": ["analyze", "execute", "verify"],
                "reasoning": "标准查询，分析后执行"
            }
    
    def _calculate_confidence(self) -> float:
        """计算推理置信度"""
        if not self.reasoning_chain:
            return 0.0
        
        # 基于推理链完整性计算
        has_intent = any(s["type"] == "intent" for s in self.reasoning_chain)
        has_strategy = any(s["type"] == "strategy" for s in self.reasoning_chain)
        
        if has_intent and has_strategy:
            return 0.85
        elif has_intent:
            return 0.6
        else:
            return 0.3


class SelfReflection:
    """自我反思系统 - 从错误中学习"""
    
    def __init__(self, memory_dir: str = None):
        self.memory_dir = memory_dir or os.path.join(os.path.dirname(__file__), "data", "reflections")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.reflections = self._load_reflections()
    
    def _load_reflections(self) -> List[dict]:
        """加载历史反思记录"""
        reflection_file = os.path.join(self.memory_dir, "reflections.json")
        if os.path.exists(reflection_file):
            with open(reflection_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_reflections(self):
        """保存反思记录"""
        reflection_file = os.path.join(self.memory_dir, "reflections.json")
        with open(reflection_file, 'w', encoding='utf-8') as f:
            json.dump(self.reflections[-100:], f, ensure_ascii=False, indent=2)  # 保留最近100条
    
    def reflect(self, query: str, result: dict, success: bool) -> dict:
        """对执行结果进行反思"""
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "success": success,
            "result_summary": self._summarize_result(result),
            "lessons": []
        }
        
        if not success:
            reflection["lessons"] = self._extract_lessons(query, result)
        else:
            reflection["lessons"] = self._extract_success_patterns(query, result)
        
        self.reflections.append(reflection)
        self._save_reflections()
        
        return reflection
    
    def _summarize_result(self, result: dict) -> str:
        """总结结果"""
        if result.get("success"):
            return "执行成功"
        elif "error" in result:
            return f"错误: {result['error'][:100]}"
        else:
            return "未知结果"
    
    def _extract_lessons(self, query: str, result: dict) -> List[str]:
        """从失败中提取教训"""
        lessons = []
        error = result.get("error", "")
        
        if "not found" in error.lower() or "不存在" in error:
            lessons.append("需要验证资源存在性再操作")
        if "permission" in error.lower() or "权限" in error:
            lessons.append("需要检查操作权限")
        if "timeout" in error.lower() or "超时" in error:
            lessons.append("需要增加超时时间或优化性能")
        if "parse" in error.lower() or "解析" in error:
            lessons.append("需要验证输入格式")
        
        if not lessons:
            lessons.append("需要更仔细地分析错误原因")
        
        return lessons
    
    def _extract_success_patterns(self, query: str, result: dict) -> List[str]:
        """从成功中提取模式"""
        lessons = []
        
        if "search" in query.lower() or "搜索" in query:
            lessons.append("搜索查询使用多引擎效果更好")
        if "file" in query.lower() or "文件" in query:
            lessons.append("文件操作前检查路径存在性")
        if "code" in query.lower() or "代码" in query:
            lessons.append("代码执行需要设置合理超时")
        
        if not lessons:
            lessons.append("当前方法有效，继续保持")
        
        return lessons
    
    def get_insights(self, query_type: str = None) -> List[str]:
        """获取洞察建议"""
        if not self.reflections:
            return ["还没有足够的经验数据"]
        
        insights = []
        
        # 分析失败模式
        failures = [r for r in self.reflections if not r["success"]]
        if failures:
            recent_failures = failures[-10:]
            common_lessons = {}
            for f in recent_failures:
                for lesson in f["lessons"]:
                    common_lessons[lesson] = common_lessons.get(lesson, 0) + 1
            
            if common_lessons:
                top_lesson = max(common_lessons, key=common_lessons.get)
                insights.append(f"常见失败原因: {top_lesson}")
        
        # 分析成功率
        total = len(self.reflections)
        success_rate = len([r for r in self.reflections if r["success"]]) / total
        insights.append(f"历史成功率: {success_rate:.1%} ({total}次操作)")
        
        return insights


class ActiveLearning:
    """主动学习系统 - 持续改进"""
    
    def __init__(self, memory_dir: str = None):
        self.memory_dir = memory_dir or os.path.join(os.path.dirname(__file__), "data", "learning")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """加载学习到的模式"""
        pattern_file = os.path.join(self.memory_dir, "patterns.json")
        if os.path.exists(pattern_file):
            with open(pattern_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "query_patterns": {},
            "tool_effectiveness": {},
            "user_preferences": {}
        }
    
    def _save_patterns(self):
        """保存学习到的模式"""
        pattern_file = os.path.join(self.memory_dir, "patterns.json")
        with open(pattern_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)
    
    def learn_from_interaction(self, query: str, tools_used: List[str], result: dict, user_feedback: str = None):
        """从交互中学习"""
        # 记录查询模式
        query_type = self._classify_query(query)
        
        if query_type not in self.patterns["query_patterns"]:
            self.patterns["query_patterns"][query_type] = {"count": 0, "tools": {}, "success_rate": 0}
        
        pattern = self.patterns["query_patterns"][query_type]
        pattern["count"] += 1
        
        for tool in tools_used:
            if tool not in pattern["tools"]:
                pattern["tools"][tool] = {"uses": 0, "successes": 0}
            pattern["tools"][tool]["uses"] += 1
            if result.get("success"):
                pattern["tools"][tool]["successes"] += 1
        
        # 更新成功率
        total = pattern["count"]
        successes = sum(1 for t in tools_used if result.get("success"))
        pattern["success_rate"] = successes / total if total > 0 else 0
        
        # 记录用户反馈
        if user_feedback:
            self._process_feedback(query, user_feedback)
        
        self._save_patterns()
    
    def _classify_query(self, query: str) -> str:
        """分类查询类型"""
        if any(kw in query for kw in ["搜索", "查找", "查询"]):
            return "search"
        elif any(kw in query for kw in ["文件", "读取", "写入"]):
            return "file_operation"
        elif any(kw in query for kw in ["运行", "执行", "代码"]):
            return "code_execution"
        elif any(kw in query for kw in ["浏览器", "网页"]):
            return "browser"
        elif any(kw in query for kw in ["定时", "提醒", "计划"]):
            return "schedule"
        elif any(kw in query for kw in ["记住", "记忆"]):
            return "memory"
        elif any(kw in query for kw in ["订单", "产品", "客户"]):
            return "business"
        else:
            return "general"
    
    def _process_feedback(self, query: str, feedback: str):
        """处理用户反馈"""
        # 简单情感分析
        positive = any(kw in feedback for kw in ["好", "不错", "满意", "谢谢", "完美"])
        negative = any(kw in feedback for kw in ["错", "不对", "不行", "失败", "差"])
        
        if positive:
            self.patterns["user_preferences"]["style"] = "current"
        elif negative:
            self.patterns["user_preferences"]["needs_improvement"] = True
    
    def get_recommendations(self, query: str) -> dict:
        """基于学习历史提供建议"""
        query_type = self._classify_query(query)
        
        recommendations = {
            "suggested_tools": [],
            "tips": [],
            "confidence": 0.5
        }
        
        if query_type in self.patterns["query_patterns"]:
            pattern = self.patterns["query_patterns"][query_type]
            
            # 推荐最有效的工具
            tools = pattern.get("tools", {})
            if tools:
                best_tool = max(tools.items(), key=lambda x: x[1].get("successes", 0))
                recommendations["suggested_tools"].append(best_tool[0])
                recommendations["confidence"] = pattern.get("success_rate", 0.5)
            
            # 提供基于经验的提示
            if pattern.get("success_rate", 1) < 0.5:
                recommendations["tips"].append("此类型查询历史成功率较低，建议仔细检查")
        
        return recommendations


class SuperIntelligence:
    """超级智能系统 - 整合所有智能模块"""
    
    def __init__(self):
        self.reasoning = DeepReasoning()
        self.reflection = SelfReflection()
        self.learning = ActiveLearning()
        self.enabled = True
        self.deep_reasoning_enabled = True
        self.self_reflection_enabled = True
        self.active_learning_enabled = True
    
    def process(self, query: str, context: dict = None, execute_func: Callable = None) -> dict:
        """处理查询 - 完整的智能流程"""
        if not self.enabled:
            return {"query": query, "mode": "basic", "result": None}
        
        # 1. 深度推理
        reasoning_result = None
        if self.deep_reasoning_enabled:
            reasoning_result = self.reasoning.analyze(query, context)
        
        # 2. 获取学习建议
        learning_recommendations = {}
        if self.active_learning_enabled:
            learning_recommendations = self.learning.get_recommendations(query)
        
        # 3. 执行（如果提供了执行函数）
        execution_result = None
        if execute_func and reasoning_result:
            try:
                execution_result = execute_func(reasoning_result)
            except Exception as e:
                execution_result = {"success": False, "error": str(e)}
        
        # 4. 自我反思
        reflection_result = None
        if self.self_reflection_enabled and execution_result:
            reflection_result = self.reflection.reflect(
                query, 
                execution_result, 
                execution_result.get("success", False)
            )
        
        # 5. 学习
        if self.active_learning_enabled and execution_result:
            tools_used = reasoning_result.get("strategy", {}).get("steps", []) if reasoning_result else []
            self.learning.learn_from_interaction(query, tools_used, execution_result)
        
        return {
            "query": query,
            "mode": "super",
            "reasoning": reasoning_result,
            "recommendations": learning_recommendations,
            "execution": execution_result,
            "reflection": reflection_result,
            "insights": self.reflection.get_insights() if self.self_reflection_enabled else []
        }
    
    def toggle_feature(self, feature: str, enabled: bool):
        """开关功能"""
        if feature == "deep_reasoning":
            self.deep_reasoning_enabled = enabled
        elif feature == "self_reflection":
            self.self_reflection_enabled = enabled
        elif feature == "active_learning":
            self.active_learning_enabled = enabled
        elif feature == "all":
            self.deep_reasoning_enabled = enabled
            self.self_reflection_enabled = enabled
            self.active_learning_enabled = enabled
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "enabled": self.enabled,
            "deep_reasoning": self.deep_reasoning_enabled,
            "self_reflection": self.self_reflection_enabled,
            "active_learning": self.active_learning_enabled,
            "reflection_count": len(self.reflection.reflections),
            "learned_patterns": len(self.learning.patterns.get("query_patterns", {}))
        }


# 全局实例
_super_intelligence = None

def get_super_intelligence() -> SuperIntelligence:
    """获取超级智能实例（单例）"""
    global _super_intelligence
    if _super_intelligence is None:
        _super_intelligence = SuperIntelligence()
    return _super_intelligence
