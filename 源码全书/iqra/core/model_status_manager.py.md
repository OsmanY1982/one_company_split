# `iqra/core/model_status_manager.py`

> 路径：`iqra/core/model_status_manager.py` | 行数：197


---


```python
"""
Iqra Model Status Manager - 模型状态追踪与自动切换

提供:
- Token 耗尽/错误模型记录
- 自动故障转移
- 24h 自动过期
- Provider 隔离
"""

import os
import json
import time
from typing import Dict, List, Any, Optional


class ModelStatusManager:
    """模型状态管理器"""
    
    EXPIRATION_HOURS = {
        "no_token": 24,      # Token 耗尽 24h 后自动恢复
        "rate_limit": 1,     # 限流 1h 后恢复
        "api_error": 1,      # 其他错误 1h 后恢复
    }
    
    def __init__(self, status_file: str = None):
        if status_file is None:
            # 使用项目相对路径，不硬编码
            _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            status_file = os.path.join(_project_root, "data", "model_status.json")
        self.status_file = status_file
        self._load_status()
    
    def _load_status(self):
        """加载状态文件"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    self.status = json.load(f)
            except Exception:
                self.status = {"failed_models": []}
        else:
            self.status = {"failed_models": []}
    
    def _save_status(self):
        """保存状态文件"""
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def _expire_old_failures(self):
        """清除过期失败记录"""
        now = time.time()
        expired_models = []
        
        for model in list(self.status.get("failed_models", [])):
            expire_hours = self.EXPIRATION_HOURS.get(model.get("error_type", "api_error"), 1)
            elapsed_hours = (now - model["timestamp"]) / 3600
            
            if elapsed_hours >= expire_hours:
                expired_models.append(model["model"])
        
        for model_name in expired_models:
            self.status["failed_models"] = [
                m for m in self.status["failed_models"] 
                if m["model"] != model_name
            ]
        
        if expired_models:
            self._save_status()
    
    def mark_failed(self, model: str, error_type: str = "api_error", 
                    error_message: str = "", provider: str = ""):
        """标记模型失败"""
        # 清除过期记录
        self._expire_old_failures()
        
        # 添加失败记录（去重）
        failed_list = self.status.get("failed_models", [])
        found_idx = next((i for i, m in enumerate(failed_list) 
                         if m["model"] == model and m["provider"] == provider), None)
        
        if found_idx is not None:
            # 更新现有记录
            failed_list[found_idx] = {
                "model": model,
                "error_type": error_type,
                "error_message": error_message[:500],  # 限制长度
                "provider": provider,
                "fail_count": failed_list[found_idx].get("fail_count", 0) + 1,
                "timestamp": time.time()
            }
        else:
            # 新增记录
            failed_list.append({
                "model": model,
                "error_type": error_type,
                "error_message": error_message[:500],
                "provider": provider,
                "fail_count": 1,
                "timestamp": time.time()
            })
        
        self.status["failed_models"] = failed_list
        self._save_status()
    
    def is_model_available(self, model: str, provider: str = "") -> bool:
        """检查模型是否可用"""
        # 清除过期记录
        self._expire_old_failures()
        
        failed_list = self.status.get("failed_models", [])
        
        for record in failed_list:
            if record["model"] == model and (not provider or record.get("provider") == provider):
                return False
        
        return True
    
    def get_next_available_model(self, models: List[str], current_model: str = None, 
                                  provider: str = "") -> Optional[str]:
        """获取下一个可用模型"""
        # 清除过期记录
        self._expire_old_failures()
        
        failed_set = set()
        for record in self.status.get("failed_models", []):
            if not provider or record.get("provider") == provider:
                failed_set.add(record["model"])
        
        # 过滤掉失败模型
        available = [m for m in models if m not in failed_set]
        
        if not available:
            return None
        
        if current_model and current_model in available:
            return current_model
        
        return available[0]
    
    def reset_model(self, model: str = None, provider: str = "") -> bool:
        """重置单个或所有模型状态"""
        if model:
            self.status["failed_models"] = [
                m for m in self.status.get("failed_models", [])
                if not (m["model"] == model and (not provider or m.get("provider") == provider))
            ]
            self._save_status()
            return True
        else:
            self.status["failed_models"] = []
            self._save_status()
            return True
    
    def get_status(self, model: str = None) -> Dict:
        """获取单个或所有模型状态"""
        self._expire_old_failures()
        
        if model:
            records = [
                r for r in self.status.get("failed_models", [])
                if r["model"] == model
            ]
            if records:
                return {
                    "model": model,
                    "available": False,
                    "errors": records
                }
            return {"model": model, "available": True}
        
        return {
            "total_failed": len(self.status.get("failed_models", [])),
            "failed_models": self.status.get("failed_models", [])
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        self._expire_old_failures()
        return {
            "total_failed_records": len(self.status.get("failed_models", [])),
            "expiration_rules": self.EXPIRATION_HOURS.copy()
        }


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_model_manager = None

def get_model_status_manager(file_path: str = None) -> ModelStatusManager:
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelStatusManager(file_path)
    return _model_manager

```
