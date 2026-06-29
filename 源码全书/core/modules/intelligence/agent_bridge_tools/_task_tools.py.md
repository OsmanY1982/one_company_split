# `core/modules/intelligence/agent_bridge_tools/_task_tools.py`

> 路径：`core/modules/intelligence/agent_bridge_tools/_task_tools.py` | 行数：103


---


```python
"""任务/生产力工具 Mixin：todo / task_scheduler / search_sessions"""


class _TaskToolsMixin:
    """任务 / 生产力工具注册"""

    # ── 17. todo ──
    def _reg_todo(self):
        """任务清单（todo_system 模块）"""
        def handler(action: str = "list", title: str = "", status: str = "") -> dict:
            todo = self._todo
            if not todo:
                return {"error": "任务系统未启用（todo_system 模块缺失）"}
            try:
                if action == "add":
                    item = todo.add(title)
                    return {"action": "add", "item": item}
                elif action == "list":
                    items = todo.list()
                    return {"action": "list", "items": items, "total": len(items)}
                elif action == "done":
                    result = todo.mark_done(title)
                    return {"action": "done", "result": result}
                else:
                    return {"error": f"未知操作: {action}，支持 add/list/done"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="todo",
            description="管理任务清单：添加、查看、标记完成",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: add（添加）/ list（查看）/ done（完成）", "default": "list"},
                    "title": {"type": "string", "description": "任务标题（add/done 时需要）"},
                    "status": {"type": "string", "description": "状态过滤（list 时可选）"},
                },
                "required": [],
            },
            category="productivity",
        )(handler)

    # ── 18. task_scheduler ──
    def _reg_task_scheduler(self):
        """定时任务（task_scheduler 模块）"""
        def handler(action: str = "list", title: str = "", schedule: str = "") -> dict:
            sched = self._task_scheduler
            if not sched:
                return {"error": "定时任务未启用（task_scheduler 模块缺失）"}
            try:
                if action == "add":
                    task = sched.add(title, schedule)
                    return {"action": "add", "task": task}
                elif action == "list":
                    tasks = sched.list()
                    return {"action": "list", "tasks": tasks}
                elif action == "remove":
                    sched.remove(title)
                    return {"action": "remove", "title": title, "success": True}
                else:
                    return {"error": f"未知操作: {action}，支持 add/list/remove"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="task_scheduler",
            description="管理定时任务：创建、查看、删除",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: add（添加）/ list（查看）/ remove（删除）", "default": "list"},
                    "title": {"type": "string", "description": "任务标题"},
                    "schedule": {"type": "string", "description": "调度表达式（add 时需要），如 'daily 08:00'"},
                },
                "required": [],
            },
            category="productivity",
        )(handler)

    # ── 19. search_sessions ──
    def _reg_search_sessions(self):
        """历史会话搜索（session_search 模块）"""
        def handler(query: str, top_k: int = 10) -> dict:
            ss = self._session_search
            if not ss:
                return {"error": "会话搜索未启用（session_search 模块缺失）"}
            try:
                results = ss.search(query, top_k=top_k)
                return {"query": query, "results": results, "count": len(results)}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="search_sessions",
            description="搜索历史对话会话，找到之前讨论过的内容",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="memory",
        )(handler)

```
