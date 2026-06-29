# `core/agent.py`

> 路径：`core/agent.py` | 行数：202


---


```python
"""
AI Agent 核心 — 命令解析、意图识别、操作调度
支持规则引擎 + 未来 LLM 扩展
"""
import re
from typing import Dict, Callable, Optional, List, Tuple


class CommandIntent:
    """解析后的命令意图"""
    def __init__(self, action: str, target: str = "", params: dict = None,
                 confidence: float = 0.0, raw: str = ""):
        self.action = action          # open / query / create / delete / navigate / system
        self.target = target          # 目标模块/对象
        self.params = params or {}
        self.confidence = confidence
        self.raw = raw

    def __repr__(self):
        return f"<Intent {self.action} -> {self.target} ({self.confidence})>"


class AgentCore:
    """AI Agent 命令解析与执行引擎"""

    # ── 模块别名 ──
    MODULE_ALIASES = {
        "业务": "business",
        "业务管理": "business",
        "业务模块": "business",
        "人员": "personnel",
        "人员管理": "personnel",
        "人事": "personnel",
        "员工": "personnel",
        "智能": "intelligence",
        "智能中心": "intelligence",
        "ai": "intelligence",
        "AI": "intelligence",
        "数据": "data",
        "数据中心": "data",
        "分析": "data",
        "系统": "system",
        "设置": "system",
        "系统设置": "system",
        "配置": "system",
        "舰桥": "intelligence",
        "主控": "intelligence",
        "首页": "intelligence",
        "总览": "intelligence",
        "主面板": "intelligence",
        "面板": "intelligence",
    }

    # ── 动作模式 ──
    ACTION_PATTERNS = [
        # (正则, 动作名, 权重)
        (r'(打开|进入|切换|跳到|前往|去|到)\s*(.+)', 'open', 0.9),
        (r'(搜索|查找|查询|查|找)\s*(.+)', 'query', 0.85),
        (r'(新建|创建|添加|增加|新增)\s*(.+)', 'create', 0.85),
        (r'(删除|移除|去掉)\s*(.+)', 'delete', 0.8),
        (r'(分析|统计|报表|报告)\s*(.*)', 'analyze', 0.8),
        (r'(帮我|请|麻烦|能不能|可以)\s*(.+)', 'help', 0.7),
        (r'(天气|时间|日期|现在几点)', 'system_query', 0.9),
        (r'(退出|关闭|返回|登出|注销)', 'exit', 0.85),
    ]

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._context = {}
        self.history: List[Tuple[str, str]] = []  # (user_msg, agent_response)

    def register_handler(self, action: str, handler: Callable):
        """注册动作处理器"""
        self._handlers[action] = handler

    def parse(self, text: str) -> Optional[CommandIntent]:
        """解析自然语言命令"""
        text = text.strip()
        if not text:
            return None

        best_match = None
        best_weight = 0

        # 遍历动作模式
        for pattern, action, base_weight in self.ACTION_PATTERNS:
            m = re.search(pattern, text)
            if m:
                raw_target = m.group(len(m.groups()))  # 最后一个捕获组
                target = self._resolve_target(raw_target.strip()) if raw_target.strip() else ""
                weight = base_weight
                # 如果能解析出确切目标则加分
                if target and target != "unknown":
                    weight += 0.08
                if weight > best_weight:
                    best_weight = weight
                    best_match = CommandIntent(
                        action=action,
                        target=target or raw_target.strip(),
                        params={'raw': raw_target.strip()},
                        confidence=weight,
                        raw=text
                    )

        # 未能匹配动作模式 → 尝试直接匹配模块名
        if best_match is None:
            target = self._resolve_target(text)
            if target and target != "unknown":
                best_match = CommandIntent(
                    action='open',
                    target=target,
                    confidence=0.75,
                    raw=text
                )
            else:
                # 作为通用帮助命令
                best_match = CommandIntent(
                    action='help',
                    target=text,
                    confidence=0.5,
                    raw=text
                )

        return best_match

    def execute(self, intent: CommandIntent) -> str:
        """执行解析后的意图"""
        if intent.action in self._handlers:
            try:
                return self._handlers[intent.action](intent)
            except Exception as e:
                return f"执行出错：{e}"

        # 默认响应
        return self._default_response(intent)

    def _resolve_target(self, raw: str) -> str:
        """将自然语言目标映射到内部模块名"""
        raw_clean = raw.strip().rstrip("。，,!！？?模块页面页签窗口界面")
        # 精确匹配
        if raw_clean in self.MODULE_ALIASES:
            return self.MODULE_ALIASES[raw_clean]
        # 模糊匹配：检查 raw 是否包含某个别名
        for alias, module in self.MODULE_ALIASES.items():
            if alias in raw_clean:
                return module
        return "unknown"

    def _default_response(self, intent: CommandIntent) -> str:
        if intent.action == 'help':
            return (
                f"收到「{intent.raw}」。我能帮你：\n"
                "• 打开/切换模块：业务管理、人员管理、智能中心、数据中心、系统设置\n"
                "• 搜索/查询信息\n"
                "• 创建、删除内容\n"
                "• 分析数据、生成报表"
            )
        return f"收到「{intent.raw}」，但我暂时不知道如何执行。"

    # ── 预置处理器 ──

    def handler_open(self, intent: CommandIntent) -> str:
        module_names = {
            "business": "业务管理",
            "personnel": "人员管理",
            "intelligence": "智能中心",
            "data": "数据中心",
            "system": "系统设置",
        }
        name = module_names.get(intent.target, intent.target)
        return f"正在打开「{name}」模块..."

    def handler_query(self, intent: CommandIntent) -> str:
        return f"正在搜索「{intent.target}」相关信息..."

    def handler_create(self, intent: CommandIntent) -> str:
        return f"正在创建「{intent.target}」..."

    def handler_delete(self, intent: CommandIntent) -> str:
        return f"请确认：确定要删除「{intent.target}」吗？"

    def handler_analyze(self, intent: CommandIntent) -> str:
        return f"正在对「{intent.target or '全局数据'}」进行分析..."

    def handler_system_query(self, intent: CommandIntent) -> str:
        from datetime import datetime
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        return f"现在是 {now}"

    def handler_exit(self, intent: CommandIntent) -> str:
        return "exit"


# 全局单例
agent = AgentCore()
agent.register_handler('open', agent.handler_open)
agent.register_handler('query', agent.handler_query)
agent.register_handler('create', agent.handler_create)
agent.register_handler('delete', agent.handler_delete)
agent.register_handler('analyze', agent.handler_analyze)
agent.register_handler('system_query', agent.handler_system_query)
agent.register_handler('exit', agent.handler_exit)
```
