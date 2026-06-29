# `iqra/core/enhanced_core.py`

> 路径：`iqra/core/enhanced_core.py` | 行数：549


---


```python
"""
Iqra 核心集成 — 新增能力整合

整合:
- 技能系统 (skill_system)
- Token 优化 (token_saver)
- 任务调度 (task_scheduler)
- 持久化记忆 (memory)
- 会话搜索 (session_search)
- 文件补丁 (patch_engine)
- 子代理委托 (agent_delegate)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 确保 iqra 在路径中
iqra_root = Path(__file__).parent.parent
if str(iqra_root) not in sys.path:
    sys.path.insert(0, str(iqra_root))


class IqraEnhanced:
    """Iqra 增强核心"""
    
    def __init__(self, skills_dir: str = None, data_dir: str = None, memory_store=None):
        self.skills_dir = skills_dir or str(iqra_root / "skills")
        self.data_dir = data_dir or str(iqra_root.parent / "data")
        
        # 接收外部 SmartMemoryStore（统一门面），否则降级为独立 IqraMemory
        self._injected_memory_store = memory_store
        
        # 初始化各模块
        self.skill_system = None
        self.token_optimizer = None
        self.scheduler = None
        self.memory = None
        self.session_search = None
        self.patch_engine = None
        self.agent_delegate = None
        
        self._init_modules()
    
    def _init_modules(self):
        """初始化模块"""
        # 技能系统
        try:
            from iqra.core.skill_system import get_skill_system
            self.skill_system = get_skill_system(self.skills_dir)
        except ImportError as e:
            print(f"⚠️ 技能系统加载失败: {e}")
        
        # Token 优化
        try:
            from iqra.core.token_saver import get_token_optimizer
            self.token_optimizer = get_token_optimizer("balanced")
        except ImportError as e:
            print(f"⚠️ Token 优化器加载失败: {e}")
        
        # 任务调度
        try:
            from iqra.core.task_scheduler import get_scheduler
            self.scheduler = get_scheduler(os.path.join(self.data_dir, "scheduler.db"))
        except ImportError as e:
            print(f"⚠️ 任务调度器加载失败: {e}")
        
        # 持久化记忆 — 优先使用注入的 SmartMemoryStore，降级为独立 IqraMemory
        try:
            if self._injected_memory_store is not None:
                self.memory = self._injected_memory_store
            else:
                from iqra.core.memory import get_memory
                self.memory = get_memory(os.path.join(self.data_dir, "memory.db"))
        except ImportError as e:
            print(f"⚠️ 记忆系统加载失败: {e}")
        
        # 会话搜索
        try:
            from iqra.core.session_search import get_session_search
            self.session_search = get_session_search(os.path.join(self.data_dir, "sessions.db"))
        except ImportError as e:
            print(f"⚠️ 会话搜索加载失败: {e}")
        
        # 文件补丁
        try:
            from iqra.core.patch_engine import get_patch_engine
            self.patch_engine = get_patch_engine()
        except ImportError as e:
            print(f"⚠️ 补丁引擎加载失败: {e}")
        
        # 子代理委托
        try:
            from iqra.core.agent_delegate import get_agent_delegate
            self.agent_delegate = get_agent_delegate()
        except ImportError as e:
            print(f"⚠️ 代理委托加载失败：{e}")
        
        # TODO 任务清单
        try:
            from iqra.core.todo_system import get_todo_system
            self.todo_system = get_todo_system(os.path.join(self.data_dir, "todos.db"))
        except ImportError as e:
            print(f"⚠️ TODO 系统加载失败：{e}")
        
        # 模型状态管理器
        try:
            from iqra.core.model_status_manager import get_model_status_manager
            self.model_manager = get_model_status_manager(os.path.join(self.data_dir, "model_status.json"))
        except ImportError as e:
            print(f"⚠️ 模型管理器加载失败：{e}")
        
        # 后台进程管理
        try:
            from iqra.core.process_manager import get_process_manager
            self.process_manager = get_process_manager()
        except ImportError as e:
            print(f"⚠️ 进程管理器加载失败：{e}")
        
        # 交互确认系统
        try:
            from iqra.core.clarify_system import get_clarify_system
            self.clarify_system = get_clarify_system()
        except ImportError as e:
            print(f"⚠️ Clarify 系统加载失败：{e}")
        
        # Web/GUI 同步桥
        try:
            from iqra.core.sync_bridge import get_sync_bridge
            self.sync_bridge = get_sync_bridge()
        except ImportError as e:
            print(f"⚠️ 同步桥加载失败：{e}")
    
    # ═══════════════════════════════════════════
    # 技能系统 API
    # ═══════════════════════════════════════════
    
    def match_skill(self, query: str, top_k: int = 3):
        """匹配技能"""
        if self.skill_system:
            return self.skill_system.match(query, top_k)
        return []
    
    def list_skills(self):
        """列出技能"""
        if self.skill_system:
            return self.skill_system.list_skills()
        return []
    
    def get_skill(self, name: str):
        """获取技能"""
        if self.skill_system:
            return self.skill_system.get_skill(name)
        return None
    
    def reload_skills(self):
        """重载技能"""
        if self.skill_system:
            self.skill_system.reload()
    
    # ═══════════════════════════════════════════
    # Token 优化 API
    # ═══════════════════════════════════════════
    
    def optimize_messages(self, messages, mode: str = None):
        """优化消息"""
        if self.token_optimizer:
            if mode:
                self.token_optimizer.set_mode(mode)
            return self.token_optimizer.optimize_messages(messages)
        return messages
    
    def get_token_stats(self):
        """获取 Token 统计"""
        if self.token_optimizer:
            return self.token_optimizer.get_stats()
        return {"error": "Token 优化器未加载"}
    
    def set_token_mode(self, mode: str):
        """设置 Token 优化模式"""
        if self.token_optimizer:
            self.token_optimizer.set_mode(mode)
    
    # ═══════════════════════════════════════════
    # 任务调度 API
    # ═══════════════════════════════════════════
    
    def add_task(self, name: str, schedule: str, handler_name: str, params: Dict = None, task_id: str = None):
        """添加定时任务"""
        if self.scheduler:
            return self.scheduler.add_task(name, schedule, handler_name, params, task_id)
        return None
    
    def remove_task(self, task_id: str):
        """移除任务"""
        if self.scheduler:
            return self.scheduler.remove_task(task_id)
        return False
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        if self.scheduler:
            self.scheduler.pause_task(task_id)
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        if self.scheduler:
            self.scheduler.resume_task(task_id)
    
    def list_tasks(self):
        """列出任务"""
        if self.scheduler:
            return self.scheduler.list_tasks()
        return []
    
    def register_handler(self, name: str, func):
        """注册任务处理函数"""
        if self.scheduler:
            self.scheduler.register_handler(name, func)
    
    def check_due_tasks(self):
        """检查并执行到期任务"""
        if self.scheduler:
            due = self.scheduler.get_due_tasks()
            results = []
            for task in due:
                result = self.scheduler.execute_task(task)
                results.append({"task_id": task.task_id, "result": result})
            return results
        return []
    
    def get_scheduler_stats(self):
        """获取调度器统计"""
        if self.scheduler:
            return self.scheduler.get_stats()
        return {"error": "调度器未加载"}
    
    # ═══════════════════════════════════════════
    # 记忆系统 API
    # ═══════════════════════════════════════════
    
    def add_memory(self, category: str, content: str, priority: int = 5):
        """添加记忆"""
        if self.memory:
            return self.memory.add(category, content, priority)
        return None
    
    def replace_memory(self, entry_id: str, new_content: str):
        """替换记忆"""
        if self.memory:
            return self.memory.replace(entry_id, new_content)
        return False
    
    def get_memory_entry(self, entry_id: str):
        """获取单个记忆"""
        if self.memory:
            return self.memory.get(entry_id)
        return None
    
    def search_memory(self, category: str = None, keyword: str = None, limit: int = 20):
        """搜索记忆"""
        if self.memory:
            return self.memory.search(category, keyword, limit)
        return []
    
    def remove_memory(self, entry_id: str):
        """删除记忆"""
        if self.memory:
            return self.memory.remove(entry_id)
        return False
    
    def get_memory_stats(self):
        """获取记忆统计"""
        if self.memory:
            return self.memory.get_stats()
        return {"error": "记忆系统未加载"}
    
    # ═══════════════════════════════════════════
    # 会话搜索 API
    # ═══════════════════════════════════════════
    
    def search_sessions(self, query: str, limit: int = 10, days: int = None):
        """搜索历史会话"""
        if self.session_search:
            return self.session_search.search(query, limit, days)
        return []
    
    def get_recent_sessions(self, limit: int = 10):
        """获取最近会话"""
        if self.session_search:
            return self.session_search.get_recent(limit)
        return []
    
    def save_session(self, session_id: str, title: str = "", summary: str = "", **kwargs):
        """保存会话索引"""
        if self.session_search:
            return self.session_search.save_session(session_id, title, summary, **kwargs)
    
    def get_session_stats(self):
        """获取会话统计"""
        if self.session_search:
            return self.session_search.get_stats()
        return {"error": "会话搜索未加载"}
    
    # ═══════════════════════════════════════════
    # 文件补丁 API
    # ═══════════════════════════════════════════
    
    def patch_file(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False):
        """精确文件补丁"""
        if self.patch_engine:
            return self.patch_engine.patch(file_path, old_string, new_string, replace_all)
        return {"error": "补丁引擎未加载"}
    
    def patch_multiple(self, file_path: str, replacements: List[Dict]):
        """批量补丁"""
        if self.patch_engine:
            return self.patch_engine.patch_multiple(file_path, replacements)
        return {"error": "补丁引擎未加载"}
    
    # ═══════════════════════════════════════════
    # 子代理委托 API
    # ═══════════════════════════════════════════
    
    def delegate_task(self, task_id: str, goal: str, context: str = "", toolsets: List[str] = None):
        """委托任务"""
        if self.agent_delegate:
            return self.agent_delegate.delegate_task(task_id, goal, context, toolsets)
        return None
    
    def execute_delegated_task(self, task_id: str):
        """执行委托任务"""
        if self.agent_delegate:
            return self.agent_delegate.execute_task(task_id)
        return {"error": "代理委托未加载"}
    
    def get_task_status(self, task_id: str):
        """获取任务状态"""
        if self.agent_delegate:
            return self.agent_delegate.get_task_status(task_id)
        return None
    
    def register_agent_handler(self, name: str, func):
        """注册代理处理器"""
        if self.agent_delegate:
            self.agent_delegate.register_handler(name, func)
    
    def get_all_tasks(self):
        """列出所有代理任务"""
        if self.agent_delegate:
            return self.agent_delegate.list_tasks()
        return []
    
    # ═══════════════════════════════════════════
    # TODO 任务清单 API
    # ═══════════════════════════════════════════
    
    def add_todo(self, content: str, priority: int = 0) -> str:
        """添加任务"""
        if self.todo_system:
            return self.todo_system.add(content, priority)
        return None
    
    def mark_todo_completed(self, task_id: str):
        """标记完成"""
        if self.todo_system:
            return self.todo_system.mark_completed(task_id)
    
    def mark_todo_in_progress(self, task_id: str):
        """设为进行中"""
        if self.todo_system:
            return self.todo_system.mark_in_progress(task_id)
    
    def cancel_todo(self, task_id: str):
        """取消任务"""
        if self.todo_system:
            return self.todo_system.cancel(task_id)
    
    def delete_todo(self, task_id: str):
        """删除任务"""
        if self.todo_system:
            return self.todo_system.delete(task_id)
        return False
    
    def get_todos(self, status: str = None) -> List[Dict]:
        """获取任务列表"""
        if self.todo_system:
            items = self.todo_system.get_all()
            if status:
                items = [i for i in items if i.status == status]
            return [{"id": i.id, "content": i.content, "status": i.status, "priority": i.priority} for i in items]
        return []
    
    def get_todo_stats(self) -> Dict:
        """获取统计"""
        if self.todo_system:
            return self.todo_system.get_stats()
        return {"error": "TODO 系统未加载"}
    
    # ═══════════════════════════════════════════
    # 模型状态管理器 API
    # ═══════════════════════════════════════════
    
    def mark_model_failed(self, model: str, error_type: str = "api_error", 
                          error_message: str = "", provider: str = ""):
        """标记模型失败"""
        if self.model_manager:
            return self.model_manager.mark_failed(model, error_type, error_message, provider)
    
    def is_model_available(self, model: str, provider: str = "") -> bool:
        """检查模型是否可用"""
        if self.model_manager:
            return self.model_manager.is_model_available(model, provider)
        return True
    
    def get_next_available_model(self, models: List[str], current: str = None, 
                                  provider: str = "") -> Optional[str]:
        """获取下一个可用模型"""
        if self.model_manager:
            return self.model_manager.get_next_available_model(models, current, provider)
        return models[0] if models else None
    
    def reset_model_status(self, model: str = None):
        """重置模型状态"""
        if self.model_manager:
            return self.model_manager.reset_model(model)
    
    def get_model_status(self, model: str = None) -> Dict:
        """获取模型状态"""
        if self.model_manager:
            return self.model_manager.get_status(model)
        return {}
    
    # ═══════════════════════════════════════════
    # 后台进程管理 API
    # ═══════════════════════════════════════════
    
    def start_process(self, command: str, workdir: str = None, name: str = None) -> str:
        """启动后台进程"""
        if self.process_manager:
            return self.process_manager.start(command, workdir, name)
        return ""
    
    def list_processes(self) -> List[Dict]:
        """列出所有进程"""
        if self.process_manager:
            return self.process_manager.list_processes()
        return []
    
    def poll_process(self, process_id: str, limit: int = 200) -> Dict:
        """轮询进程输出"""
        if self.process_manager:
            return self.process_manager.poll(process_id, limit)
        return {"error": "进程管理器未加载"}
    
    def log_process(self, process_id: str, offset: int = 0, limit: int = 200) -> Dict:
        """查看进程日志"""
        if self.process_manager:
            return self.process_manager.log(process_id, offset, limit)
        return {"error": "进程管理器未加载"}
    
    def wait_process(self, process_id: str, timeout: int = None) -> Dict:
        """等待进程完成"""
        if self.process_manager:
            return self.process_manager.wait(process_id, timeout)
        return {"error": "进程管理器未加载"}
    
    def kill_process(self, process_id: str) -> bool:
        """终止进程"""
        if self.process_manager:
            return self.process_manager.kill(process_id)
        return False
    
    def send_to_process(self, process_id: str, data: str):
        """向进程发送 stdin"""
        if self.process_manager:
            self.process_manager.write(process_id, data)
    
    # ═══════════════════════════════════════════
    # 交互确认系统 API
    # ═══════════════════════════════════════════
    
    def clarify(self, question: str, choices: List[str] = None, 
               open_ended: bool = False, timeout_minutes: int = 60) -> str:
        """提出问题并等待用户回答"""
        if self.clarify_system:
            return self.clarify_system.ask(question, choices, open_ended, timeout_minutes)
        return "clarify 系统未加载"
    
    def quick_confirm(self, question: str, choices: List[str] = None) -> bool:
        """快速确认"""
        if self.clarify_system:
            answer = self.clarify_system.ask(question, choices, open_ended=False)
            return answer.lower() in ["确定", "是", "yes", "y", "1"]
        return True
    
    # ═══════════════════════════════════════════
    # Web/GUI 同步桥 API
    # ═══════════════════════════════════════════
    
    def push_gui_data(self, data: Dict[str, Any]) -> bool:
        """GUI → Web 推送数据"""
        if self.sync_bridge:
            return self.sync_bridge.push_gui_to_web(data)
        return False
    
    def push_web_data(self, data: Dict[str, Any]) -> bool:
        """Web → GUI 推送数据"""
        if self.sync_bridge:
            return self.sync_bridge.push_web_to_gui(data)
        return False
    
    def read_gui_changes(self) -> Dict[str, Any]:
        """Web 读取 GUI 变更"""
        if self.sync_bridge:
            return self.sync_bridge.read_gui_changes()
        return {"data": {}, "version": 1}
    
    def read_web_changes(self) -> Dict[str, Any]:
        """GUI 读取 Web 变更"""
        if self.sync_bridge:
            return self.sync_bridge.read_web_changes()
        return {"data": {}, "version": 1}
    
    def reset_sync(self):
        """重置同步数据"""
        if self.sync_bridge:
            return self.sync_bridge.reset_sync()
    
    def get_sync_status(self) -> Dict:
        """获取同步状态"""
        if self.sync_bridge:
            return self.sync_bridge.get_status()
        return {}


# ═══════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════

_enhanced = None

def get_enhanced(skills_dir: str = None, data_dir: str = None) -> IqraEnhanced:
    """获取增强核心单例"""
    global _enhanced
    if _enhanced is None:
        _enhanced = IqraEnhanced(skills_dir, data_dir)
    return _enhanced

```
