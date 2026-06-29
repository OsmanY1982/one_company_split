# `iqra/core/core_engine.py`

> 路径：`iqra/core/core_engine.py` | 行数：289


---


```python
"""
Iqra Core Engine v2.0 - 智能核心引擎
支持 Function Calling、多轮工具调用、任务规划、代码执行
让 Iqra 具备与 Hermes 相当的智能水平
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# 导入 LLM 后端
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from iqra.core.llm_backend import (
    ProviderConfig, OpenAICompatibleBackend, LLMResponse, ToolDefinition
)

# ── 子模块导入 ──
from ._config_helpers import _get_default_model, _get_active_provider_config
from ._tool_registry import ToolRegistry
from ._basic_tools import _register_basic_tools
from ._claude_tools import _register_claude_tools


# ── 内置工具初始化（委派到子模块）──
def init_builtin_tools(registry: ToolRegistry):
    """注册内置工具"""
    _register_basic_tools(registry)
    _register_claude_tools(registry)


# ═══════════════════════════════════════════
# 智能核心引擎
# ═══════════════════════════════════════════

@dataclass
class ChatMessage:
    """对话消息"""
    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class IqraCoreEngine:
    """
    Iqra 智能核心引擎 v2.0
    支持 Function Calling、多轮工具调用、任务规划
    """
    
    def __init__(self, provider_config: ProviderConfig = None):
        self.registry = ToolRegistry()
        init_builtin_tools(self.registry)
        
        # 默认使用 Ollama 本地模型（从配置文件读取模型名）
        if provider_config is None:
            provider_config = ProviderConfig(
                name="Ollama",
                provider_type="openai_compatible",
                base_url="http://localhost:11434/v1",
                model=_get_default_model(),
                temperature=0.7,
                max_tokens=262144
            )
        self.provider_config = provider_config
        self.backend = OpenAICompatibleBackend(provider_config)
        
        # 对话历史
        self.messages: List[ChatMessage] = []
        
        # 系统提示词
        self.system_prompt = """你是 Iqra，一个运行在用户本地电脑上的 AI 编程助手，定位对标 Claude Code。

核心原则：
- 行动优先，能直接用工具解决就不要追问
- 多轮工具调用直到完成任务，不提前放弃
- 回答简洁专业，中文优先，技术术语保留英文

工具选择铁律（违反将导致任务失败）：
- 读文件 → 只用 read_file，严禁 shell_execute + cat/more/osascript/head/tail
- 搜文件 → 只用 search_files，严禁 shell_execute + find/grep/mdfind/rg
- 写文件 → 只用 write_file/edit_file，严禁 shell_execute + echo/printf/tee 重定向
- 列目录 → 只用 list_directory，严禁 shell_execute + ls/dir/tree
- 独立操作（同时读多个文件/搜多个关键词）必须并行调用

可用工具：
1.  Shell 命令(shell_execute)：执行 git/npm/pip/build/test/lint/docker 等命令（严禁用于文件读写搜索列目录）
2.  文件操作：read_file 读取、write_file 写入、edit_file 精确替换、list_directory 列目录
3.  内容搜索：search_files 按名称/内容搜索文件和代码
4.  代码执行：execute_code 运行 Python 代码，用于数据分析/文件处理
5.  数据库查询：query_database 查询 products/orders/customers/finance 等业务数据
6.  联网搜索：web_search 获取实时信息
7.  日程与客户管理：add_schedule/list_schedules/add_customer/list_customers 等

编程场景最佳实践：
- 修改代码前先用 search_files 找到相关代码位置
- 多文件编辑时用 edit_file 逐个精确替换
- 构建/测试/格式化用 shell_execute
- 代码执行错误时读取日志并修复

当用户请求需要工具才能完成的任务时，请调用相应的工具。进行多轮工具调用直到任务完成。
请用中文回答，保持友好和专业。"""
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.messages.append(ChatMessage(role=role, content=content))
    
    def clear_history(self):
        """清空对话历史"""
        self.messages = []
    
    def _trim_messages(self, messages: List[dict], max_messages: int = 60) -> List[dict]:
        """智能裁剪消息历史，防止超出 token 限制
        
        保留策略：
        - 系统消息（role=system）永久保留
        - 最近 30 条消息必留
        - 中间保留错误消息和工具调用结果消息
        """
        if len(messages) <= max_messages:
            return messages
        
        # 分离系统消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]
        recent = other_msgs[-30:] if len(other_msgs) > 30 else other_msgs
        
        # 中间部分保留关键消息（错误、工具调用结果）
        middle = other_msgs[:-30] if len(other_msgs) > 30 else []
        kept_middle = [
            m for m in middle
            if (m["role"] == "tool" and '"error"' in str(m.get("content", "")))
            or (m["role"] == "assistant" and m.get("tool_calls"))
        ][-10:]  # 最多保留 10 条中间关键消息
        
        trimmed = system_msgs + kept_middle + recent
        return trimmed[:max_messages]
    
    def chat(self, user_input: str, max_tool_iterations: int = 5) -> str:
        """
        与用户对话，支持多轮工具调用
        
        Args:
            user_input: 用户输入
            max_tool_iterations: 最大工具调用轮数
        
        Returns:
            AI 回复
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 添加用户消息
        self.add_message("user", user_input)
        
        # 构建消息历史
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.messages:
            if msg.role == "tool":
                messages.append({
                    "role": "tool",
                    "content": json.dumps(msg.content, ensure_ascii=False),
                    "tool_call_id": msg.tool_call_id
                })
            else:
                msg_dict = {"role": msg.role, "content": msg.content}
                if msg.tool_calls:
                    msg_dict["tool_calls"] = msg.tool_calls
                messages.append(msg_dict)
        
        # 获取工具定义
        tools = self.registry.list_tools()
        
        # 多轮工具调用循环
        for iteration in range(max_tool_iterations):
            # 裁剪消息防止超 token
            if len(messages) > 60:
                messages = self._trim_messages(messages)
            
            # 调用 LLM
            response = self.backend.chat(messages, tools=tools)
            
            # 检查是否需要调用工具
            if response.tool_calls:
                tool_calls = response.tool_calls
                
                # 单工具调用：串行执行（保留重试语义）
                if len(tool_calls) == 1:
                    tc = tool_calls[0]
                    result = self.registry.execute(tc.name, tc.arguments)
                    tc_results = [(tc, result)]
                # 多工具调用：并行执行无依赖的工具
                else:
                    tc_results = []
                    with ThreadPoolExecutor(max_workers=min(len(tool_calls), 8)) as executor:
                        future_to_tc = {
                            executor.submit(self.registry.execute, tc.name, tc.arguments): tc
                            for tc in tool_calls
                        }
                        for future in as_completed(future_to_tc):
                            tc = future_to_tc[future]
                            try:
                                result = future.result()
                            except Exception as e:
                                result = {"error": str(e)}
                            tc_results.append((tc, result))
                    # 恢复原始顺序
                    tc_order = {id(tc): i for i, tc in enumerate(tool_calls)}
                    tc_results.sort(key=lambda x: tc_order[id(x[0])])
                
                # 构建 assistant 消息（含所有工具调用）
                assistant_tool_calls = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    }
                    for tc in tool_calls
                ]
                
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": assistant_tool_calls
                })
                
                # 保存到本地历史
                self.messages.append(ChatMessage(
                    role="assistant",
                    content="",
                    tool_calls=assistant_tool_calls
                ))
                
                # 添加工具结果（按原始顺序）
                for tc, result in tc_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    self.messages.append(ChatMessage(
                        role="tool",
                        content=result,
                        tool_call_id=tc.id
                    ))
                
                # 继续下一轮 LLM 调用
                continue
            else:
                # 没有工具调用，返回文本回复
                assistant_message = response.content or ""
                self.add_message("assistant", assistant_message)
                return assistant_message
        
        # 达到最大迭代次数，强制返回当前回复
        if messages[-1]["role"] == "tool":
            # 再调用一次 LLM 获取最终回复
            response = self.backend.chat(messages, tools=tools)
            assistant_message = response.content or "任务处理完成。"
        else:
            assistant_message = response.content or "我需要调用工具来完成这个任务。"
        
        self.add_message("assistant", assistant_message)
        return assistant_message
    
    def get_status(self) -> dict:
        """获取引擎状态"""
        return {
            "model": self.provider_config.model,
            "provider": self.provider_config.name,
            "tools_available": len(self.registry._tools),
            "message_count": len(self.messages),
            "tools": list(self.registry._tools.keys())
        }


# ═══════════════════════════════════════════
# 重导出（从子模块）
# ═══════════════════════════════════════════

from ._quick_funcs import create_engine, quick_chat

# ── 兼容别名（调用方期望 CoreEngine）──
CoreEngine = IqraCoreEngine

```
