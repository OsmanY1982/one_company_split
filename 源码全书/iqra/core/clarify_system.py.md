# `iqra/core/clarify_system.py`

> 路径：`iqra/core/clarify_system.py` | 行数：220


---


```python
"""
Iqra Clarify - 交互确认系统

提供:
- 多项选择询问
- 开放式问题收集
- 决策中间层
- 等待用户响应
"""

import os
import json
import time
from typing import Dict, List, Any, Optional


class ClarifySystem:
    """交互确认系统"""
    
    _DEFAULT_RESPONSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "clarify_response.json")

    def __init__(self, response_file: str = None):
        self.response_file = response_file or self._DEFAULT_RESPONSE_FILE
        self.pending_questions: Dict[str, Dict] = {}
    
    def ask(self, question: str, choices: List[str] = None, 
            open_ended: bool = False, timeout_minutes: int = 60) -> str:
        """
        提出问题并等待用户回答
        
        Args:
            question: 问题内容
            choices: 选项列表 (如果为空则为开放式提问)
            open_ended: 是否开放式提问
            timeout_minutes: 超时时间
            
        Returns:
            用户回答
        """
        import uuid
        question_id = str(uuid.uuid4())[:8]
        
        # 构建问题对象
        question_obj = {
            "id": question_id,
            "question": question,
            "choices": choices,
            "open_ended": open_ended or not choices,
            "created_at": time.time(),
            "timeout_at": time.time() + (timeout_minutes * 60),
            "status": "pending"
        }
        
        # 写入待回答文件
        self._write_pending(question_id, question_obj)
        
        # 提示用户如何回答
        if choices:
            print(f"\n❓ 需要你的决策:\n{question}")
            print("选项:")
            for i, choice in enumerate(choices, 1):
                print(f"  {i}. {choice}")
            print(f"\n请回复数字 (1-{len(choices)}) 或输入你的答案")
            print(f"(回答文件：{self.response_file})\n")
        else:
            print(f"\n❓ 需要你输入:\n{question}")
            print(f"\n请输入文字回答\n")
        
        # 轮询等待回答
        answer = self._wait_for_answer(question_id, timeout_seconds=timeout_minutes * 60)
        
        return answer
    
    def _wait_for_answer(self, question_id: str, timeout_seconds: int) -> str:
        """等待用户回答"""
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            # 检查是否有回答
            answer = self._check_answer(question_id)
            if answer:
                return answer
            
            # 检查超时
            question = self._get_question(question_id)
            if question and time.time() > question.get("timeout_at", 0):
                return f"[超时] 未在 {timeout_seconds//60}分钟内得到回应"
            
            # 等待 2 秒后重试
            time.sleep(2)
        
        return f"[超时] 未在 {timeout_seconds//60}分钟内得到回应"
    
    def _check_answer(self, question_id: str) -> Optional[str]:
        """检查是否有回答"""
        try:
            if os.path.exists(self.response_file):
                with open(self.response_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                answer_data = data.get("answer", {})
                if answer_data.get("question_id") == question_id:
                    status = answer_data.get("status")
                    
                    if status == "submitted":
                        # 标记为已读取
                        answer_data["status"] = "read"
                        self._write_response(answer_data)
                        
                        # 清理旧记录
                        self._cleanup_old_answers()
                        
                        return answer_data.get("value")
                    
                    elif status == "cancelled":
                        answer_data["status"] = "read"
                        self._write_response(answer_data)
                        return "cancelled"
                
                # 如果没有匹配的问题，清空回答文件
                if answer_data.get("question_id"):
                    self._clear_response()
            
            return None
            
        except Exception:
            return None
    
    def _write_pending(self, question_id: str, question_obj: dict):
        """写入待回答问题"""
        pending_dir = os.path.dirname(self.response_file) + "/pending"
        os.makedirs(pending_dir, exist_ok=True)
        
        path = os.path.join(pending_dir, f"{question_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(question_obj, f, ensure_ascii=False, indent=2)
    
    def _get_question(self, question_id: str) -> Optional[Dict]:
        """获取问题"""
        pending_dir = os.path.dirname(self.response_file) + "/pending"
        path = os.path.join(pending_dir, f"{question_id}.json")
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _write_response(self, answer_data: Dict):
        """写入回答"""
        with open(self.response_file, 'w', encoding='utf-8') as f:
            json.dump(answer_data, f, ensure_ascii=False, indent=2)
    
    def _clear_response(self):
        """清空回答"""
        if os.path.exists(self.response_file):
            os.remove(self.response_file)
    
    def _cleanup_old_answers(self):
        """清理旧回答"""
        pending_dir = os.path.dirname(self.response_file) + "/pending"
        if not os.path.exists(pending_dir):
            return
        
        now = time.time()
        for filename in os.listdir(pending_dir):
            if filename.endswith(".json"):
                path = os.path.join(pending_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 超过 1 小时且已读的答案，删除
                    if data.get("status") == "read" and (now - data.get("created_at", 0)) > 3600:
                        os.remove(path)
                except Exception:
                    pass
    
    def quick_confirm(self, question: str, choices: List[str] = None) -> bool:
        """
        快速确认 - 简化版，立即返回结果
        
        使用场景: 用户正在操作终端，可以直接输入回答
        """
        question_id = str(time.time())[:13]
        
        print(f"\n⚠️  确认:{question}")
        if choices:
            print("选项:", ", ".join(choices))
        
        # 临时修改 response_file 让检查能工作
        original_file = self.response_file
        temp_file = f"/tmp/clarify_temp_{question_id}.json"
        
        return self.ask(question, choices, open_ended=not choices)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        pending_dir = os.path.dirname(self.response_file) + "/pending"
        pending_count = 0
        
        if os.path.exists(pending_dir):
            pending_count = len([f for f in os.listdir(pending_dir) if f.endswith(".json")])
        
        return {
            "pending_questions": pending_count,
            "response_file": self.response_file
        }


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_clarify_system = None

def get_clarify_system(response_file: str = None) -> ClarifySystem:
    global _clarify_system
    if _clarify_system is None:
        _clarify_system = ClarifySystem(response_file)
    return _clarify_system

```
