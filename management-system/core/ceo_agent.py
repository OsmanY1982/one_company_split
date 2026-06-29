# -*- coding: utf-8 -*-
"""
AI CEO Agent — 智能CEO助手
支持角色定义、任务派发、团队状态监控
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class CEOAgent:
    """AI CEO 智能代理"""

    def __init__(self, name: str = "小马", data_dir: str = None):
        self.name = name
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "data")
        self._team: List[Dict] = []
        self._tasks: List[Dict] = []
        self._init_team()

    def _init_team(self):
        """初始化团队"""
        self._team = [
            {"name": "小王", "role": "销售经理", "status": "在线", "skills": ["客户管理", "订单处理"]},
            {"name": "小张", "role": "财务专员", "status": "在线", "skills": ["财务报表", "收支管理"]},
            {"name": "小李", "role": "技术开发", "status": "在线", "skills": ["系统开发", "数据分析"]},
        ]

    def hire(self, name: str, role: str, skills: List[str] = None) -> Dict:
        """招聘新员工"""
        employee = {
            "name": name,
            "role": role,
            "status": "在线",
            "skills": skills or [],
            "joined_at": datetime.now().isoformat()
        }
        self._team.append(employee)
        print(f"[CEO] 新成员加入: {name} - {role}")
        return employee

    def assign_task(self, title: str, description: str, assignee: str = "", priority: str = "medium") -> Dict:
        """派发任务"""
        task = {
            "id": f"task_{len(self._tasks) + 1}",
            "title": title,
            "description": description,
            "assignee": assignee,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self._tasks.append(task)
        print(f"[CEO] 任务已派发: {title} → {assignee}")
        return task

    def get_team_status(self) -> List[Dict]:
        """获取团队状态"""
        return [
            {
                "name": m["name"],
                "role": m["role"],
                "status": m["status"]
            }
            for m in self._team
        ]

    def get_pending_tasks(self) -> List[Dict]:
        """获取待处理任务"""
        return [t for t in self._tasks if t["status"] == "pending"]


# 全局实例
_ceo = None


def get_ceo() -> CEOAgent:
    global _ceo
    if _ceo is None:
        _ceo = CEOAgent()
    return _ceo
