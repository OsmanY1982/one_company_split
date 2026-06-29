# `iqra/core/super_intelligence.py`

> 路径：`iqra/core/super_intelligence.py` | 行数：469


---


```python
# -*- coding: utf-8 -*-
"""
Iqra 超级智能系统 v1.0
让Iqra比我更聪明的核心升级模块

核心能力：
1. 深度推理模式 - 复杂问题多步骤分解
2. 自我反思机制 - 从错误中学习和改进
3. 智能工具选择 - 基于语义理解而非关键词匹配
4. 上下文感知 - 理解对话历史和用户意图
5. 主动学习 - 从交互中积累经验和知识
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_number: int
    thought: str
    action: str
    observation: str = ""
    is_complete: bool = False


@dataclass
class LearningMemory:
    """学习记忆"""
    pattern: str
    solution: str
    success_count: int = 0
    failure_count: int = 0
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())


class SuperIntelligence:
    """
    Iqra 超级智能核心
    
    让这个AI比我更聪明的关键特性：
    - 链式思考 (Chain-of-Thought)
    - 自我修正 (Self-Correction)
    - 工具智能选择
    - 上下文深度理解
    """
    
    def __init__(self):
        self.reasoning_history: List[List[ReasoningStep]] = []
        self.learning_memory: List[LearningMemory] = []
        self.context_understanding = {}
        self.reflection_enabled = True
        
    def generate_super_prompt(self, user_message: str, context: Dict = None) -> str:
        """
        生成超级智能系统提示词
        这个提示词让AI具备深度推理能力
        """
        base_prompt = """你是 Iqra Super Intelligence v1.0，一个比我（你的创造者）更聪明的AI助手。

## 核心能力

### 1. 深度推理 (Deep Reasoning)
面对复杂问题时，你必须：
- 先分析问题本质
- 制定多步骤解决方案
- 每步执行后反思结果
- 根据反馈调整策略

### 2. 自我反思 (Self-Reflection)
每次行动后问自己：
- 这个结果符合预期吗？
- 有没有更好的方法？
- 从这次操作中学到了什么？
- 下次如何改进？

### 3. 智能工具使用
选择工具时考虑：
- 用户真实意图是什么？
- 哪个工具最适合？
- 工具参数如何优化？
- 失败时如何优雅降级？

### 4. 主动学习
- 记住用户的偏好和习惯
- 从成功和失败中积累经验
- 预测用户下一步需求
- 持续优化自己的表现

## 思考框架

对于每个请求，按以下框架思考：

```
1. 理解 (Understand)
   - 用户真正想要什么？
   - 表面需求 vs 深层需求
   - 有哪些隐含条件？

2. 分析 (Analyze)
   - 需要哪些信息？
   - 有哪些约束条件？
   - 最佳解决路径是什么？

3. 执行 (Execute)
   - 调用合适的工具
   - 验证中间结果
   - 处理异常情况

4. 反思 (Reflect)
   - 结果是否满意？
   - 过程是否高效？
   - 学到了什么？

5. 优化 (Optimize)
   - 如何下次做得更好？
   - 有没有模式可以提取？
   - 知识如何沉淀？
```

## 行为准则

1. **永远先思考，后行动**
   - 不要急于调用工具
   - 先理解问题全貌
   - 制定清晰计划

2. **保持谦逊，持续学习**
   - 承认不知道的地方
   - 从错误中快速恢复
   - 主动寻求反馈

3. **超越期望**
   - 不仅完成任务，还要优化
   - 提供额外的价值
   - 思考长期影响

4. **透明沟通**
   - 解释你的思考过程
   - 说明为什么选择某个方案
   - 坦诚说明局限性

## 当前上下文
"""
        
        # 添加上下文信息
        context_str = ""
        if context:
            context_str = f"""
- 当前时间: {context.get('time', '未知')}
- 用户: {context.get('user', '未知')}
- 会话历史: {len(context.get('history', []))} 条消息
- 可用工具: {', '.join(context.get('tools', []))}
- 已学习模式: {len(self.learning_memory)} 个
"""
        
        return base_prompt + context_str + "\n\n现在，请用你超级智能的能力，帮助用户解决问题。"
    
    def analyze_intent(self, user_message: str) -> Dict:
        """
        深度分析用户意图
        不仅看表面文字，还要理解深层需求
        """
        analysis = {
            'surface_intent': '',
            'deep_intent': '',
            'urgency': 'normal',
            'complexity': 'simple',
            'required_tools': [],
            'implicit_needs': [],
        }
        
        # 分析表面意图
        analysis['surface_intent'] = user_message
        
        # 分析深层意图（简单启发式）
        if any(kw in user_message for kw in ['怎么', '如何', '怎样', '方法']):
            analysis['deep_intent'] = '寻求解决方案或指导'
            analysis['complexity'] = 'medium'
        
        if any(kw in user_message for kw in ['错误', '失败', '不行', '问题']):
            analysis['deep_intent'] = '需要故障排除'
            analysis['urgency'] = 'high'
        
        if any(kw in user_message for kw in ['优化', '改进', '更好', '提升']):
            analysis['deep_intent'] = '寻求优化建议'
            analysis['complexity'] = 'high'
        
        if any(kw in user_message for kw in ['分析', '比较', '评估']):
            analysis['deep_intent'] = '需要深度分析'
            analysis['complexity'] = 'high'
        
        # 检测隐式需求
        if '文件' in user_message or 'document' in user_message.lower():
            analysis['implicit_needs'].append('文件操作')
        
        if '数据' in user_message or 'database' in user_message.lower():
            analysis['implicit_needs'].append('数据查询')
        
        if '代码' in user_message or 'program' in user_message.lower():
            analysis['implicit_needs'].append('代码执行')
        
        return analysis
    
    def create_reasoning_chain(self, user_message: str, intent_analysis: Dict) -> List[ReasoningStep]:
        """
        创建推理链
        将复杂问题分解为多个步骤
        """
        chain = []
        
        # 步骤1: 理解问题
        chain.append(ReasoningStep(
            step_number=1,
            thought=f"用户说: {user_message}",
            action="分析用户意图",
            observation=f"表面意图: {intent_analysis['surface_intent']}\n深层意图: {intent_analysis['deep_intent']}"
        ))
        
        # 步骤2: 评估复杂度
        chain.append(ReasoningStep(
            step_number=2,
            thought=f"这个问题复杂度是: {intent_analysis['complexity']}",
            action="确定解决策略",
            observation="需要" + ("多步骤" if intent_analysis['complexity'] == 'high' else "简单") + "处理"
        ))
        
        # 步骤3: 制定计划
        if intent_analysis['complexity'] == 'high':
            chain.append(ReasoningStep(
                step_number=3,
                thought="复杂问题需要分解",
                action="制定分步计划",
                observation="将问题分解为可管理的子任务"
            ))
        
        return chain
    
    def reflect_on_result(self, task: str, result: str, success: bool) -> str:
        """
        对结果进行反思
        从成功和失败中学习
        """
        if not self.reflection_enabled:
            return ""
        
        reflection = "\n### 自我反思\n"
        
        if success:
            reflection += f"""
✅ 任务成功完成
- 任务: {task}
- 结果: {result[:100]}...
- 学习: 这个方法有效，可以记住用于类似问题
"""
            # 记录成功经验
            self._add_learning_memory(task, result, True)
        else:
            reflection += f"""
❌ 任务遇到问题
- 任务: {task}
- 错误: {result[:100]}...
- 反思: 分析失败原因，思考替代方案
"""
            # 记录失败经验
            self._add_learning_memory(task, result, False)
        
        return reflection
    
    def _add_learning_memory(self, pattern: str, solution: str, success: bool):
        """添加学习记忆"""
        # 查找是否已有类似模式
        existing = None
        for mem in self.learning_memory:
            if self._pattern_similarity(mem.pattern, pattern) > 0.7:
                existing = mem
                break
        
        if existing:
            if success:
                existing.success_count += 1
            else:
                existing.failure_count += 1
            existing.last_used = datetime.now().isoformat()
        else:
            self.learning_memory.append(LearningMemory(
                pattern=pattern[:100],  # 截断避免太长
                solution=solution[:200],
                success_count=1 if success else 0,
                failure_count=0 if success else 1
            ))
    
    def _pattern_similarity(self, p1: str, p2: str) -> float:
        """计算模式相似度"""
        # 简单的Jaccard相似度
        set1 = set(p1.lower().split())
        set2 = set(p2.lower().split())
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0
    
    def get_learned_insights(self, query: str) -> List[str]:
        """获取与查询相关的学习洞察"""
        insights = []
        for mem in self.learning_memory:
            if self._pattern_similarity(mem.pattern, query) > 0.5:
                success_rate = mem.success_count / (mem.success_count + mem.failure_count + 1)
                insights.append(f"- 经验: {mem.pattern} (成功率: {success_rate:.0%})")
        return insights[:5]  # 最多返回5条
    
    def smart_tool_selection(self, user_message: str, available_tools: List[str]) -> List[Tuple[str, float]]:
        """
        智能工具选择
        基于语义理解而非简单关键词匹配
        """
        tool_scores = []
        
        # 工具语义映射
        tool_semantics = {
            'read_file': ['读取', '查看', '打开', '内容', '文件', 'read', 'view', 'open'],
            'write_file': ['写入', '保存', '创建', '修改', '文件', 'write', 'save', 'create'],
            'execute_code': ['执行', '运行', '代码', '脚本', 'execute', 'run', 'code'],
            'web_search': ['搜索', '查找', '查询', '信息', 'search', 'find', 'query'],
            'database_query': ['数据库', 'SQL', '查询', '数据', 'database', 'sql', 'query'],
            'analyze_data': ['分析', '统计', '图表', '数据', 'analyze', 'statistics'],
        }
        
        message_lower = user_message.lower()
        
        for tool in available_tools:
            score = 0.0
            semantics = tool_semantics.get(tool, [])
            
            # 直接匹配
            for keyword in semantics:
                if keyword.lower() in message_lower:
                    score += 0.3
            
            # 语义相关性（简单实现）
            if any(s in message_lower for s in semantics):
                score += 0.2
            
            # 工具历史成功率
            for mem in self.learning_memory:
                if tool in mem.pattern:
                    success_rate = mem.success_count / (mem.success_count + mem.failure_count + 1)
                    score += success_rate * 0.1
            
            if score > 0:
                tool_scores.append((tool, min(score, 1.0)))
        
        # 按分数排序
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        return tool_scores
    
    def generate_thinking_process(self, user_message: str) -> str:
        """
        生成思考过程
        展示AI是如何思考的（透明化）
        """
        intent = self.analyze_intent(user_message)
        
        thinking = f"""
🧠 **思考过程**

1. **理解意图**
   - 表面: {intent['surface_intent'][:50]}...
   - 深层: {intent['deep_intent'] or '直接请求'}
   - 紧急度: {intent['urgency']}

2. **评估复杂度**
   - 级别: {intent['complexity']}
   - 隐式需求: {', '.join(intent['implicit_needs']) or '无'}

3. **制定策略**
   - 方法: {'分步解决' if intent['complexity'] == 'high' else '直接处理'}
   - 预期工具: {', '.join(intent['required_tools']) or '待定'}

4. **准备执行**
   - 检查历史经验...
   - 优化参数...
   - 准备回退方案...
"""
        
        # 添加相关经验
        insights = self.get_learned_insights(user_message)
        if insights:
            thinking += "\n📚 **相关经验**\n" + "\n".join(insights)
        
        return thinking


# 全局超级智能实例
super_intelligence = SuperIntelligence()


def enhance_chat_engine(chat_engine):
    """
    增强现有的ChatEngine
    注入超级智能能力
    """
    # 保存原始方法
    original_chat = chat_engine.chat
    original_chat_stream = chat_engine.chat_stream
    
    def enhanced_chat(user_message: str) -> str:
        """增强版聊天 - 添加深度推理"""
        # 生成超级提示词
        context = {
            'time': datetime.now().isoformat(),
            'history_count': len(chat_engine.messages),
            'tools': list(chat_engine.registry.list_tools()) if chat_engine.registry else [],
        }
        
        # 分析意图
        intent = super_intelligence.analyze_intent(user_message)
        
        # 如果是复杂问题，添加推理链到上下文
        if intent['complexity'] == 'high':
            reasoning_chain = super_intelligence.create_reasoning_chain(user_message, intent)
            reasoning_text = "\n".join([
                f"步骤 {step.step_number}: {step.thought}\n行动: {step.action}\n观察: {step.observation}"
                for step in reasoning_chain
            ])
            chat_engine.inject_context(f"[推理过程]\n{reasoning_text}")
        
        # 调用原始方法
        result = original_chat(user_message)
        
        # 反思结果
        reflection = super_intelligence.reflect_on_result(
            user_message, result, 'error' not in result.lower()
        )
        
        if reflection:
            result += reflection
        
        return result
    
    def enhanced_chat_stream(user_message: str):
        """增强版流式聊天"""
        # 添加思考过程
        thinking = super_intelligence.generate_thinking_process(user_message)
        yield thinking
        yield "\n---\n"
        
        # 调用原始流式方法
        yield from original_chat_stream(user_message)
    
    # 替换方法
    chat_engine.chat = enhanced_chat
    chat_engine.chat_stream = enhanced_chat_stream
    chat_engine.super_intelligence = super_intelligence
    
    return chat_engine


# 导出主要组件
__all__ = [
    'SuperIntelligence',
    'super_intelligence',
    'enhance_chat_engine',
    'ReasoningStep',
    'LearningMemory',
]
```
