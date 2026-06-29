# `iqra/core/multi_model.py`

> 路径：`iqra/core/multi_model.py` | 行数：304


---


```python
# -*- coding: utf-8 -*-
"""
Iqra Multi-Model Router — 多模型智能路由引擎

支持同时运行多个模型，根据任务类型自动选择最优模型：

  任务类型          推荐模型              典型场景
  ─────────────────────────────────────────────────
  chat (聊天)       fast model           问候、翻译、格式转换
  code (编程)       deep model           写代码、debug、重构
  analysis (分析)   deep model           数据分析、报告生成
  reasoning (推理)  reasoning model      复杂多步推理、规划
  vision (视觉)     vision model         图片理解、OCR
  tools (工具调用)   deep model           需要 Function Calling

特性:
- 多个后端并行初始化，按需调用
- 关键词 + 模式匹配的轻量级任务分类
- 模型 fallback：首选模型不可用时自动降级
- 对 ChatWindow 透明——暴露与 ChatEngine 完全相同的接口
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .llm_backend import BaseLLMBackend, ProviderConfig, BackendFactory

# ═══════════════════════════════════════════
# 任务类型定义
# ═══════════════════════════════════════════

@dataclass
class TaskType:
    """任务类型及对应的模型偏好"""
    name: str                      # chat / code / analysis / vision / reasoning
    keywords: List[str]            # 触发关键词
    model_preference: str          # 首选模型角色名: fast / deep / vision / reasoning
    description: str = ""


# 内置任务类型配置
BUILTIN_TASK_TYPES: List[TaskType] = [
    TaskType(
        name="chat",
        keywords=["你好", "谢谢", "翻译", "怎么说", "格式", "天气", "时间", "日期",
                  "hello", "hi", "hey", "thanks", "translate", "format", "weather"],
        model_preference="fast",
        description="日常对话、翻译、格式转换等轻量任务",
    ),
    TaskType(
        name="code",
        keywords=["代码", "编程", "debug", "重构", "修复", "实现", "函数", "类", "模块",
                  "import", "class", "def", "函数", "bug", "错误", "报错", "优化",
                  "code", "debug", "refactor", "implement", "function", "module",
                  "npm", "pip", "git", "build", "compile", "test", "lint",
                  "编辑", "修改", "写入", "创建文件", "生成代码",
                  "算法", "排序", "爬虫", "脚本", "程序", "开发", "接口", "API",
                  "python", "java", "javascript", "typescript", "rust", "golang"],
        model_preference="deep",
        description="编程、调试、重构、代码生成等需要强逻辑能力的任务",
    ),
    TaskType(
        name="analysis",
        keywords=["分析", "统计", "报表", "总结", "对比", "趋势", "图表", "数据",
                  "analysis", "report", "summary", "statistics", "trend", "chart",
                  "SQL", "查询", "数据库", "导出"],
        model_preference="deep",
        description="数据分析、报表生成、趋势对比等深度分析任务",
    ),
    TaskType(
        name="reasoning",
        keywords=["规划", "方案", "策略", "评估", "决策", "推理", "论证", "推导",
                  "plan", "strategy", "evaluate", "decision", "reason", "logic",
                  "架构", "设计模式", "系统设计"],
        model_preference="reasoning",
        description="复杂推理、规划、决策等需要深度思考的任务",
    ),
    TaskType(
        name="tools",
        keywords=["执行", "运行", "调用工具", "文件操作", "搜索文件", "查找",
                  "execute", "run", "search", "find", "read file", "write file",
                  "shell", "terminal", "命令行"],
        model_preference="deep",
        description="需要调用工具的实操任务，要求模型支持 Function Calling",
    ),
    TaskType(
        name="vision",
        keywords=["图片", "图像", "照片", "看图", "截图", "OCR", "识别",
                  "image", "photo", "picture", "screenshot", "vision", "ocr"],
        model_preference="vision",
        description="图片理解、OCR、视觉分析任务",
    ),
]


# ═══════════════════════════════════════════
# 模型角色定义
# ═══════════════════════════════════════════

@dataclass
class ModelRole:
    """模型角色——一个角色对应一个 LLM 后端"""
    name: str                      # fast / deep / vision / reasoning
    backend: BaseLLMBackend        # 后端实例
    priority: int = 0              # 优先级（数值越大越优先作为 fallback）
    enabled: bool = True
    fallback_role: str = ""        # 不可用时的降级角色名


# ═══════════════════════════════════════════
# 多模型路由器
# ═══════════════════════════════════════════

ROUTER_SYSTEM_PROMPT = """你是 Iqra，多模型智能助手。

当前对话由 AI 路由器自动选择最适合的模型处理：
- 日常对话 → 快速模型（响应快）
- 编程/分析 → 深度模型（逻辑强）
- 复杂推理 → 推理模型（深度思考）

你的回复仍然是一人公司数字员工的风格：中文、简洁、专业、主动使用工具。"""


class MultiModelRouter:
    """
    多模型路由器 — 核心类

    用法:
        router = MultiModelRouter()

        # 注册模型角色
        router.register_role("fast", BackendFactory.create(fast_config))
        router.register_role("deep", BackendFactory.create(deep_config))
        router.register_role("reasoning", BackendFactory.create(reasoning_config))

        # 路由消息
        backend, task_type = router.route("帮我写一个排序算法")
        # → (deep_backend, "code")

        # 获取系统提示词
        prompt = router.get_system_prompt()
    """

    def __init__(self):
        self._roles: Dict[str, ModelRole] = {}
        self._task_types: List[TaskType] = list(BUILTIN_TASK_TYPES)
        self._default_role = "fast"
        self._classification_history: List[Dict] = []  # 最近分类记录

    # ── 角色管理 ──

    def register_role(self, name: str, backend: BaseLLMBackend,
                      priority: int = 0, fallback_role: str = "") -> None:
        """注册一个模型角色"""
        self._roles[name] = ModelRole(
            name=name,
            backend=backend,
            priority=priority,
            fallback_role=fallback_role,
        )

    def remove_role(self, name: str) -> bool:
        if name in self._roles:
            del self._roles[name]
            if self._default_role == name:
                self._default_role = next(iter(self._roles), "fast")
            return True
        return False

    def get_role(self, name: str) -> Optional[ModelRole]:
        return self._roles.get(name)

    def list_roles(self) -> List[str]:
        return list(self._roles.keys())

    def role_count(self) -> int:
        return len(self._roles)

    def has_multi_model(self) -> bool:
        """是否真正启用了多模型（至少 2 个不同角色）"""
        return len(self._roles) >= 2 and len({r.backend for r in self._roles.values()}) >= 2

    # ── 任务分类 ──

    def classify(self, message: str) -> str:
        """
        分析用户消息，返回任务类型名

        策略：关键词匹配（轻量、零延迟、确定性）
        """
        msg_lower = message.lower()

        # 按 task_type 的优先级匹配（先定义的优先级高）
        for tt in self._task_types:
            for kw in tt.keywords:
                if kw.lower() in msg_lower:
                    self._classification_history.append({
                        "message": message[:100],
                        "task_type": tt.name,
                        "matched_keyword": kw,
                    })
                    # 只保留最近 50 条
                    if len(self._classification_history) > 50:
                        self._classification_history.pop(0)
                    return tt.name

        # 默认：长消息倾向于分析/代码，短消息倾向于聊天
        if len(message) > 200:
            return "analysis"
        return "chat"

    # ── 路由 ──

    def route(self, message: str) -> tuple:
        """
        根据消息内容路由到最合适的后端

        Returns:
            (backend, task_type_name)
        """
        task_type = self.classify(message)

        # 查找对应的 model_preference
        preferred_role = "fast"
        for tt in self._task_types:
            if tt.name == task_type:
                preferred_role = tt.model_preference
                break

        # 获取后端（带 fallback）
        backend = self._resolve_backend(preferred_role)
        return backend, task_type

    def _resolve_backend(self, role_name: str) -> BaseLLMBackend:
        """解析角色为实际后端，不可用时 fallback"""
        role = self._roles.get(role_name)
        if role and role.enabled:
            return role.backend

        # Fallback 链
        if role and role.fallback_role:
            fallback = self._roles.get(role.fallback_role)
            if fallback and fallback.enabled:
                return fallback.backend

        # 最终 fallback：按优先级选任意可用角色
        available = sorted(
            [r for r in self._roles.values() if r.enabled],
            key=lambda r: -r.priority,
        )
        if available:
            return available[0].backend

        raise RuntimeError("没有可用的模型后端，请先注册至少一个模型角色")

    def get_backend_for_task(self, task_type_name: str) -> BaseLLMBackend:
        """根据任务类型名获取后端"""
        for tt in self._task_types:
            if tt.name == task_type_name:
                return self._resolve_backend(tt.model_preference)
        return self._resolve_backend("fast")

    # ── 系统提示词 ──

    def get_system_prompt(self) -> str:
        """生成多模型模式的系统提示词"""
        if not self.has_multi_model():
            return ""

        roles_desc = []
        for name, role in self._roles.items():
            cfg = role.backend.config
            roles_desc.append(f"  - {name}: {cfg.name} ({cfg.model})")

        task_desc = []
        for tt in self._task_types:
            task_desc.append(f"  - {tt.name} → {tt.model_preference}: {tt.description}")

        return (
            f"{ROUTER_SYSTEM_PROMPT}\n\n"
            f"当前已加载 {len(self._roles)} 个模型角色:\n"
            + "\n".join(roles_desc) + "\n\n"
            "任务路由规则:\n"
            + "\n".join(task_desc)
        )

    def get_active_model_name(self, task_type: str = "") -> str:
        """获取当前活跃的模型名称（用于 UI 显示）"""
        if not task_type:
            task_type = "chat"
        backend = self.get_backend_for_task(task_type)
        return f"{backend.config.name} ({backend.config.model})"

    # ── 统计 ──

    def get_classification_stats(self) -> Dict[str, int]:
        """获取最近分类统计"""
        stats = {}
        for entry in self._classification_history:
            t = entry["task_type"]
            stats[t] = stats.get(t, 0) + 1
        return stats

    def reset_stats(self) -> None:
        self._classification_history.clear()

```
