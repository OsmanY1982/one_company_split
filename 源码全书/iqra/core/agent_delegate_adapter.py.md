# `iqra/core/agent_delegate_adapter.py`

> 路径：`iqra/core/agent_delegate_adapter.py` | 行数：335


---


```python
# -*- coding: utf-8 -*-
"""
AgentDelegate 适配层 — 为 AgentLoop 提供四个清晰接口

将 agent_delegate.py 的内部方法封装为独立类，方便 AgentLoop 按步骤调用：
  TaskDecomposer   → LLM 驱动的任务分解
  DependencyResolver → 依赖图拓扑排序，输出执行批次
  ParallelExecutor → 并行执行同批次无依赖子任务（上限 ≤5 并发）
  ResultAggregator → LLM 或简单文本聚合

设计约束：
  - 不改 agent_delegate.py 代码
  - 所有类均可独立实例化和使用
  - 并行度上限默认 5（可配置）
"""

import copy
import time
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .agent_delegate import LLMDecomposer


# ═══════════════════════════════════════════
# TaskDecomposer — 任务分解
# ═══════════════════════════════════════════

class TaskDecomposer:
    """
    LLM 驱动的任务分解器

    用法:
        decomposer = TaskDecomposer(backend)
        subtasks = decomposer.decompose("搜索 Python 文件并统计代码行数")
        # → [{"goal": "搜索 Python 文件", "handler": "default", "depends_on": [], ...},
        #    {"goal": "统计代码行数", "handler": "default", "depends_on": [0], ...}]
    """

    def __init__(self, backend):
        """
        Args:
            backend: BaseLLMBackend 实例
        """
        self._decomposer = LLMDecomposer(backend)

    def decompose(
        self,
        goal: str,
        handler_names: List[str] = None,
        context: str = "",
    ) -> List[dict]:
        """
        将目标拆解为子任务列表

        Args:
            goal: 用户原始目标
            handler_names: 可用处理器名称列表（默认 ["default"]）
            context: 额外上下文

        Returns:
            子任务列表 [{goal, handler, depends_on, context}, ...]
            失败时返回单任务列表（回退）
        """
        names = handler_names if handler_names else ["default"]
        return self._decomposer.decompose(goal, names, context)


# ═══════════════════════════════════════════
# DependencyResolver — 依赖图解析
# ═══════════════════════════════════════════

class DependencyResolver:
    """
    依赖图拓扑排序器

    输入子任务列表（含 depends_on 字段），输出分批执行计划。
    同一批次内的子任务无相互依赖，可安全并行。
    """

    @staticmethod
    def resolve(subtasks: List[dict]) -> List[List[dict]]:
        """
        按依赖关系分批

        Args:
            subtasks: 子任务列表 [{goal, handler, depends_on(idx list), context}, ...]

        Returns:
            批次列表 batches，每个批次是子任务列表，批内可并行，批间顺序执行

        Raises:
            ValueError: 检测到循环依赖时抛出
        """
        if not subtasks:
            return []

        completed: set = set()
        remaining: set = set(range(len(subtasks)))
        batches: List[List[dict]] = []

        while remaining:
            # 找出所有依赖已满足的任务
            ready = [
                i for i in remaining
                if all(dep in completed for dep in subtasks[i].get("depends_on", []))
            ]

            if not ready:
                # 有剩余任务但无依赖满足 → 循环依赖
                stuck_goals = [subtasks[i].get("goal", "?") for i in remaining]
                raise ValueError(
                    f"检测到循环依赖，卡住的任务: {stuck_goals}。"
                    f"已完成: {completed}"
                )

            batches.append([subtasks[i] for i in ready])
            for i in ready:
                completed.add(i)
                remaining.discard(i)

        return batches

    @staticmethod
    def has_parallelism(subtasks: List[dict]) -> bool:
        """判断子任务之间是否有可并行的机会"""
        if len(subtasks) <= 1:
            return False
        batches = DependencyResolver.resolve(subtasks)
        return any(len(batch) > 1 for batch in batches)


# ═══════════════════════════════════════════
# ParallelExecutor — 并行执行器
# ═══════════════════════════════════════════

class ParallelExecutor:
    """
    并行执行器 — 以受限并发数并行执行同批子任务

    特性:
      - 并发上限可配置（默认 5）
      - 每个子任务在独立线程中执行，上下文隔离
      - 失败不影响同批次其他任务
    """

    def __init__(self, max_workers: int = 5):
        """
        Args:
            max_workers: 最大并行线程数
        """
        self._max_workers = max(1, min(max_workers, 5))

    def execute(
        self,
        batch: List[dict],
        handler_func: Callable[[str, list], dict],
    ) -> List[dict]:
        """
        并行执行一批子任务

        Args:
            batch: 子任务列表 [{goal, handler, context, toolsets?}, ...]
            handler_func: 处理器函数，签名为 (context: str, toolsets: list) -> dict

        Returns:
            结果列表（与 batch 顺序一致），每个元素为 {success, result, error, goal, ...}
        """
        n = len(batch)
        if n == 0:
            return []
        if n == 1:
            return [ParallelExecutor._execute_single(batch[0], handler_func)]

        results: dict = {}

        with ThreadPoolExecutor(max_workers=min(n, self._max_workers)) as pool:
            futures = {}
            for i, task in enumerate(batch):
                ctx = copy.deepcopy(task.get("context", ""))
                ts = copy.deepcopy(task.get("toolsets", []))
                futures[pool.submit(handler_func, ctx, ts)] = i

            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception as e:
                    results[i] = {
                        "success": False,
                        "error": str(e),
                        "goal": batch[i].get("goal", ""),
                    }

        # 按原始顺序返回
        return [
            results.get(i, {
                "success": False,
                "error": "执行结果缺失",
                "goal": batch[i].get("goal", ""),
            })
            for i in range(n)
        ]

    @staticmethod
    def _execute_single(task: dict, handler_func: Callable) -> dict:
        """串行执行单个子任务"""
        try:
            result = handler_func(
                task.get("context", ""),
                task.get("toolsets", []),
            )
            result["goal"] = task.get("goal", "")
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "goal": task.get("goal", ""),
            }


# ═══════════════════════════════════════════
# ResultAggregator — 结果聚合
# ═══════════════════════════════════════════

class ResultAggregator:
    """
    结果聚合器 — 将多个子任务结果合并为统一总结

    支持 LLM 聚合（需要 backend）和简单文本拼接两种模式。
    """

    def __init__(self, decomposer: Optional[TaskDecomposer] = None):
        """
        Args:
            decomposer: TaskDecomposer 实例（用于 LLM 聚合），
                        不传则使用简单文本拼接
        """
        self._decomposer = decomposer

    def aggregate(self, goal: str, results: List[dict]) -> str:
        """
        聚合子任务结果

        Args:
            goal: 原始目标
            results: 子任务结果列表 [{goal, status, result, error}, ...]

        Returns:
            聚合后的文本总结
        """
        if self._decomposer:
            try:
                return self._decomposer._decomposer.aggregate(goal, results)
            except Exception:
                pass  # 降级到简单拼接

        # 简单文本拼接
        lines = [f"任务「{goal}」执行结果:"]
        for i, r in enumerate(results, 1):
            status_icon = "✓" if r.get("status") == "completed" else "✗"
            goal_text = str(r.get("goal", ""))[:80]
            result_text = str(r.get("result", r.get("error", "")))[:200]
            lines.append(f"  [{i}] {status_icon} {goal_text}")
            if result_text:
                lines.append(f"      → {result_text}")
        return "\n".join(lines)


# ═══════════════════════════════════════════
# 便捷函数：完整流水线
# ═══════════════════════════════════════════

def run_delegate_pipeline(
    goal: str,
    backend,
    handler_func: Callable[[str, list], dict],
    context: str = "",
    max_workers: int = 5,
) -> dict:
    """
    一键运行 AgentDelegate 完整流水线

    流程: TaskDecomposer → DependencyResolver → ParallelExecutor → ResultAggregator

    Args:
        goal: 用户原始目标
        backend: BaseLLMBackend 实例
        handler_func: 子任务处理器 (context, toolsets) -> dict
        context: 全局上下文
        max_workers: 最大并行数

    Returns:
        {
            "success": bool,
            "summary": str,
            "tasks": [{goal, status, result, error}, ...],
            "batches": int,
            "execution_time": float,
        }
    """
    start_time = time.time()

    # 1. 分解
    decomposer = TaskDecomposer(backend)
    subtasks_raw = decomposer.decompose(goal, context=context)

    # 2. 解析依赖
    batches = DependencyResolver.resolve(subtasks_raw)

    # 3. 逐批并行执行
    executor = ParallelExecutor(max_workers=max_workers)
    all_results = []
    for batch_idx, batch in enumerate(batches):
        batch_results = executor.execute(batch, handler_func)
        # 标注状态
        for r in batch_results:
            r.setdefault("status", "completed" if r.get("success", False) else "failed")
        all_results.extend(batch_results)

    # 4. 聚合
    aggregator = ResultAggregator(decomposer)
    summary = aggregator.aggregate(goal, all_results)

    elapsed = time.time() - start_time
    all_success = all(r.get("success", False) for r in all_results)

    return {
        "success": all_success,
        "summary": summary,
        "tasks": all_results,
        "batches": len(batches),
        "execution_time": round(elapsed, 2),
    }

```
