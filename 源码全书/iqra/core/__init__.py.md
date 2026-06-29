# `iqra/core/__init__.py`

> 路径：`iqra/core/__init__.py` | 行数：568


---


```python
"""
Iqra 智能核心 v2.0
集成所有增强模块的主入口
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

# 添加核心模块路径
sys.path.insert(0, str(Path(__file__).parent))

# 弹性导入 - 每个模块独立 try/except
def _safe_import(module_name, names, alias_map=None):
    """安全导入，导入失败时返回 None"""
    result = {}
    for name in names:
        result[name] = None
    try:
        module = __import__(module_name, fromlist=names)
        for name in names:
            if hasattr(module, name):
                result[name] = getattr(module, name)
    except (ImportError, AttributeError, Exception):
        pass
    
    # 应用别名映射
    if alias_map:
        for src, dst in alias_map.items():
            if result.get(src):
                result[dst] = result[src]
    
    return result

# 核心引擎
_core = _safe_import('core_engine', ['ToolRegistry', 'IqraCoreEngine', 'CoreEngine'],
                     {'IqraCoreEngine': 'CoreEngine'})
ToolRegistry = _core.get('ToolRegistry')
CoreEngine = _core.get('CoreEngine') or _core.get('IqraCoreEngine')

# 技能路由
_skill = _safe_import('skill_router', ['SmartSkillRouter', 'SkillMatcher'],
                      {'SmartSkillRouter': 'SkillRouter', 'SkillMatcher': 'SkillMatch'})
SkillRouter = _skill.get('SkillRouter') or _skill.get('SmartSkillRouter')
SkillMatch = _skill.get('SkillMatch') or _skill.get('SkillMatcher')

# 记忆系统 - 尝试多个可能的文件名
_memory_classes = None
for _mem_module in ['enhanced_memory', 'smart_memory', 'memory_system', 'memory_store']:
    _m = _safe_import(_mem_module, ['EnhancedMemory', 'MemoryQuery', 'SmartMemory'])
    if _m.get('EnhancedMemory') or _m.get('MemoryQuery') or _m.get('SmartMemory'):
        _memory_classes = _m
        break
EnhancedMemory = (_memory_classes or {}).get('EnhancedMemory') or (_memory_classes or {}).get('SmartMemory')
MemoryQuery = (_memory_classes or {}).get('MemoryQuery')

# 任务规划
_task = _safe_import('task_planner', ['TaskPlanner', 'Task', 'TaskStatus'])
TaskPlanner = _task.get('TaskPlanner')
Task = _task.get('Task')
TaskStatus = _task.get('TaskStatus')

# 代码执行
_code = _safe_import('code_executor', ['CodeExecutor', 'ExecutionResult'])
CodeExecutor = _code.get('CodeExecutor')
ExecutionResult = _code.get('ExecutionResult')
execute_code = None  # 模块级函数

# 网络搜索
_web = _safe_import('web_search', ['WebSearchManager', 'DuckDuckGoSearch', 'SearchResponse'])
WebSearchManager = _web.get('WebSearchManager')
DuckDuckGoSearch = _web.get('DuckDuckGoSearch')
SearchResponse = _web.get('SearchResponse')
web_search = None  # 模块级函数

# 协作客户端
_collab = _safe_import('collaboration_client', ['IqraHermesClient', 'CollaborationMessage', 'CollaborationResponse'])
IqraHermesClient = _collab.get('IqraHermesClient')
CollaborationMessage = _collab.get('CollaborationMessage')
CollaborationResponse = _collab.get('CollaborationResponse')

# 云端同步
_cloud = _safe_import('cloud_sync', ['CloudSyncService', 'push_all', 'pull_all', 'smart_sync'])
CloudSyncService = _cloud.get('CloudSyncService')
PushAll = _cloud.get('push_all')
PullAll = _cloud.get('pull_all')
SmartSync = _cloud.get('smart_sync')

# Supabase 客户端
_supabase = _safe_import('supabase_client', ['SupabaseClient', 'get_client', 'get_service_client'])
SupabaseClient = _supabase.get('SupabaseClient')
GetClient = _supabase.get('get_client')
GetServiceClient = _supabase.get('get_service_client')


@dataclass
class IqraConfig:
    """Iqra 配置"""
    # 内存配置
    memory_enabled: bool = True
    memory_storage_path: str = "iqra/data/memory"
    
    # 任务规划配置
    planning_enabled: bool = True
    max_subtasks: int = 10
    
    # 代码执行配置
    code_execution_enabled: bool = True
    code_timeout: int = 30
    
    # 网络搜索配置
    web_search_enabled: bool = True
    
    # 协作配置
    collaboration_enabled: bool = True
    hermes_endpoint: str = "http://localhost:8080"
    
    # 技能配置
    skills_path: str = "iqra/skills"


class IqraCore:
    """
    Iqra 智能核心 v2.0
    集成所有增强功能的统一接口
    """
    
    def __init__(self, config: IqraConfig = None):
        """
        初始化 Iqra 核心
        
        Args:
            config: 配置对象
        """
        self.config = config or IqraConfig()
        self.version = "2.0"
        
        # 初始化各模块
        self._init_modules()
        
        # 注册内置工具
        self._register_builtin_tools()
        
        print(f"✓ Iqra Core v{self.version} 初始化完成")
    
    def _init_modules(self):
        """初始化各模块"""
        # 核心引擎
        self.core_engine = CoreEngine()
        
        # 技能路由
        self.skill_router = SkillRouter()
        self.skill_router.load_skills_from_directory(
            f"{self.config.skills_path}/builtin"
        )
        
        # 增强记忆 — 统一使用 SmartMemoryStore 门面
        if self.config.memory_enabled:
            from .smart_memory_adapter import SmartMemoryStore
            self.memory = SmartMemoryStore(
                base_dir=self.config.memory_storage_path
            )
        else:
            self.memory = None
        
        # 任务规划
        if self.config.planning_enabled:
            self.task_planner = TaskPlanner(
                max_subtasks=self.config.max_subtasks
            )
        else:
            self.task_planner = None
        
        # 代码执行
        if self.config.code_execution_enabled:
            self.code_executor = CodeExecutor(
                default_timeout=self.config.code_timeout
            )
        else:
            self.code_executor = None
        
        # 网络搜索
        if self.config.web_search_enabled:
            self.web_search = WebSearchManager()
            from web_search import DuckDuckGoSearch
            self.web_search.register_engine(DuckDuckGoSearch(), set_default=True)
        else:
            self.web_search = None
        
        # 协作客户端
        if self.config.collaboration_enabled:
            self.collaboration = IqraHermesClient(
                hermes_endpoint=self.config.hermes_endpoint,
                use_local_socket=False
            )
        else:
            self.collaboration = None
    
    def _register_builtin_tools(self):
        """注册内置工具到核心引擎"""
        # 代码执行工具
        if self.code_executor:
            self.core_engine.register_tool(
                name="execute_python",
                description="执行 Python 代码",
                parameters={
                    "code": {"type": "string", "description": "Python 代码"},
                    "timeout": {"type": "integer", "description": "超时时间（秒）", "default": 30}
                },
                function=self._tool_execute_python
            )
        
        # 网络搜索工具
        if self.web_search:
            self.core_engine.register_tool(
                name="web_search",
                description="搜索网页获取信息",
                parameters={
                    "query": {"type": "string", "description": "搜索查询"},
                    "num_results": {"type": "integer", "description": "结果数量", "default": 5}
                },
                function=self._tool_web_search
            )
        
        # 技能匹配工具
        self.core_engine.register_tool(
            name="match_skill",
            description="根据问题匹配最合适的技能",
            parameters={
                "query": {"type": "string", "description": "用户问题"},
                "top_k": {"type": "integer", "description": "返回数量", "default": 3}
            },
            function=self._tool_match_skill
        )
        
        # 记忆查询工具
        if self.memory:
            self.core_engine.register_tool(
                name="query_memory",
                description="查询历史对话和记忆",
                parameters={
                    "query": {"type": "string", "description": "查询内容"},
                    "memory_type": {"type": "string", "description": "记忆类型", "default": "all"}
                },
                function=self._tool_query_memory
            )
        
        # 任务规划工具
        if self.task_planner:
            self.core_engine.register_tool(
                name="create_plan",
                description="创建任务执行计划",
                parameters={
                    "goal": {"type": "string", "description": "任务目标"},
                    "context": {"type": "string", "description": "任务上下文", "default": ""}
                },
                function=self._tool_create_plan
            )
        
        # 协作工具
        if self.collaboration:
            self.core_engine.register_tool(
                name="collaborate_with_hermes",
                description="与 Hermes 协作完成复杂任务",
                parameters={
                    "task_type": {"type": "string", "description": "任务类型"},
                    "description": {"type": "string", "description": "任务描述"},
                    "parameters": {"type": "object", "description": "任务参数", "default": {}}
                },
                function=self._tool_collaborate
            )
    
    # ═════════════════════════════════════════════════════════
    # 工具函数实现
    # ═════════════════════════════════════════════════════════
    
    def _tool_execute_python(self, code: str, timeout: int = 30) -> Dict:
        """执行 Python 代码工具"""
        if not self.code_executor:
            return {"error": "代码执行器未启用"}
        
        result = self.code_executor.execute(code, timeout=timeout)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    def _tool_web_search(self, query: str, num_results: int = 5) -> Dict:
        """网络搜索工具"""
        if not self.web_search:
            return {"error": "网络搜索未启用"}
        
        response = self.web_search.search(query, num_results=num_results)
        return {
            "query": response.query,
            "results_count": len(response.results),
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet
                }
                for r in response.results
            ]
        }
    
    def _tool_match_skill(self, query: str, top_k: int = 3) -> Dict:
        """技能匹配工具"""
        matches = self.skill_router.match(query, top_k=top_k)
        return {
            "matches": [
                {
                    "skill": m.skill.name,
                    "confidence": m.confidence,
                    "reason": m.reason
                }
                for m in matches
            ]
        }
    
    def _tool_query_memory(self, query: str, memory_type: str = "all") -> Dict:
        """记忆查询工具"""
        if not self.memory:
            return {"error": "记忆系统未启用"}
        
        results = self.memory.query(MemoryQuery(
            query=query,
            memory_type=memory_type
        ))
        return {
            "results_count": len(results),
            "results": [
                {
                    "type": r.type,
                    "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    "timestamp": r.timestamp,
                    "relevance": r.relevance
                }
                for r in results
            ]
        }
    
    def _tool_create_plan(self, goal: str, context: str = "") -> Dict:
        """创建任务计划工具"""
        if not self.task_planner:
            return {"error": "任务规划器未启用"}
        
        plan = self.task_planner.create_plan(goal, context)
        return {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "subtasks_count": len(plan.subtasks),
            "estimated_duration": plan.estimated_duration,
            "subtasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "status": t.status.value,
                    "estimated_duration": t.estimated_duration
                }
                for t in plan.subtasks
            ]
        }
    
    def _tool_collaborate(self, task_type: str, description: str, 
                         parameters: Dict = None) -> Dict:
        """与 Hermes 协作工具"""
        if not self.collaboration:
            return {"error": "协作功能未启用"}
        
        result = self.collaboration.send_task(
            task_type=task_type,
            description=description,
            parameters=parameters or {}
        )
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    # ═════════════════════════════════════════════════════════
    # 主接口
    # ═════════════════════════════════════════════════════════
    
    def process(self, user_input: str, 
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            处理结果
        """
        context = context or {}
        start_time = time.time()
        
        # 1. 记录对话
        if self.memory:
            self.memory.add_dialogue("user", user_input)
        
        # 2. 技能匹配
        skill_matches = self.skill_router.match(user_input, top_k=3)
        best_match = skill_matches[0] if skill_matches else None
        
        # 3. 判断是否需要任务规划
        if self.task_planner and self.task_planner.should_plan(user_input):
            plan = self.task_planner.create_plan(user_input)
            plan_result = self.task_planner.execute_plan(plan.plan_id)
            
            response = {
                "type": "plan_execution",
                "plan": plan.to_dict(),
                "result": plan_result,
                "execution_time": time.time() - start_time
            }
        
        # 4. 判断是否需要工具调用
        elif self.core_engine.should_use_tools(user_input):
            tool_result = self.core_engine.process_with_tools(user_input)
            
            response = {
                "type": "tool_execution",
                "tools_used": tool_result.get("tools_used", []),
                "result": tool_result.get("result", ""),
                "execution_time": time.time() - start_time
            }
        
        # 5. 普通对话
        else:
            response = {
                "type": "conversation",
                "matched_skill": best_match.skill.name if best_match else None,
                "confidence": best_match.confidence if best_match else 0,
                "execution_time": time.time() - start_time
            }
        
        # 6. 记录助手回复
        if self.memory:
            self.memory.add_dialogue("assistant", json.dumps(response, ensure_ascii=False))
        
        return response
    
    def chat(self, message: str, session_id: str = None) -> str:
        """
        对话接口（简化版）
        
        Args:
            message: 用户消息
            session_id: 会话 ID
            
        Returns:
            回复文本
        """
        result = self.process(message)
        
        # 格式化回复
        if result["type"] == "tool_execution":
            return f"[使用工具] {result['result']}"
        elif result["type"] == "plan_execution":
            return f"[任务规划] 已执行 {len(result['plan']['subtasks'])} 个子任务"
        else:
            return f"[对话] 已匹配技能: {result.get('matched_skill', '无')}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "version": self.version,
            "modules": {
                "core_engine": True,
                "skill_router": {
                    "loaded_skills": len(self.skill_router.skills)
                },
                "memory": self.memory.get_stats() if self.memory else None,
                "task_planner": self.task_planner is not None,
                "code_executor": self.code_executor.get_stats() if self.code_executor else None,
                "web_search": self.web_search.get_stats() if self.web_search else None,
                "collaboration": self.collaboration.get_status() if self.collaboration else None
            }
        }
        return status
    
    def close(self):
        """关闭系统"""
        if self.memory:
            self.memory.close()
        if self.collaboration:
            self.collaboration.close()


# ═══════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════

_core_instance = None

def get_core() -> IqraCore:
    """获取全局核心实例"""
    global _core_instance
    if _core_instance is None:
        _core_instance = IqraCore()
    return _core_instance


def chat(message: str) -> str:
    """便捷对话函数"""
    return get_core().chat(message)


def process(message: str) -> Dict[str, Any]:
    """便捷处理函数"""
    return get_core().process(message)


# ═══════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Iqra 智能核心 v2.0 测试")
    print("=" * 60)
    
    # 初始化核心
    core = IqraCore()
    
    # 显示状态
    print("\n系统状态:")
    status = core.get_status()
    print(f"版本: {status['version']}")
    print(f"已加载技能: {status['modules']['skill_router']['loaded_skills']}")
    print(f"记忆系统: {'启用' if status['modules']['memory'] else '禁用'}")
    print(f"任务规划: {'启用' if status['modules']['task_planner'] else '禁用'}")
    print(f"代码执行: {'启用' if status['modules']['code_executor'] else '禁用'}")
    print(f"网络搜索: {'启用' if status['modules']['web_search'] else '禁用'}")
    print(f"协作功能: {'启用' if status['modules']['collaboration'] else '禁用'}")
    
    # 测试对话
    print("\n" + "=" * 60)
    print("对话测试")
    print("=" * 60)
    
    test_messages = [
        "帮我计算一下 123 乘以 456",
        "搜索一下 Python 数据分析教程",
        "规划一下本周的工作任务"
    ]
    
    for msg in test_messages:
        print(f"\n用户: {msg}")
        result = core.process(msg)
        print(f"类型: {result['type']}")
        print(f"耗时: {result['execution_time']:.3f}s")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    core.close()

```
