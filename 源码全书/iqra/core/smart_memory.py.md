# `iqra/core/smart_memory.py`

> 路径：`iqra/core/smart_memory.py` | 行数：168


---


```python
"""
SmartMemory - 智能记忆系统
独立实现，支持检索画像、学习特征、偏好档案、建议记录
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class SmartMemory:
    """智能记忆引擎 - 深度学习用户偏好和行为模式"""

    # 受保护的内容类型边界
    BOUNDARIES = {
        "protected_content_types": [
            "api_keys", "passwords", "tokens", "private_keys",
            "credentials", "secrets", "auth_tokens"
        ]
    }

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.data_dir = os.path.join(project_root, "data", "smart_memory")
        os.makedirs(self.data_dir, exist_ok=True)

        # 默认选项
        self.options = {
            "enabled": True,
            "auto_learn": True,
            "max_memories": 1000,
            "context_window": 20,
        }

        # 运行时状态
        self._profile: Dict[str, Any] = {}
        self._retrieval_profile: Dict[str, Any] = {"stable_domains": []}
        self._learned_features: Dict[str, Any] = {"vocabulary": {}, "patterns": {}}
        self._suggestions: List[Dict[str, Any]] = []
        self._important_memories: List[Dict[str, Any]] = []

    # ── 检索画像 ──────────────────────────────────────

    def update_retrieval_profile(self, data: Dict[str, Any]) -> None:
        """更新检索画像"""
        if "stable_domains" in data:
            existing = set(self._retrieval_profile.get("stable_domains", []))
            for d in data["stable_domains"]:
                if d and len(d.strip()) > 0:
                    existing.add(d.strip()[:100])
            self._retrieval_profile["stable_domains"] = list(existing)[:50]

    def get_retrieval_profile(self) -> Dict[str, Any]:
        return self._retrieval_profile

    # ── 学习特征 ──────────────────────────────────────

    def update_learned_features(self, data: Dict[str, Any]) -> None:
        if "vocabulary" in data:
            vocab = self._learned_features.get("vocabulary", {})
            for k, v in data["vocabulary"].items():
                if isinstance(v, (int, float)):
                    vocab[k] = vocab.get(k, 0) + v
                else:
                    vocab[k] = v
            self._learned_features["vocabulary"] = vocab

    # ── 建议反馈 ──────────────────────────────────────

    def record_accepted_suggestion(self, content: str, context: Optional[Dict] = None) -> None:
        self._suggestions.append({
            "content": content[:500],
            "context": context or {},
            "accepted": True,
            "timestamp": datetime.now().isoformat(),
        })
        self._trim_suggestions()

    def record_rejected_suggestion(self, content: str, context: Optional[Dict] = None) -> None:
        self._suggestions.append({
            "content": content[:500],
            "context": context or {},
            "accepted": False,
            "timestamp": datetime.now().isoformat(),
        })
        self._trim_suggestions()

    def _trim_suggestions(self) -> None:
        max_items = self.options.get("max_memories", 1000)
        if len(self._suggestions) > max_items:
            self._suggestions = self._suggestions[-max_items:]

    # ── 用户档案 ──────────────────────────────────────

    def get_user_profile(self) -> Dict[str, Any]:
        """获取用户画像"""
        profile = self._load_preference_profile()
        return {
            "name": profile.get("name", ""),
            "language": profile.get("language", "zh"),
            "learning_state": profile.get("learning_state", "active"),
            "stable_domains": self._retrieval_profile.get("stable_domains", []),
            "vocabulary_size": len(self._learned_features.get("vocabulary", {})),
        }

    def _load_preference_profile(self) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, "preferences.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception:
                pass
        return self._default_preferences()

    def _default_preferences(self) -> Dict[str, Any]:
        return {
            "name": "",
            "language": "zh",
            "timezone": "Asia/Shanghai",
            "learning_state": "active",
            "preferences": {},
        }

    def save_preferences(self, preferences: Dict[str, Any]) -> None:
        current = self._load_preference_profile()
        current.update(preferences)
        path = os.path.join(self.data_dir, "preferences.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)

    # ── 重要记忆 ──────────────────────────────────────

    def add_important_memory(self, memory: Dict[str, Any]) -> None:
        memory["timestamp"] = memory.get("timestamp", datetime.now().isoformat())
        self._important_memories.append(memory)
        self._save_important_memories()

    def get_important_memories(self) -> List[Dict[str, Any]]:
        return self._important_memories[-50:]

    def _save_important_memories(self) -> None:
        path = os.path.join(self.data_dir, "important_memories.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._important_memories, f, ensure_ascii=False, indent=2)

    # ── 统计 ──────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "suggestions_total": len(self._suggestions),
            "suggestions_accepted": sum(1 for s in self._suggestions if s.get("accepted")),
            "domains_tracked": len(self._retrieval_profile.get("stable_domains", [])),
            "features_learned": len(self._learned_features.get("vocabulary", {})),
            "important_memories": len(self._important_memories),
            "options": self.options,
        }

    # ── 清理 ──────────────────────────────────────────

    def clear(self) -> None:
        self._retrieval_profile = {"stable_domains": []}
        self._learned_features = {"vocabulary": {}, "patterns": {}}
        self._suggestions = []
        self._important_memories = []
        # 不删除文件，仅清空运行时状态
```
