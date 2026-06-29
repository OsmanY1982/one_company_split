# `iqra/core/agent_delegate.py`

> 路径：`iqra/core/agent_delegate.py` | 行数：665


---


```python
# -*- coding: utf-8 -*-
"""
Iqra Agent Delegate — LLM 驱动的智能子代理委派系统

v2.0 升级要点:
  - LLM 驱动的任务分解（替代关键词匹配）
  - 并行子代理执行（ThreadPoolExecutor）
  - 上下文隔离（每个子代理独立上下文切片）
  - 结果聚合与结构化输出

用法:
    from iqra.core.agent_delegate import AgentDelegate, SubAgentTask
    from iqra.core.llm_backend import create_backend

    backend = create_backend(...)
    delegate = AgentDelegate(backend=backend)

    # 注册处理器
    delegate.register_handler("file_ops", handle_files)
    delegate.register_handler("search", handle_search)

    # 委托复杂任务（LLM 自动分解）
    result = delegate.delegate("把 src/ 下所有 .py 文件的 import 改成绝对路径")

    # 查看状态
    for task_id, task in delegate.tasks.items():
        print(f"{task_id}: {task.status}")
"""

import json
import time
import copy
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from .iqra_logging import logger


# ═══════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════

@dataclass
class SubAgentTask:
    """子代理任务"""
    goal: str
    context: str = ""
    handler: str = ""                 # 指定处理器名（可选，LLM 自动匹配）
    toolsets: List[str] = field(default_factory=list)
    depends_on: List[int] = field(default_factory=list)  # 依赖的任务索引
    priority: int = 0                 # 优先级（数字越大越优先，暂未启用）
    result: Optional[Dict] = None
    status: str = "pending"           # pending → running → completed / failed / cancelled
    started_at: float = 0.0
    finished_at: float = 0.0
    retries: int = 0
    error: str = ""


# ═══════════════════════════════════════════
# 任务分解器（LLM 驱动）
# ═══════════════════════════════════════════

DECOMPOSE_SYSTEM_PROMPT = """你是一个任务分解器。将用户目标拆解为独立的子任务。

规则:
1. 每个子任务必须是原子操作，可独立执行
2. 有依赖关系的任务在 depends_on 中标注前置任务索引（0-based）
3. 无依赖的任务可以并行执行
4. handler 从可用处理器列表中选择最匹配的，无法匹配时填 "default"
5. 输出纯 JSON 数组，无额外文字

可用处理器: {handlers}

输出格式:
[
  {{
    "goal": "子任务描述",
    "handler": "处理器名",
    "depends_on": [0],
    "context": "需要的额外上下文"
  }}
]
"""

RESULT_AGGREGATE_SYSTEM_PROMPT = """你是一个结果聚合器。将多个子任务的结果合并为统一回复。

规则:
1. 成功和失败的结果都要包含
2. 按执行顺序组织信息
3. 输出简洁的结构化文本

原始目标: {goal}

子任务结果:
{results}
"""


class LLMDecomposer:
    """使用 LLM 进行任务分解"""

    def __init__(self, backend):
        """
        Args:
            backend: BaseLLMBackend 实例（用于 chat 调用）
        """
        self._backend = backend

    def decompose(self, goal: str, handler_names: List[str], context: str = "") -> List[dict]:
        """
        使用 LLM 分解任务

        Args:
            goal: 用户目标
            handler_names: 可用处理器名称列表
            context: 额外上下文

        Returns:
            子任务列表 [{goal, handler, depends_on, context}, ...]
        """
        handlers_str = ", ".join(handler_names) if handler_names else "default"
        system = DECOMPOSE_SYSTEM_PROMPT.format(handlers=handlers_str)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"目标: {goal}\n\n{context}" if context else goal},
        ]

        try:
            response = self._backend.chat(messages)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # 提取 JSON 块
            if "```" in content:
                # 去掉 markdown 代码块标记
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.split("```")[0].strip()

            tasks = json.loads(content)
            if not isinstance(tasks, list):
                return [{"goal": goal, "handler": "default", "depends_on": [], "context": context}]

            # 校验并规范化
            validated = []
            for t in tasks:
                validated.append({
                    "goal": str(t.get("goal", "")),
                    "handler": str(t.get("handler", "default")),
                    "depends_on": list(t.get("depends_on", [])) if isinstance(t.get("depends_on"), list) else [],
                    "context": str(t.get("context", context)),
                })
            return validated

        except (json.JSONDecodeError, IndexError, Exception) as e:
            logger.warning("LLM 任务分解失败，回退到单任务模式: %s", e)
            return [{"goal": goal, "handler": "default", "depends_on": [], "context": context}]

    def aggregate(self, goal: str, subtask_results: List[Dict]) -> str:
        """
        使用 LLM 聚合子任务结果

        Args:
            goal: 原始目标
            subtask_results: [{goal, handler, status, result, error}, ...]

        Returns:
            聚合后的文本总结
        """
        results_text = "\n---\n".join(
            f"[{i+1}] {r.get('goal', '?')}\n"
            f"处理器: {r.get('handler', '?')}\n"
            f"状态: {r.get('status', '?')}\n"
            f"结果: {r.get('result', r.get('error', '无'))}"
            for i, r in enumerate(subtask_results)
        )

        system = RESULT_AGGREGATE_SYSTEM_PROMPT.format(goal=goal, results=results_text)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "请聚合以上结果。"},
        ]

        try:
            response = self._backend.chat(messages)
            return response.content.strip() if hasattr(response, 'content') else str(response).strip()
        except Exception as e:
            logger.warning("LLM 结果聚合失败: %s", e)
            # 降级：简单拼接
            parts = [f"{r.get('goal', '')}: {r.get('result', r.get('error', '?'))}"
                     for r in subtask_results]
            return "\n".join(parts)


# ═══════════════════════════════════════════
# AgentDelegate 主类
# ═══════════════════════════════════════════

class AgentDelegate:
    """
    智能子代理委派管理器

    特性:
      - LLM 驱动的任务分解
      - 并行子代理执行（ThreadPoolExecutor）
      - 上下文隔离
      - 结果聚合
    """

    def __init__(self, backend=None, max_workers: int = 8):
        """
        Args:
            backend: BaseLLMBackend 实例（用于 LLM 驱动的分解和聚合）。
                     不传则仅使用关键词匹配模式。
            max_workers: 并行执行的最大线程数
        """
        self._backend = backend
        self._max_workers = max_workers
        self._decomposer = LLMDecomposer(backend) if backend else None
        self.tasks: Dict[str, SubAgentTask] = {}
        self.handlers: Dict[str, Callable] = {}
        self._task_counter = 0

    # ── 处理器注册 ──

    def register_handler(self, name: str, func: Callable) -> None:
        """
        注册任务处理器

        Args:
            name: 处理器名称（LLM 分解时匹配用）
            func: 处理器函数，签名为 func(context: str, toolsets: List[str]) -> dict
        """
        self.handlers[name] = func
        logger.debug("AgentDelegate: 注册处理器 '%s'", name)

    def unregister_handler(self, name: str) -> bool:
        """注销处理器"""
        if name in self.handlers:
            del self.handlers[name]
            return True
        return False

    @property
    def handler_names(self) -> List[str]:
        return list(self.handlers.keys())

    # ── 任务委派 ──

    def delegate(
        self,
        goal: str,
        context: str = "",
        toolsets: List[str] = None,
        use_llm: bool = True,
    ) -> Dict:
        """
        委托任务（自动分解并执行）

        这是主入口方法。根据 goal 自动分解为子任务并在隔离上下文中执行。

        Args:
            goal: 任务目标（自然语言描述）
            context: 全局上下文（注入到所有子任务）
            toolsets: 启用的工具集
            use_llm: 是否使用 LLM 分解（关闭则回退到单任务模式）

        Returns:
            {
                "success": bool,
                "summary": str,          # 聚合总结
                "tasks": [               # 子任务详情
                    {"task_id": str, "goal": str, "handler": str,
                     "status": str, "result": dict, "error": str},
                    ...
                ],
                "execution_time": float  # 总耗时（秒）
            }
        """
        start_time = time.time()
        results = []

        # 步骤1: 任务分解
        if use_llm and self._decomposer and len(self.handler_names) > 0:
            subtasks_raw = self._decomposer.decompose(goal, self.handler_names, context)
        else:
            # 回退：单任务模式
            handler = self._match_handler(goal)
            subtasks_raw = [{
                "goal": goal, "handler": handler,
                "depends_on": [], "context": context,
            }]

        # 步骤2: 创建 SubAgentTask 实例
        subtasks: List[SubAgentTask] = []
        task_ids: List[str] = []

        for raw in subtasks_raw:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"
            task = SubAgentTask(
                goal=raw["goal"],
                context=raw.get("context", context),
                handler=raw.get("handler", "default"),
                toolsets=toolsets or [],
                depends_on=raw.get("depends_on", []),
            )
            self.tasks[task_id] = task
            subtasks.append(task)
            task_ids.append(task_id)

        if not subtasks:
            return {"success": False, "summary": "任务分解后无子任务", "tasks": [], "execution_time": 0}

        # 步骤3: 拓扑排序执行（先执行无依赖的，再执行有依赖的）
        executed = self._execute_with_dependencies(task_ids, subtasks)

        # 步骤4: 收集结果
        for i, task_id in enumerate(task_ids):
            task = self.tasks[task_id]
            results.append({
                "task_id": task_id,
                "goal": task.goal,
                "handler": task.handler,
                "status": task.status,
                "result": task.result,
                "error": task.error,
            })

        # 步骤5: 聚合总结
        if use_llm and self._decomposer:
            summary = self._decomposer.aggregate(goal, results)
        else:
            summary = self._simple_aggregate(results)

        execution_time = time.time() - start_time

        all_success = all(r["status"] == "completed" for r in results)

        return {
            "success": all_success,
            "summary": summary,
            "tasks": results,
            "execution_time": round(execution_time, 2),
        }

    def delegate_single(
        self,
        task_id: str,
        goal: str,
        context: str = "",
        toolsets: List[str] = None,
    ) -> SubAgentTask:
        """
        委托单个任务（不分解）

        Args:
            task_id: 任务 ID
            goal: 任务目标
            context: 上下文
            toolsets: 工具集

        Returns:
            SubAgentTask
        """
        task = SubAgentTask(
            goal=goal,
            context=context,
            toolsets=toolsets or [],
        )
        self.tasks[task_id] = task
        return task

    # ── 执行引擎 ──

    def _execute_with_dependencies(
        self,
        task_ids: List[str],
        subtasks: List[SubAgentTask],
    ) -> None:
        """
        按依赖关系执行子任务

        算法:
          1. 找出所有无依赖的任务 → 并行执行
          2. 等待批次完成
          3. 检查哪些任务的依赖已全部完成 → 继续下一批
          4. 重复直到所有任务完成
        """
        completed = set()  # 已完成的索引集合
        remaining = set(range(len(subtasks)))  # 待执行的索引集合

        while remaining:
            # 找出本批次可执行的任务（所有依赖已满足）
            ready = [
                i for i in remaining
                if all(dep in completed for dep in subtasks[i].depends_on)
            ]

            if not ready:
                # 死锁检测：有任务但无法满足依赖
                stuck = [subtasks[i].goal for i in remaining]
                logger.error("AgentDelegate: 依赖死锁！卡住的任务: %s", stuck)
                for i in remaining:
                    sid = task_ids[i]
                    subtasks[i].status = "failed"
                    subtasks[i].error = f"依赖死锁: 前置任务 {subtasks[i].depends_on} 未完成"
                    self.tasks[sid] = subtasks[i]
                break

            # 并行执行就绪任务
            if len(ready) == 1:
                self._execute_single(task_ids[ready[0]], subtasks[ready[0]])
            else:
                self._execute_parallel(ready, task_ids, subtasks)

            # 标记完成
            for i in ready:
                completed.add(i)
                remaining.discard(i)

    def _execute_single(self, task_id: str, task: SubAgentTask) -> None:
        """执行单个子任务"""
        task.status = "running"
        task.started_at = time.time()
        self.tasks[task_id] = task

        try:
            handler_name = task.handler if task.handler in self.handlers else self._match_handler(task.goal)
            handler = self.handlers.get(handler_name)

            if handler:
                task.result = handler(task.context, task.toolsets)
                task.status = "completed"
            else:
                # 无匹配处理器 → 记录目标并完成
                task.result = {
                    "goal": task.goal,
                    "context": task.context,
                    "note": "无匹配处理器，已记录目标",
                    "executed_at": time.time(),
                }
                task.status = "completed"

        except Exception as e:
            task.retries += 1
            if task.retries <= 2:
                # 重试一次
                logger.warning("AgentDelegate: '%s' 失败，重试 (%d/2): %s",
                               task.goal[:50], task.retries, e)
                try:
                    handler = self.handlers.get(self._match_handler(task.goal))
                    if handler:
                        task.result = handler(task.context, task.toolsets)
                        task.status = "completed"
                    else:
                        raise
                except Exception as e2:
                    task.status = "failed"
                    task.error = str(e2)
            else:
                task.status = "failed"
                task.error = str(e)

        task.finished_at = time.time()
        self.tasks[task_id] = task

    def _execute_parallel(
        self,
        indices: List[int],
        task_ids: List[str],
        subtasks: List[SubAgentTask],
    ) -> None:
        """并行执行多个子任务"""
        # 标记所有为 running
        for i in indices:
            subtasks[i].status = "running"
            subtasks[i].started_at = time.time()
            self.tasks[task_ids[i]] = subtasks[i]

        with ThreadPoolExecutor(max_workers=min(len(indices), self._max_workers)) as pool:
            futures = {}
            for i in indices:
                task = subtasks[i]
                # 为每个子任务创建隔离的上下文副本
                isolated_context = copy.deepcopy(task.context)
                isolated_toolsets = copy.deepcopy(task.toolsets)

                futures[pool.submit(
                    self._execute_isolated,
                    task.goal,
                    task.handler,
                    isolated_context,
                    isolated_toolsets,
                )] = i

            for future in as_completed(futures):
                i = futures[future]
                try:
                    task = subtasks[i]
                    task.result, task.error = future.result()
                    task.status = "completed" if not task.error else "failed"
                    task.finished_at = time.time()
                except Exception as e:
                    subtasks[i].status = "failed"
                    subtasks[i].error = str(e)
                    subtasks[i].finished_at = time.time()

                self.tasks[task_ids[i]] = subtasks[i]

    def _execute_isolated(
        self,
        goal: str,
        handler_name: str,
        context: str,
        toolsets: List[str],
    ) -> tuple:
        """
        在隔离上下文中执行（线程安全）

        Returns:
            (result_dict, error_string)
        """
        try:
            handler = self.handlers.get(handler_name)
            if handler:
                result = handler(context, toolsets)
                return (result, "")
            else:
                handler = self._match_handler(goal)
                matched = self.handlers.get(handler)
                if matched:
                    result = matched(context, toolsets)
                    return (result, "")
                return (
                    {"goal": goal, "note": "无匹配处理器"},
                    "",
                )
        except Exception as e:
            return (None, str(e))

    # ── 处理器匹配 ──

    def _match_handler(self, goal: str) -> str:
        """
        根据目标匹配处理器（关键词匹配，作为 LLM 分解的回退）

        Args:
            goal: 任务目标

        Returns:
            匹配到的处理器名，无匹配返回 "default"
        """
        goal_lower = goal.lower()

        # 精确匹配
        for name in self.handlers:
            if name.lower() == goal_lower:
                return name

        # 包含匹配（按长度降序，优先匹配长关键词）
        sorted_names = sorted(self.handlers.keys(), key=len, reverse=True)
        for name in sorted_names:
            if name.lower() in goal_lower:
                return name

        return "default"

    # ── 结果聚合 ──

    def _simple_aggregate(self, results: List[Dict]) -> str:
        """简单文本聚合（无需 LLM）"""
        lines = []
        for i, r in enumerate(results, 1):
            status_icon = "✓" if r["status"] == "completed" else "✗"
            result_text = str(r.get("result", r.get("error", "")))[:200]
            lines.append(f"[{i}] {status_icon} {r['goal'][:80]}")
            if result_text:
                lines.append(f"    → {result_text}")
        return "\n".join(lines)

    # ── 状态查询 ──

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if task:
            return {
                "task_id": task_id,
                "goal": task.goal,
                "handler": task.handler,
                "status": task.status,
                "result": task.result,
                "error": task.error,
                "retries": task.retries,
            }
        return None

    def list_tasks(self) -> List[Dict]:
        """列出所有任务"""
        return [
            {
                "task_id": tid,
                "goal": t.goal,
                "handler": t.handler,
                "status": t.status,
                "retries": t.retries,
            }
            for tid, t in self.tasks.items()
        ]

    def cancel_task(self, task_id: str) -> bool:
        """取消待执行的任务"""
        task = self.tasks.get(task_id)
        if task and task.status in ("pending",):
            task.status = "cancelled"
            return True
        return False

    def clear_completed(self) -> int:
        """清理已完成/失败/取消的任务"""
        to_remove = [
            tid for tid, t in self.tasks.items()
            if t.status in ("completed", "failed", "cancelled")
        ]
        for tid in to_remove:
            del self.tasks[tid]
        return len(to_remove)


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_delegate: Optional[AgentDelegate] = None


def get_agent_delegate(backend=None, max_workers: int = 8) -> AgentDelegate:
    """
    获取全局 AgentDelegate 单例

    Args:
        backend: BaseLLMBackend 实例（首次创建时传入）
        max_workers: 最大并行线程数

    Returns:
        AgentDelegate 实例
    """
    global _delegate
    if _delegate is None:
        _delegate = AgentDelegate(backend=backend, max_workers=max_workers)
    elif backend is not None and _delegate._backend is None:
        # 补充 backend
        _delegate._backend = backend
        _delegate._decomposer = LLMDecomposer(backend)
    return _delegate


def reset_agent_delegate() -> None:
    """重置全局单例"""
    global _delegate
    _delegate = None

```
