# `iqra/core/skill_system.py`

> 路径：`iqra/core/skill_system.py` | 行数：235


---


```python
"""
Iqra 技能系统 — SKILL.md 动态加载与路由

提供:
- SKILL.md 解析
- 技能自动发现
- 智能匹配路由
- 技能执行引擎
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    version: str
    emoji: str
    tools: List[str]
    content: str
    capabilities: List[str]
    workflow: List[str]
    examples: List[str]
    file_path: str
    linked_files: Dict[str, List[str]] = None  # references, templates, scripts


@dataclass
class SkillMatch:
    """技能匹配结果"""
    skill: Skill
    confidence: float
    reason: str


class SkillSystem:
    """技能管理系统"""
    
    _DEFAULT_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "iqra", "skills")

    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir or self._DEFAULT_SKILLS_DIR
        self.skills: Dict[str, Skill] = {}
        self._load_all_skills()
    
    def _load_all_skills(self):
        """加载所有技能"""
        skills_path = Path(self.skills_dir)
        if not skills_path.exists():
            skills_path.mkdir(parents=True, exist_ok=True)
            return
        
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    self._load_skill(skill_file)
    
    def _load_skill(self, file_path: Path):
        """加载单个技能"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 解析 YAML frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
            else:
                frontmatter = {}
                body = content
            
            # 扫描关联文件
            linked_files = self._scan_linked_files(file_path.parent)
            
            skill = Skill(
                name=frontmatter.get('name', file_path.parent.name),
                description=frontmatter.get('description', ''),
                version=frontmatter.get('version', '1.0'),
                emoji=frontmatter.get('emoji', ''),
                tools=frontmatter.get('tools', []),
                content=body,
                capabilities=self._extract_section(body, 'Capabilities'),
                workflow=self._extract_section(body, 'Workflow'),
                examples=self._extract_section(body, 'Examples'),
                file_path=str(file_path),
                linked_files=linked_files
            )
            
            self.skills[skill.name] = skill
            
        except Exception as e:
            print(f"⚠️ 加载技能失败 {file_path}: {e}")
    
    def _scan_linked_files(self, skill_dir: Path) -> Dict[str, List[str]]:
        """扫描关联文件"""
        linked = {"references": [], "templates": [], "scripts": []}
        
        for subdir in ["references", "templates", "scripts"]:
            dir_path = skill_dir / subdir
            if dir_path.exists() and dir_path.is_dir():
                for f in dir_path.iterdir():
                    if f.is_file():
                        linked[subdir].append(str(f.relative_to(skill_dir)))
        
        return linked
    
    def _extract_section(self, body: str, section_name: str) -> List[str]:
        """提取 Markdown 章节内容"""
        lines = body.split('\n')
        result = []
        in_section = False
        
        for line in lines:
            if line.startswith('## ') and section_name.lower() in line.lower():
                in_section = True
                continue
            elif line.startswith('## '):
                in_section = False
            elif in_section and line.strip():
                if line.startswith('- ') or line.startswith('* '):
                    result.append(line[2:].strip())
                elif not line.startswith('#'):
                    result.append(line.strip())
        
        return result
    
    def match(self, query: str, top_k: int = 3) -> List[SkillMatch]:
        """匹配查询到最相关的技能"""
        if not self.skills:
            return []
        
        scores = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for skill in self.skills.values():
            score = 0.0
            reasons = []
            
            # 名称匹配
            if skill.name.lower() in query_lower:
                score += 0.4
                reasons.append(f"名称匹配 '{skill.name}'")
            
            # 描述匹配
            if skill.description and any(w in skill.description.lower() for w in query_words):
                score += 0.3
                reasons.append("描述关键词匹配")
            
            # 能力匹配
            for cap in skill.capabilities:
                if any(w in cap.lower() for w in query_words):
                    score += 0.2
                    reasons.append(f"能力匹配 '{cap[:20]}...'")
                    break
            
            # 工具匹配
            for tool in skill.tools:
                if tool.lower() in query_lower:
                    score += 0.15
                    reasons.append(f"工具匹配 '{tool}'")
                    break
            
            if score > 0:
                scores.append(SkillMatch(
                    skill=skill,
                    confidence=min(score, 1.0),
                    reason="; ".join(reasons)
                ))
        
        # 按置信度排序
        scores.sort(key=lambda x: x.confidence, reverse=True)
        return scores[:top_k]
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def load_linked_file(self, skill_name: str, file_path: str) -> Optional[str]:
        """加载技能关联文件"""
        skill = self.skills.get(skill_name)
        if not skill or not skill.linked_files:
            return None
        
        # 检查文件是否在关联文件中
        for category in ["references", "templates", "scripts"]:
            linked_files = skill.linked_files.get(category, [])
            for linked_file in linked_files:
                if linked_file == file_path:
                    # 读取文件内容
                    full_path = os.path.join(os.path.dirname(skill.file_path), category, file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            return f.read()
        
        return None
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有技能"""
        return [
            {
                "name": s.name,
                "description": s.description,
                "emoji": s.emoji,
                "version": s.version
            }
            for s in self.skills.values()
        ]
    
    def reload(self):
        """重新加载所有技能"""
        self.skills.clear()
        self._load_all_skills()


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_skill_system = None

def get_skill_system(skills_dir: str = None) -> SkillSystem:
    """获取技能系统单例"""
    global _skill_system
    if _skill_system is None:
        _skill_system = SkillSystem(skills_dir)
    return _skill_system

```
