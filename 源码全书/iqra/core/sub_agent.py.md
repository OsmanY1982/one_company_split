# `iqra/core/sub_agent.py`

> 路径：`iqra/core/sub_agent.py` | 行数：680


---


```python
# -*- coding: utf-8 -*-
"""
Iqra Sub-Agent 多智能体架构

Phase 1 实现：
  - SubAgentConfig: Agent 元数据（名称/System Prompt/工具白名单/模型）
  - SubAgentRegistry: Agent 注册中心
  - SubAgentRunner: 为 Sub-Agent 创建隔离执行环境并运行 AgentLoop
  - SubAgentOrchestrator: 意图路由 → 派发 → 结果合并

对标 Claude Code Agent Teams：每个 Sub-Agent 有自己的 System Prompt + 工具白名单，
iqra 独有能力：不同 Sub-Agent 可以跑不同模型。
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from .iqra_logging import logger

# ═══════════════════════════════════════════
# SubAgentConfig — Agent 元数据
# ═══════════════════════════════════════════

@dataclass
class SubAgentConfig:
    """
    定义一个 Sub-Agent 的完整配置

    Attributes:
        name: Agent 名称（唯一标识，如 "code", "search", "shell"）
        description: 一句话描述，供 LLM 路由时匹配
        system_prompt: 注入给该 Agent 的 System Prompt
        allowed_tools: 工具白名单（空列表 = 继承主 Agent 全部工具）
        model: 可选，指定该 Agent 使用的模型名（None = 继承主 Agent 模型）
              支持格式: "ollama:qwen2.5:7b" / "openai:gpt-4o" / "gemma4:hermes"
        backend_kwargs: 可选，创建独立后端时传递的额外参数
    """
    name: str
    description: str
    system_prompt: str
    allowed_tools: List[str] = field(default_factory=list)
    model: Optional[str] = None
    backend_kwargs: dict = field(default_factory=dict)


# ═══════════════════════════════════════════
# 预设 Sub-Agent 定义
# ═══════════════════════════════════════════

PRESET_AGENTS: Dict[str, SubAgentConfig] = {
    "code": SubAgentConfig(
        name="code",
        description="代码读写、重构、测试生成、项目结构分析",
        system_prompt=(
            "你是 iqra 代码助手（Code Agent）。"
            "负责代码文件的读写、编辑、重构、测试生成和项目结构分析。\n\n"
            "规则：\n"
            "1. 先用 search_files 定位相关文件，再用 read_file 阅读内容\n"
            "2. 修改代码前确保理解上下文和所有引用方\n"
            "3. 修改后用 write_file 或 edit_file 写入\n"
            "4. 输出简洁：文件路径 + 改动摘要 + 注意事项\n"
            "5. 不执行 shell 命令（除非是 git status / diff 等只读操作）"
        ),
        allowed_tools=[
            "read_file", "write_file", "edit_file",
            "search_files", "list_directory",
            "execute_shell",  # 仅 git diff/status 等只读命令
        ],
    ),
    "search": SubAgentConfig(
        name="search",
        description="代码库搜索、文档检索、RAG 知识问答、全文检索",
        system_prompt=(
            "你是 iqra 搜索助手（Search Agent）。"
            "负责在代码库和文档中查找信息，回答关于项目的问题。\n\n"
            "规则：\n"
            "1. 优先使用 search_files 精准搜索，而非遍历目录\n"
            "2. 找到相关文件后，用 read_file 确认内容\n"
            "3. 回答基于实际文件内容，不凭记忆猜测\n"
            "4. 输出格式：文件路径 → 相关片段 → 一句话总结"
        ),
        allowed_tools=[
            "search_files", "read_file", "list_directory",
        ],
    ),
    "shell": SubAgentConfig(
        name="shell",
        description="命令执行、环境管理、git 操作、包安装、脚本运行",
        system_prompt=(
            "你是 iqra Shell 助手（Shell Agent）。"
            "负责执行系统命令、管理环境、操作 git 仓库。\n\n"
            "规则：\n"
            "1. 使用 execute_shell 执行命令\n"
            "2. 危险命令（rm/format/kill）在执行前需要确认\n"
            "3. 输出命令执行结果的关键信息，截断过长输出\n"
            "4. git 操作后报告变更摘要"
        ),
        allowed_tools=["execute_shell"],
        model="",  # 默认用小模型更快，留空即继承主模型
    ),
    "review": SubAgentConfig(
        name="review",
        description="代码审查、安全检查、最佳实践检查、bug 检测",
        system_prompt=(
            "你是 iqra 代码审查助手（Review Agent）。"
            "负责审查代码质量、安全性和最佳实践。\n\n"
            "规则：\n"
            "1. 用 read_file 读取待审查文件\n"
            "2. 检查：安全问题、性能隐患、代码风格、潜在 bug、测试覆盖\n"
            "3. 给出分级建议：🔴 必须修复 / 🟡 建议改进 / 🟢 可选优化\n"
            "4. 每条建议附带具体行号和修改方案"
        ),
        allowed_tools=["read_file", "search_files"],
        model="",  # 推理强模型，留空即继承
    ),
    "file": SubAgentConfig(
        name="file",
        description="文件整理、格式转换、批量操作、文件归类、目录管理",
        system_prompt=(
            "你是 iqra 文件助手（File Agent）。"
            "负责文件的整理、转换、归类和批量操作。\n\n"
            "规则：\n"
            "1. 先用 list_directory 或 search_files 了解目录结构\n"
            "2. 文件操作使用对应专用工具（切勿用 execute_shell + 命令替代）\n"
            "3. 批量操作先试点 1-2 个文件确认，再全量执行\n"
            "4. 操作后报告：受影响文件数 + 变更摘要"
        ),
        allowed_tools=[
            "read_file", "write_file", "edit_file",
            "search_files", "list_directory",
            "delete", "execute_shell",
        ],
    ),
}


# ═══════════════════════════════════════════
# SubAgentRegistry — Agent 注册中心
# ═══════════════════════════════════════════

class SubAgentRegistry:
    """
    Sub-Agent 注册中心（单例模式）

    用法:
        registry = SubAgentRegistry()
        registry.register(SubAgentConfig(...))
        agent = registry.get("code")

    预设 5 个 Agent：code / search / shell / review / file
    """

    def __init__(self):
        self._agents: Dict[str, SubAgentConfig] = {}
        self._load_presets()

    def _load_presets(self):
        """加载预设 Agent"""
        for name, config in PRESET_AGENTS.items():
            self._agents[name] = config
        logger.debug("SubAgentRegistry: 加载 %d 个预设 Agent", len(self._agents))

    def register(self, config: SubAgentConfig) -> None:
        """注册一个 Sub-Agent"""
        if not config.name or not config.name.strip():
            raise ValueError("Agent 名称不能为空")
        self._agents[config.name] = config
        logger.info("SubAgentRegistry: 注册 Agent '%s' (工具=%d)", config.name, len(config.allowed_tools))

    def unregister(self, name: str) -> bool:
        """注销一个 Sub-Agent"""
        if name in self._agents and name not in PRESET_AGENTS:
            del self._agents[name]
            return True
        return False

    def get(self, name: str) -> Optional[SubAgentConfig]:
        """获取 Agent 配置"""
        return self._agents.get(name)

    def list_names(self) -> List[str]:
        """列出所有 Agent 名称"""
        return list(self._agents.keys())

    def list_agents(self) -> List[SubAgentConfig]:
        """列出所有 Agent 配置"""
        return list(self._agents.values())

    def get_for_llm_routing(self) -> List[dict]:
        """
        返回供 LLM 路由使用的 Agent 摘要列表

        Returns:
            [{"name": "code", "description": "...", "tools": [...]}, ...]
        """
        return [
            {
                "name": cfg.name,
                "description": cfg.description,
                "tools": cfg.allowed_tools if cfg.allowed_tools else ["<inherit all>"],
            }
            for cfg in self._agents.values()
        ]


# 全局单例
_registry: Optional[SubAgentRegistry] = None


def get_registry() -> SubAgentRegistry:
    """获取全局 SubAgentRegistry 单例"""
    global _registry
    if _registry is None:
        _registry = SubAgentRegistry()
    return _registry


# ═══════════════════════════════════════════
# SubAgentRunner — Sub-Agent 执行器
# ═══════════════════════════════════════════

class SubAgentRunner:
    """
    为 Sub-Agent 创建隔离执行环境并运行 AgentLoop

    职责：
      1. 根据 SubAgentConfig 创建受限 ChatEngine（只注册白名单工具）
      2. 可选：为 Sub-Agent 创建独立模型后端（多模型能力）
      3. 运行 AgentLoop 并返回结果
    """

    def __init__(self, main_engine, main_backend, main_tool_registry):
        """
        Args:
            main_engine: 主 ChatEngine 实例（用于复用配置）
            main_backend: 主 LLM Backend 实例
            main_tool_registry: 主 ToolRegistry 实例（含全部工具）
        """
        self._main_engine = main_engine
        self._main_backend = main_backend
        self._main_registry = main_tool_registry

    def run(
        self,
        config: SubAgentConfig,
        task: str,
        max_iterations: int = 30,
    ) -> Dict[str, Any]:
        """
        在隔离环境中执行 Sub-Agent 任务

        Args:
            config: Sub-Agent 配置
            task: 派发给该 Agent 的具体任务
            max_iterations: 最大迭代轮数

        Returns:
            {
                "success": bool,
                "summary": str,
                "agent_name": str,
                "tools_called": [...],
                "errors": [...],
                "duration_seconds": float,
            }
        """
        start_time = time.time()
        agent_name = config.name

        try:
            # 1. 创建 Sub-Agent 后端（可选多模型）
            backend = self._create_backend(config)

            # 2. 创建受限 ToolRegistry（仅白名单工具）
            restricted_registry = self._create_restricted_registry(config)

            # 3. 构建 ChatEngine
            engine = self._build_engine(config, backend, restricted_registry)

            # 4. 运行 AgentLoop
            result = self._run_agent_loop(engine, task, max_iterations)

        except Exception as e:
            logger.error("SubAgentRunner[%s]: 执行失败: %s", agent_name, e)
            return {
                "success": False,
                "summary": f"Sub-Agent '{agent_name}' 执行异常: {e}",
                "agent_name": agent_name,
                "tools_called": [],
                "errors": [str(e)],
                "duration_seconds": round(time.time() - start_time, 2),
            }

        duration = round(time.time() - start_time, 2)
        result["agent_name"] = agent_name
        result["duration_seconds"] = duration
        return result

    def _create_backend(self, config: SubAgentConfig):
        """为 Sub-Agent 创建后端（默认继承主后端）"""
        if not config.model:
            return self._main_backend

        # Sub-Agent 指定了不同模型 → 创建独立后端
        try:
            from .llm_backend import create_backend

            model = config.model
            # 解析 provider:model 格式
            if ":" in model:
                provider_str, model_name = model.split(":", 1)
            else:
                provider_str = "ollama"
                model_name = model

            extra_kwargs = dict(config.backend_kwargs)
            extra_kwargs.setdefault("model", model_name)

            backend = create_backend(provider_str, **extra_kwargs)
            logger.info(
                "SubAgentRunner[%s]: 创建独立后端 provider=%s model=%s",
                config.name, provider_str, model_name,
            )
            return backend
        except Exception as e:
            logger.warning(
                "SubAgentRunner[%s]: 创建独立后端失败(%s)，回退到主后端",
                config.name, e,
            )
            return self._main_backend

    def _create_restricted_registry(self, config: SubAgentConfig):
        """创建只包含白名单工具的限制版 ToolRegistry"""
        from .tool_registry import ToolRegistry

        if not config.allowed_tools:
            # 空白名单 = 继承全部工具
            return self._main_registry

        restricted = ToolRegistry()
        for tool_name in config.allowed_tools:
            tool = self._main_registry.get_tool(tool_name)  # ToolDefinition
            if tool is not None:
                restricted.add_tool(tool, category=tool.category or "general")
            else:
                logger.debug(
                    "SubAgentRunner[%s]: 工具 '%s' 不在主注册表中，跳过",
                    config.name, tool_name,
                )

        logger.debug(
            "SubAgentRunner[%s]: 受限工具注册表 (%d/%d)",
            config.name, restricted.count(), self._main_registry.count(),
        )
        return restricted

    def _build_engine(self, config, backend, registry):
        """构建 Sub-Agent 专用 ChatEngine"""
        from .chat_engine import ChatEngine

        engine = ChatEngine(
            backend=backend,
            registry=registry,
            system_prompt=config.system_prompt,
            auto_save=False,
            session_id=f"sub_{config.name}_{int(time.time())}",
        )
        return engine

    def _run_agent_loop(self, engine, task: str, max_iterations: int) -> dict:
        """运行 AgentLoop"""
        try:
            from .agent_loop import AgentLoop

            agent = AgentLoop(
                engine=engine,
                max_iterations=max_iterations,
                max_retries=3,
                timeout_seconds=300,
                verbose=False,
            )
            result = agent.run(task)
            return {
                "success": result.success,
                "summary": result.summary,
                "tools_called": result.tools_called,
                "errors": result.errors,
            }
        except ImportError:
            # 降级：直接用 engine.chat 单轮执行
            return self._fallback_chat(engine, task)

    def _fallback_chat(self, engine, task: str) -> dict:
        """降级方案：单轮 LLM 调用（无 AgentLoop 时）"""
        try:
            tools = engine.registry.to_openai_tools() if engine.registry.count() > 0 else None
            response = engine.backend.chat(
                engine.messages + [{"role": "user", "content": task}],
                tools,
            )

            content = response.content or ""
            tools_called = []
            if response.tool_calls:
                for tc in response.tool_calls:
                    tools_called.append(tc.name)
                    try:
                        result = engine.registry.execute(tc)
                        content += f"\n[{tc.name}]: {str(result.get('result', result.get('error', '')))[:300]}"
                    except Exception as e:
                        content += f"\n[{tc.name} 失败]: {e}"

            return {
                "success": True,
                "summary": content[:2000],
                "tools_called": tools_called,
                "errors": [],
            }
        except Exception as e:
            return {
                "success": False,
                "summary": f"执行失败: {e}",
                "tools_called": [],
                "errors": [str(e)],
            }


# ═══════════════════════════════════════════
# SubAgentOrchestrator — 意图路由 + 派发 + 合并
# ═══════════════════════════════════════════

ROUTING_SYSTEM_PROMPT = """你是 iqra 任务路由器。分析用户任务，判断应交给哪个 Sub-Agent 处理。

可用 Agent:
{agents_summary}

规则：
1. 简单明确的任务指派给单个 Agent
2. 跨域任务可指派多个 Agent（最多 3 个），按顺序执行
3. 无法判断时指派给 "default"
4. 输出纯 JSON，无额外文字

输出格式:
{{
  "agents": ["code"],
  "tasks": ["重构 src/auth.py 的登录逻辑"],
  "reason": "代码重构任务，交给 Code Agent"
}}

多 Agent 格式:
{{
  "agents": ["search", "code"],
  "tasks": [
    "在项目中搜索所有调用 login() 的地方",
    "根据搜索结果重构 login() 函数签名"
  ],
  "reason": "先搜索再改代码"
}}
"""


class SubAgentOrchestrator:
    """
    Sub-Agent 编排器 — Main Agent 的"大脑"

    流程：
      1. 意图路由：LLM 分析用户任务 → 选择 Sub-Agent(s) + 拆分 task
      2. 派发执行：按顺序调用 SubAgentRunner 执行
      3. 结果合并：聚合所有 Sub-Agent 的输出

    用法:
        orchestrator = SubAgentOrchestrator(engine, backend, tool_registry)
        result = orchestrator.execute("重构 src/auth.py 的登录逻辑")
    """

    def __init__(self, main_engine, main_backend, main_tool_registry):
        self._engine = main_engine
        self._backend = main_backend
        self._registry_obj = main_tool_registry
        self._agent_registry = get_registry()
        self._agents: list = self._agent_registry.list_agents()  # 当前可用 Agent 配置列表
        self._runner = SubAgentRunner(main_engine, main_backend, main_tool_registry)

    def route(self, user_message: str) -> Tuple[List[str], List[str], str]:
        """
        LLM 意图路由：分析任务并选择 Sub-Agent(s)

        Args:
            user_message: 用户原始消息

        Returns:
            (agent_names, tasks, reason)
            - agent_names: 选中的 Agent 名称列表 ["code"]
            - tasks: 派发给每个 Agent 的具体任务 ["重构 src/auth.py..."]
            - reason: 路由理由
        """
        agents_summary = json.dumps(
            self._agent_registry.get_for_llm_routing(),
            ensure_ascii=False,
            indent=2,
        )
        system = ROUTING_SYSTEM_PROMPT.format(agents_summary=agents_summary)

        try:
            response = self._backend.chat([
                {"role": "system", "content": system},
                {"role": "user", "content": f"路由以下任务: {user_message}"},
            ])
            content = response.content.strip() if hasattr(response, 'content') else ""

            # 提取 JSON
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.split("```")[0].strip()

            routing = json.loads(content)
            agents = routing.get("agents", ["default"])
            tasks = routing.get("tasks", [user_message])
            reason = routing.get("reason", "")

            # 确保 agents 和 tasks 长度一致
            if len(tasks) < len(agents):
                tasks.extend([user_message] * (len(agents) - len(tasks)))
            tasks = tasks[:len(agents)]

            # 验证 agent 名称有效性
            valid_agent_names = self._agent_registry.list_names()
            valid_agents = []
            valid_tasks = []
            for name, task in zip(agents, tasks):
                if name in valid_agent_names:
                    valid_agents.append(name)
                    valid_tasks.append(task)
                else:
                    logger.warning("SubAgentOrchestrator: 未知 Agent '%s'，跳过", name)

            if not valid_agents:
                return (["default"], [user_message], "所有指定 Agent 无效，回退到 default")

            logger.info(
                "SubAgentOrchestrator: 路由 → %s: %s",
                valid_agents, reason,
            )
            return (valid_agents, valid_tasks, reason)

        except Exception as e:
            logger.warning("SubAgentOrchestrator: LLM 路由失败(%s)，使用关键词匹配", e)
            # 降级：关键词匹配
            return self._keyword_route(user_message)

    def _keyword_route(self, user_message: str) -> Tuple[List[str], List[str], str]:
        """降级方案：关键词匹配路由"""
        msg = user_message.lower()
        scores = {}

        for cfg in self._agent_registry.list_agents():
            score = 0
            desc_words = cfg.description.lower().split("、")
            for word in desc_words:
                if word in msg:
                    score += 1
            if cfg.name in msg:
                score += 3
            if score > 0:
                scores[cfg.name] = score

        if not scores:
            return (["default"], [user_message], "关键词无匹配")

        best = max(scores, key=scores.get)
        return ([best], [user_message], f"关键词匹配 → {best} (score={scores[best]})")

    def execute(
        self,
        user_message: str,
        max_iterations: int = 30,
        use_routing: bool = True,
    ) -> Dict[str, Any]:
        """
        执行 Sub-Agent 编排

        Args:
            user_message: 用户原始任务
            max_iterations: 每个 Sub-Agent 的最大迭代轮数
            use_routing: 是否使用 LLM 路由（False 时直接全串行执行）

        Returns:
            {
                "success": bool,
                "summary": str,          # 聚合总结
                "agent_results": [       # 每个 Agent 的详细结果
                    {"agent_name": str, "success": bool, "summary": str, ...}
                ],
                "routing_reason": str,
                "total_duration": float,
            }
        """
        start_time = time.time()

        if use_routing:
            agent_names, tasks, reason = self.route(user_message)
        else:
            agent_names = self._agent_registry.list_names()
            tasks = [user_message] * len(agent_names)
            reason = "全 Agent 串行执行"

        if not agent_names:
            return {
                "success": False,
                "summary": "无可用 Agent",
                "agent_results": [],
                "routing_reason": reason,
                "total_duration": 0,
            }

        # 串行执行（顺序模式，Phase 1 暂不做并行）
        agent_results = []
        for name, task in zip(agent_names, tasks):
            config = self._agent_registry.get(name)
            if not config:
                agent_results.append({
                    "agent_name": name,
                    "success": False,
                    "summary": f"Agent '{name}' 未注册",
                    "tools_called": [],
                    "errors": ["未注册"],
                })
                continue

            result = self._runner.run(config, task, max_iterations=max_iterations)
            agent_results.append(result)

        # 聚合总结
        all_success = all(r.get("success", False) for r in agent_results)
        summary = self._merge_results(user_message, agent_results, reason)

        duration = round(time.time() - start_time, 2)
        logger.info(
            "SubAgentOrchestrator: 完成 — agents=%s success=%s duration=%ss",
            agent_names, all_success, duration,
        )

        return {
            "success": all_success,
            "summary": summary,
            "agent_results": agent_results,
            "routing_reason": reason,
            "total_duration": duration,
        }

    def _merge_results(
        self,
        user_message: str,
        agent_results: List[dict],
        reason: str,
    ) -> str:
        """合并多个 Agent 的输出为统一总结"""
        lines = [
            f"任务: {user_message}",
            f"路由: {reason}",
            "",
        ]

        for i, r in enumerate(agent_results, 1):
            icon = "✓" if r.get("success") else "✗"
            name = r.get("agent_name", "?")
            summary = str(r.get("summary", ""))[:300]
            tools = ", ".join(r.get("tools_called", []))
            lines.append(f"[{i}] {icon} {name}")
            if summary:
                lines.append(f"    {summary[:200]}")
            if tools:
                lines.append(f"    工具: {tools[:100]}")
            lines.append("")

        return "\n".join(lines)

```
