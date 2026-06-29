# `iqra/core/patch_engine.py`

> 路径：`iqra/core/patch_engine.py` | 行数：234


---


```python
"""
Iqra Patch Engine - 精确文件补丁引擎

提供:
- 模糊匹配查找替换
- 自动语法检查
- 安全备份
- 差异报告
"""

import os
import re
import difflib
import shutil
from typing import Dict, List, Any, Optional, Tuple


class PatchEngine:
    """精确文件补丁引擎"""
    
    _DEFAULT_BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "patches", "backups")

    def __init__(self):
        self.backup_dir = self._DEFAULT_BACKUP_DIR
    
    def patch(self, file_path: str, old_string: str, new_string: str, 
              replace_all: bool = False) -> Dict:
        """
        精确补丁
        
        Args:
            file_path: 文件路径
            old_string: 查找内容
            new_string: 替换内容
            replace_all: 是否替换所有匹配
            
        Returns:
            {
                "success": bool,
                "diff": str,
                "backup_path": str,
                "message": str
            }
        """
        if not os.path.exists(file_path):
            return {"success": False, "message": f"文件不存在: {file_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()
            
            # 尝试模糊匹配
            match_info = self._fuzzy_find(original, old_string)
            if not match_info:
                return {"success": False, "message": "未找到匹配内容"}
            
            # 执行替换
            if replace_all:
                modified = original.replace(old_string, new_string)
            else:
                start, end = match_info["start"], match_info["end"]
                modified = original[:start] + new_string + original[end:]
            
            # 生成 diff
            diff = self._generate_diff(original, modified)
            
            # 备份
            backup_path = self._backup_file(file_path)
            
            # 写入
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)
            
            # 语法检查 (Python)
            syntax_ok = True
            syntax_error = ""
            if file_path.endswith('.py'):
                syntax_ok, syntax_error = self._check_syntax(file_path)
                if not syntax_ok:
                    # 恢复备份
                    shutil.copy2(backup_path, file_path)
                    return {
                        "success": False,
                        "message": f"语法错误: {syntax_error}",
                        "diff": diff,
                        "restored": True
                    }
            
            return {
                "success": True,
                "diff": diff,
                "backup_path": backup_path,
                "message": "补丁应用成功",
                "syntax_ok": syntax_ok
            }
            
        except Exception as e:
            return {"success": False, "message": f"错误: {str(e)}"}
    
    def _fuzzy_find(self, content: str, pattern: str, threshold: float = 0.85) -> Optional[Dict]:
        """模糊查找"""
        # 精确匹配
        idx = content.find(pattern)
        if idx >= 0:
            return {"start": idx, "end": idx + len(pattern), "score": 1.0}
        
        # 忽略空白差异
        normalized_content = re.sub(r'\s+', ' ', content)
        normalized_pattern = re.sub(r'\s+', ' ', pattern)
        idx = normalized_content.find(normalized_pattern)
        if idx >= 0:
            # 映射回原始位置
            orig_idx = self._map_normalized_to_original(content, pattern)
            if orig_idx >= 0:
                return {"start": orig_idx, "end": orig_idx + len(pattern), "score": 0.95}
        
        # 模糊匹配
        lines = content.split('\n')
        pattern_lines = pattern.split('\n')
        
        best_match = None
        best_score = 0
        
        for i in range(len(lines) - len(pattern_lines) + 1):
            chunk = '\n'.join(lines[i:i+len(pattern_lines)])
            score = self._similarity(chunk, pattern)
            if score > best_score and score >= threshold:
                best_score = score
                start_idx = sum(len(l) + 1 for l in lines[:i])
                end_idx = start_idx + len(chunk)
                best_match = {"start": start_idx, "end": end_idx, "score": score}
        
        return best_match
    
    def _map_normalized_to_original(self, content: str, pattern: str) -> int:
        """映射归一化位置到原始位置"""
        # 简化实现：查找模式首行在原始内容中的位置
        first_line = pattern.split('\n')[0].strip()
        if not first_line:
            return -1
        
        idx = content.find(first_line)
        return idx
    
    def _similarity(self, a: str, b: str) -> float:
        """计算字符串相似度"""
        return difflib.SequenceMatcher(None, a, b).ratio()
    
    def _generate_diff(self, original: str, modified: str) -> str:
        """生成统一 diff"""
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            orig_lines, mod_lines,
            fromfile='original', tofile='modified',
            n=3
        )
        return ''.join(diff)
    
    def _backup_file(self, file_path: str) -> str:
        """备份文件"""
        os.makedirs(self.backup_dir, exist_ok=True)
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        basename = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{basename}.{timestamp}.bak")
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _check_syntax(self, file_path: str) -> Tuple[bool, str]:
        """检查 Python 语法"""
        import py_compile
        try:
            py_compile.compile(file_path, doraise=True)
            return True, ""
        except py_compile.PyCompileError as e:
            return False, str(e)
    
    def patch_multiple(self, file_path: str, replacements: List[Dict]) -> Dict:
        """
        批量补丁
        
        Args:
            replacements: [{"old": "...", "new": "..."}, ...]
        """
        if not os.path.exists(file_path):
            return {"success": False, "message": f"文件不存在: {file_path}"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        
        modified = original
        applied = []
        failed = []
        
        for rep in replacements:
            old_str = rep.get("old", "")
            new_str = rep.get("new", "")
            
            if old_str in modified:
                modified = modified.replace(old_str, new_str, 1)
                applied.append({"old": old_str[:30], "status": "ok"})
            else:
                failed.append({"old": old_str[:30], "reason": "not_found"})
        
        if applied:
            backup = self._backup_file(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)
            
            diff = self._generate_diff(original, modified)
            return {
                "success": True,
                "applied": applied,
                "failed": failed,
                "diff": diff,
                "backup_path": backup
            }
        
        return {"success": False, "message": "无匹配项", "failed": failed}


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_patch_engine = None

def get_patch_engine() -> PatchEngine:
    global _patch_engine
    if _patch_engine is None:
        _patch_engine = PatchEngine()
    return _patch_engine

```
