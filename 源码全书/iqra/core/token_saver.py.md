# `iqra/core/token_saver.py`

> 路径：`iqra/core/token_saver.py` | 行数：197


---


```python
"""
Token 优化系统 — 多模式 Token 节省策略

提供:
- 上下文压缩
- 消息裁剪
- 智能摘要
- 去重优化
- 多模式切换
"""

import json
import hashlib
import time
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenStats:
    """Token 统计"""
    mode: str
    original_tokens: int
    optimized_tokens: int
    savings_percent: float


class TokenOptimizer:
    """Token 优化器"""
    
    MODES = {
        "extreme": {"savings": "85-95%", "context_limit": 1000, "use_when": "Token 几乎耗尽"},
        "balanced": {"savings": "60-75%", "context_limit": 2000, "use_when": "日常使用"},
        "performance": {"savings": "20-40%", "context_limit": 4000, "use_when": "重要任务"},
        "disabled": {"savings": "0%", "context_limit": 8000, "use_when": "调试/测试"},
    }
    
    def __init__(self, mode: str = "balanced"):
        self.mode = mode
        self.cache: Dict[str, Any] = {}
        self.stats: Dict[str, int] = {"original": 0, "optimized": 0}
    
    def estimate_tokens(self, text: str) -> int:
        """估算 Token 数"""
        if not text:
            return 0
        chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english = len(re.findall(r'[a-zA-Z]+', text))
        punctuation = sum(1 for c in text if not c.isalnum() and not c.isspace())
        return int(chinese * 1.5 + english * 0.75 + punctuation * 0.5)
    
    def optimize_messages(self, messages: List[Dict]) -> List[Dict]:
        """优化消息列表"""
        if self.mode == "disabled" or len(messages) <= 3:
            return messages
        
        self.stats["original"] += sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        
        result = messages
        
        if self.mode == "extreme":
            result = self._extreme_compress(messages)
        elif self.mode == "balanced":
            result = self._balanced_compress(messages)
        elif self.mode == "performance":
            result = self._performance_compress(messages)
        
        result = self._deduplicate(result)
        result = self._whitespace_optimize(result)
        
        self.stats["optimized"] += sum(self.estimate_tokens(m.get("content", "")) for m in result)
        return result
    
    def _extreme_compress(self, messages: List[Dict]) -> List[Dict]:
        """极限模式：保留最后 3 轮，其余压缩为关键词摘要"""
        if len(messages) <= 6:
            return messages
        
        # 保留最后 6 条（3 轮对话）
        recent = messages[-6:]
        
        # 将历史压缩为摘要
        history_text = "\n".join(m.get("content", "") for m in messages[:-6])
        keywords = self._extract_keywords(history_text, max_keywords=20)
        
        summary_msg = {
            "role": "system",
            "content": f"[历史摘要] {', '.join(keywords)}"
        }
        
        return [summary_msg] + recent
    
    def _balanced_compress(self, messages: List[Dict]) -> List[Dict]:
        """平衡模式：保留最后 5 轮，其余截断"""
        if len(messages) <= 10:
            return messages
        
        recent = messages[-10:]
        older = messages[:-10]
        
        # 截断旧消息
        truncated = []
        for msg in older:
            content = msg.get("content", "")
            if len(content) > 500:
                msg = msg.copy()
                msg["content"] = content[:300] + "\n...[已截断]...\n" + content[-150:]
            truncated.append(msg)
        
        return truncated + recent
    
    def _performance_compress(self, messages: List[Dict]) -> List[Dict]:
        """性能模式：仅去除重复和空白"""
        return self._deduplicate(messages)
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """提取关键词"""
        # 简单频率统计
        words = re.findall(r'[\u4e00-\u9fff]{2,4}|[a-zA-Z]{3,}', text)
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]
    
    def _deduplicate(self, messages: List[Dict]) -> List[Dict]:
        """去除重复消息"""
        seen = set()
        result = []
        
        for msg in messages:
            content = msg.get("content", "")
            # 归一化
            normalized = re.sub(r'\s+', ' ', content.lower().strip())
            content_hash = hashlib.md5(normalized.encode()).hexdigest()
            
            if content_hash not in seen:
                seen.add(content_hash)
                result.append(msg)
        
        return result
    
    def _whitespace_optimize(self, messages: List[Dict]) -> List[Dict]:
        """空白优化"""
        result = []
        for msg in messages:
            content = msg.get("content", "")
            # 压缩连续空白
            optimized = re.sub(r'\n{3,}', '\n\n', content)
            optimized = re.sub(r' {2,}', ' ', optimized)
            
            if optimized != content:
                msg = msg.copy()
                msg["content"] = optimized
            
            result.append(msg)
        return result
    
    def set_mode(self, mode: str):
        """设置优化模式"""
        if mode in self.MODES:
            self.mode = mode
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        original = self.stats.get("original", 0)
        optimized = self.stats.get("optimized", 0)
        savings = ((original - optimized) / original * 100) if original > 0 else 0
        
        return {
            "mode": self.mode,
            "original_tokens": original,
            "optimized_tokens": optimized,
            "savings_percent": round(savings, 1),
            "available_modes": list(self.MODES.keys())
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {"original": 0, "optimized": 0}


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_token_optimizer = None

def get_token_optimizer(mode: str = "balanced") -> TokenOptimizer:
    """获取 Token 优化器单例"""
    global _token_optimizer
    if _token_optimizer is None:
        _token_optimizer = TokenOptimizer(mode)
    return _token_optimizer

```
