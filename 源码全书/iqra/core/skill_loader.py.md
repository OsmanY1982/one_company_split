# `iqra/core/skill_loader.py`

> 路径：`iqra/core/skill_loader.py` | 行数：372


---


```python
"""
Skill Loader - 动态加载技能系统

将 SKILL.md 文档转换为 LLM 可调用的知识和工具描述。
支持:
- 自动发现所有 skills
- 根据用户请求智能推荐相关技能
- 生成技能上下文注入 prompt
- 兼容两种技能格式：iqra 自有格式（YAML frontmatter）和 Anthropic Skills 格式（metadata.yaml）
"""

import os
import re
import yaml
from typing import List, Dict, Optional
from pathlib import Path


class SkillLoader:
    """技能加载器 - 管理所有 SKILL.md 文件

    支持两种技能格式，自动识别：
    1. iqra 自有格式：SKILL.md 内嵌 YAML frontmatter
    2. Anthropic Skills 格式：独立的 metadata.yaml + SKILL.md（纯正文）
    """

    def __init__(self, skills_base_path: str = None):
        """
        Args:
            skills_base_path: 技能目录路径，默认尝试多个位置
        """
        if skills_base_path:
            self.skills_path = Path(skills_base_path)
        else:
            # 尝试多个可能的位置（支持多种路径格式）
            possible_paths = [
                Path(__file__).parent.parent / "iqra" / "skills",
                Path.cwd() / "iqra" / "skills",
                Path.cwd() / "skills",
                Path(__file__).parent.parent / "skills",  # 项目相对路径（跨平台）
                Path.home() / "Library" / "Application Support" / "Iqra" / "skills",  # macOS
                Path.home() / ".iqra" / "skills",
            ]
            self.skills_path = next((p for p in possible_paths if p.exists()), None)

        if not self.skills_path or not self.skills_path.exists():
            # 最后尝试：直接打印可用路径供调试
            print(f"⚠️ 技能目录未找到，已检查:")
            for p in possible_paths:
                exists = "✅" if p.exists() else "❌"
                print(f"   {exists} {p}")
            raise FileNotFoundError(f"技能目录不存在：{self.skills_path}")

        self._skills_cache: Dict[str, Dict] = {}
        self._load_all_skills()

    def _load_all_skills(self):
        """扫描并加载所有 SKILL.md"""
        for skill_md in self.skills_path.rglob("*/SKILL.md"):
            skill_name = skill_md.parent.name.replace("_", "-")
            try:
                skill_data = self._parse_skill_file(skill_md)
                if skill_data:
                    self._skills_cache[skill_name] = skill_data
                    self._skills_cache[skill_md.parent.stem] = skill_data  # 也存带下划线的名字
            except Exception as e:
                print(f"加载技能 {skill_md} 失败：{e}")

    def _parse_skill_file(self, filepath: Path) -> Optional[Dict]:
        """解析单个 SKILL.md 文件。

        自动识别格式：
        - 若同级目录存在 metadata.yaml → Anthropic Skills 格式
        - 否则 → iqra 自有格式（YAML frontmatter）
        """
        content = filepath.read_text(encoding='utf-8')

        # === 检测 Anthropic Skills 格式（metadata.yaml） ===
        metadata_yaml = filepath.parent / "metadata.yaml"
        if not metadata_yaml.exists():
            metadata_yaml = filepath.parent / "metadata.yml"

        if metadata_yaml.exists():
            return self._parse_anthropic_skill(filepath, metadata_yaml, content)

        # === iqra 自有格式（YAML frontmatter） ===
        return self._parse_iqra_skill(filepath, content)

    def _parse_anthropic_skill(
        self, filepath: Path, metadata_yaml: Path, sk_content: str
    ) -> Optional[Dict]:
        """解析 Anthropic Skills 格式：metadata.yaml + SKILL.md（纯正文无 frontmatter）。

        metadata.yaml 示例::

            name: my-skill
            version: "1.0.0"
            description: "A cool skill"
            tools: [read, write]
            triggers: [keyword1, keyword2]
            platforms: [linux, macos, windows]
        """
        try:
            metadata = yaml.safe_load(metadata_yaml.read_text(encoding='utf-8')) or {}
        except yaml.YAMLError:
            return None
        if not isinstance(metadata, dict):
            return None

        # Anthropic 格式的 SKILL.md 不含 frontmatter，全文即为 body
        body = sk_content.strip()

        # 构建与 iqra 格式一致的输出结构，兼容下游调用
        name = metadata.get("name", filepath.parent.name)

        return {
            "name": name,
            "description": metadata.get("description", ""),
            "version": str(metadata.get("version", "1.0")),
            "emoji": metadata.get("emoji", "📚"),
            "tools": metadata.get("tools", []),
            "path": str(filepath),
            "directory": str(filepath.parent),
            "full_content": sk_content,
            "body": body,
            "metadata": metadata,
            # Anthropic 特有字段（不影响现有代码，供将来扩展用）
            "format": "anthropic",
            "triggers": metadata.get("triggers", []),
            "platforms": metadata.get("platforms", []),
        }

    def _parse_iqra_skill(self, filepath: Path, content: str) -> Optional[Dict]:
        """解析 iqra 自有格式：SKILL.md 内嵌 YAML frontmatter。"""
        yaml_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not yaml_match:
            return None

        metadata = yaml.safe_load(yaml_match.group(1)) or {}
        body = content[yaml_match.end():].strip()

        return {
            "name": metadata.get("name", filepath.parent.name),
            "description": metadata.get("description", ""),
            "version": str(metadata.get("version", "1.0")),
            "emoji": metadata.get("emoji", "📚"),
            "tools": metadata.get("tools", []),
            "path": str(filepath),
            "directory": str(filepath.parent),
            "full_content": content,
            "body": body,
            "metadata": metadata,
            "format": "iqra",
        }
    
    def list_skills(self) -> List[Dict]:
        """列出所有已加载的技能（去重）"""
        seen = set()
        result = []
        for skill in self._skills_cache.values():
            name = skill.get("name", "")
            path = skill.get("path", "")
            key = (name, path)  # 按名称+路径去重
            if key not in seen:
                seen.add(key)
                result.append(skill)
        return result
    
    def get_skill(self, name: str) -> Optional[Dict]:
        """获取指定技能的详细信息"""
        # 尝试多种名称匹配方式
        variations = [
            name,
            name.replace("-", "_"),
            name.replace("_", "-"),
            name.lower(),
        ]
        for variant in variations:
            if variant in self._skills_cache:
                return self._skills_cache[variant]
        return None
    
    def search_skills(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        根据查询关键词搜索相关技能
        
        使用简单的关键词匹配，可升级为语义搜索
        """
        query_lower = query.lower()
        keywords = self._extract_keywords(query_lower)
        
        scored_skills = []
        for skill in self._skills_cache.values():
            score = self._calculate_relevance_score(skill, keywords)
            if score > 0:
                scored_skills.append((score, skill))
        
        # 按分数排序，返回前 k 个
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored_skills[:top_k]]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单分词）"""
        # 中文 + 英文混合分词
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z_][a-zA-Z0-9_]*', text)
        return [w for w in words if len(w) > 1]  # 过滤单字
    
    def _calculate_relevance_score(self, skill: Dict, keywords: List[str]) -> float:
        """计算技能与关键词的相关性得分"""
        score = 0.0
        searchable_text = f"{skill['name']} {skill['description']}".lower()
        
        for keyword in keywords:
            if keyword in searchable_text:
                score += 2.0  # 在元数据中匹配，权重高
            if keyword in skill.get('body', '').lower():
                score += 1.0  # 在正文中匹配，权重低
        
        return score
    
    def get_skill_context(self, skill_name: str, include_full: bool = False) -> str:
        """
        生成技能的 prompt 上下文
        
        Args:
            skill_name: 技能名称
            include_full: 是否包含完整内容（默认为 False，仅返回摘要）
        
        Returns:
            Markdown 格式的上下文文本
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return f"❌ 未找到技能：{skill_name}"
        
        if include_full:
            return skill['full_content']
        
        # 生成精简版上下文
        lines = [
            f"## 📖 技能：{skill['emoji']} {skill['name']}",
            f"**描述**: {skill['description']}",
            f"**版本**: {skill['version']}",
            f"**可用工具**: {', '.join(skill.get('tools', [])) or '无'}",
            "",
            "---",
            "",
        ]
        
        # 提取正文的前 500 字符作为预览
        body_preview = skill.get('body', '')[:500]
        if len(skill.get('body', '')) > 500:
            body_preview += "\n\n... (内容截断，需要时可提供完整技能)"
        
        lines.append(body_preview)
        
        return "\n".join(lines)
    
    def build_skills_prompt(self, related_skills: List[Dict], user_query: str) -> str:
        """
        构建包含相关技能的完整 prompt
        
        Args:
            related_skills: 相关技能列表
            user_query: 用户原始查询（用于提供上下文）
        
        Returns:
            完整的技能上下文 prompt
        """
        if not related_skills:
            return ""
        
        sections = [
            "══════════════════════════════════════════",
            "📚 已加载相关技能知识",
            f"根据你的问题「{user_query}」，以下技能可能对你有帮助:",
            "",
        ]
        
        for i, skill in enumerate(related_skills, 1):
            sections.append(self.get_skill_context(skill['name'], include_full=False))
            sections.append("")
            sections.append("---")
            sections.append("")
        
        sections.append(
            "💡 提示：你可以参考以上技能的模板、方法和建议来完成任务。\n"
            "如果需要查看某个技能的完整内容，可以明确要求调用该技能。"
        )
        
        return "\n".join(sections)
    
    def auto_select_skills_for_query(self, user_query: str, max_count: int = 3) -> List[Dict]:
        """
        自动为用户查询选择最相关的技能
        
        Args:
            user_query: 用户的查询
            max_count: 最多返回的技能数量
        
        Returns:
            排序后的技能列表
        """
        return self.search_skills(user_query, top_k=max_count)
    
    def get_all_skill_summaries(self) -> str:
        """获取所有技能的简要列表（用于菜单或帮助）"""
        lines = ["# 📚 可用技能列表", ""]
        
        # 按首字母分组
        grouped = {}
        for skill in self._skills_cache.values():
            first_char = skill['emoji']
            if first_char not in grouped:
                grouped[first_char] = []
            grouped[first_char].append(skill)
        
        for emoji, skills in sorted(grouped.items()):
            lines.append(f"### {emoji}")
            for skill in sorted(skills, key=lambda s: s['name']):
                lines.append(f"- **{skill['name']}**: {skill['description']}")
            lines.append("")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def create_skill_loader(base_path: str = None) -> SkillLoader:
    """创建技能加载器实例"""
    return SkillLoader(base_path)


def load_skills_for_query(query: str, base_path: str = None, 
                          max_skills: int = 3) -> tuple[List[Dict], str]:
    """
    为给定查询加载相关技能
    
    Returns:
        (技能列表，prompt 上下文)
    """
    loader = SkillLoader(base_path)
    skills = loader.auto_select_skills_for_query(query, max_count=max_skills)
    context = loader.build_skills_prompt(skills, query)
    return skills, context


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.insert(0, "/d/one_company_desktop")
    
    loader = SkillLoader()
    
    print("=== 所有技能 ===")
    print(loader.get_all_skill_summaries())
    
    print("\n=== 搜索测试 ===")
    test_queries = [
        "帮我写一封邮件给客户",
        "分析销售数据",
        "代码审查",
        "翻译文档",
    ]
    
    for query in test_queries:
        print(f"\n查询：{query}")
        skills = loader.search_skills(query, top_k=2)
        for s in skills:
            print(f"  → {s['emoji']} {s['name']}: {s['description']}")

```
