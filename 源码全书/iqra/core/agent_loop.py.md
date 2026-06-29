# `iqra/core/agent_loop.py`

> 路径：`iqra/core/agent_loop.py` | 行数：74


---


```python
# -*- coding: utf-8 -*-
"""
AgentLoop — 自主 Agent 执行循环 (对标 Codex / Claude Code)

在 ChatEngine 的工具调用循环之上叠加 Think → Plan → Act → Observe → Reflect
自主执行模式，支持多步推理、错误恢复、进度追踪和可中断执行。

与 ChatEngine 的关系：
  - AgentLoop 是 ChatEngine 的上层封装，复用其工具注册表和 LLM 后端
  - AgentLoop 可直接替换 ChatEngine 用于需要自主多步执行的场景
  - ChatEngine 保留用于简单单轮问答

用法:
    from iqra.core.agent_loop import AgentLoop, AgentEventType
    from iqra.core.chat_engine import ChatEngine

    engine = ChatEngine(backend=..., registry=..., ...)
    agent = AgentLoop(engine)

    # 同步执行
    result = agent.run("帮我重构 src/ 下所有 Python 文件的 import 语句")

    # 流式执行
    for event in agent.run_stream("排查为什么 API 返回 500"):
        print(event)

    # 取消执行
    agent.cancel()

特性:
  - Think-Plan-Act-Observe-Reflect 五阶段 ReAct 循环
  - 自动错误恢复（最多 3 次重试，每次尝试不同策略）
  - 进度事件流（每一步都有回调）
  - 可中断（cancel() 方法）
  - 可配置最大迭代、超时

模块结构 (mixin 拆分):
  - _agent_events.py: AgentEventType / AgentEvent / AgentResult 数据模型
  - _agent_prompts.py: AGENT_SYSTEM_PROMPT 系统提示词常量
  - _agent_fallbacks.py: TOOL_FALLBACK_MAP 工具降级映射
  - _agent_loop_base.py: AgentLoopBase(QObject) — __init__ + 公开接口 + 内部辅助
  - _agent_loop_exec_mixin.py: AgentLoopExecMixin — 工具执行引擎
  - _agent_loop_compat_mixin.py: AgentLoopCompatMixin — ChatEngine 兼容层
  - agent_loop.py (本文件): AgentLoop 组装 + 重导出
"""

from ._agent_events import AgentEventType, AgentEvent, AgentResult
from ._agent_prompts import AGENT_SYSTEM_PROMPT
from ._agent_fallbacks import TOOL_FALLBACK_MAP
from ._agent_loop_base import AgentLoopBase
from ._agent_loop_exec_mixin import AgentLoopExecMixin
from ._agent_loop_compat_mixin import AgentLoopCompatMixin


class AgentLoop(AgentLoopBase, AgentLoopExecMixin, AgentLoopCompatMixin):
    """
    自主 Agent 执行循环（组装类）

    多重继承顺序：
      AgentLoopBase(QObject)  →  信号 + 初始化 + 公开接口 + 内部辅助
      AgentLoopExecMixin       →  工具执行引擎 (_tool_loop / _execute_one_tool 等)
      AgentLoopCompatMixin     →  ChatEngine 兼容层 (chat_stream / backend / messages 等)
    """
    pass


__all__ = [
    "AgentLoop",
    "AgentEventType",
    "AgentEvent",
    "AgentResult",
    "AGENT_SYSTEM_PROMPT",
    "TOOL_FALLBACK_MAP",
]

```
