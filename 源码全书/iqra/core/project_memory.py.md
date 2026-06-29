# `iqra/core/project_memory.py`

> 路径：`iqra/core/project_memory.py` | 行数：485


---


```python
# -*- coding: utf-8 -*-
"""
项目记忆系统 — .iqra.md + .iqra/memory.json

对标 CLAUDE.md + Codex Memory 设计：

  项目根目录
  ├── .iqra.md              ← 项目级记忆（提交 Git）
  │   ├── 技术栈
  │   ├── 代码规范
  │   ├── 架构决策
  │   └── 常用命令
  │
  └── .iqra/
      ├── memory.json       ← 个人偏好（本地，不提交）
      │   ├── 命名习惯
      │   ├── 偏好模型
      │   └── 权限设置
      │
      └── sessions/         ← 会话存档

用法:
    pm = ProjectMemory()
    pm.scan_up(os.getcwd())              # 向上扫描找项目根目录
    context = pm.load_context()           # 获取注入上下文
    pm.write_entry("代码规范", "使用 snake_case")  # 写入记忆
    pm.suggest("用户命名", "考虑用 camelCase")     # 自动建议
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .iqra_logging import logger

# ── 配置 ──

PROJECT_MEMORY_FILE = ".iqra.md"
PERSONAL_MEMORY_DIR = ".iqra"
PERSONAL_MEMORY_FILE = "memory.json"
SESSION_DIR = "sessions"

MEMORY_SECTION_DELIMITERS = ["# ", "## ", "### "]  # Markdown 标题作为 section 边界

AUTOSUGGEST_CONFIRMATION_THRESHOLD = 3  # 连续 N 次同类操作 → 建议记忆


@dataclass
class MemorySection:
    """记忆条目：.iqra.md 中的一个 ## 段落"""
    title: str
    content: str
    line_start: int = 0
    line_end: int = 0


@dataclass
class PersonalMemory:
    """个人偏好（.iqra/memory.json 的内容）"""
    naming_style: str = ""
    preferred_model: str = ""
    permissions: str = "ask"  # restricted / ask / auto
    custom_entries: Dict[str, str] = field(default_factory=dict)
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "naming_style": self.naming_style,
            "preferred_model": self.preferred_model,
            "permissions": self.permissions,
            "custom_entries": self.custom_entries,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PersonalMemory":
        return cls(
            naming_style=d.get("naming_style", ""),
            preferred_model=d.get("preferred_model", ""),
            permissions=d.get("permissions", "ask"),
            custom_entries=d.get("custom_entries", {}),
            last_updated=d.get("last_updated", ""),
        )

    def has_any(self) -> bool:
        """是否有任何非默认偏好"""
        return bool(
            self.naming_style
            or self.preferred_model
            or self.permissions != "ask"
            or self.custom_entries
        )


class ProjectMemory:
    """
    项目记忆管理器

    职责：
      1. 向上扫描目录树定位项目根目录（找 .iqra.md 或 .git）
      2. 加载 .iqra.md 和 .iqra/memory.json
      3. 提供记忆写入接口（write_entry / write_personal / suggest）
      4. 生成注入到 system prompt 的上下文块
    """

    def __init__(self, start_dir: str = None):
        self._project_root: Optional[str] = None
        self._project_md_path: Optional[str] = None
        self._personal_dir: Optional[str] = None
        self._personal_json_path: Optional[str] = None
        self._sections: List[MemorySection] = []
        self._personal: PersonalMemory = PersonalMemory()

        if start_dir:
            self.scan_up(start_dir)

    # ── 项目根目录扫描 ──

    def scan_up(self, start_dir: str) -> Optional[str]:
        """
        从 start_dir 向上扫描，寻找项目根目录。

        判定依据（优先级递减）：
          1. 存在 .iqra.md
          2. 存在 .git 目录
          3. 存在 .iqra/ 目录
          4. 走到文件系统根为止，以 start_dir 的最近父目录作为根

        Returns:
            项目根目录路径，未找到返回 None
        """
        current = os.path.abspath(start_dir)

        while True:
            iqra_md = os.path.join(current, PROJECT_MEMORY_FILE)
            git_dir = os.path.join(current, ".git")
            iqra_dir = os.path.join(current, PERSONAL_MEMORY_DIR)

            if os.path.isfile(iqra_md):
                self._set_root(current, iqra_md)
                logger.info("ProjectMemory: 找到项目根 %s (by .iqra.md)", current)
                return current

            parent = os.path.dirname(current)
            if parent == current:
                # 到达文件系统根，无项目标记 — 回退到 start_dir 父目录
                fallback = os.path.dirname(os.path.abspath(start_dir))
                # 确保 start_dir 本身可以用作"项目根"
                if os.path.isfile(os.path.join(start_dir, PROJECT_MEMORY_FILE)):
                    self._set_root(start_dir, os.path.join(start_dir, PROJECT_MEMORY_FILE))
                    return start_dir
                if os.path.isdir(start_dir):
                    # 视为无项目根的普通目录
                    self._set_root(start_dir, os.path.join(start_dir, PROJECT_MEMORY_FILE))
                    return start_dir
                return None

            if os.path.isdir(git_dir) or os.path.isdir(iqra_dir):
                # .git 或 .iqra/ 存在但无 .iqra.md → 自动创建空的 .iqra.md
                auto_md = os.path.join(current, PROJECT_MEMORY_FILE)
                self._set_root(current, auto_md)
                logger.info("ProjectMemory: 找到项目根 %s (by .git/.iqra，自动创建 .iqra.md)", current)
                return current

            current = parent

    def _set_root(self, root_dir: str, md_path: str):
        """设置项目根并初始化路径"""
        self._project_root = root_dir
        self._project_md_path = md_path
        self._personal_dir = os.path.join(root_dir, PERSONAL_MEMORY_DIR)
        self._personal_json_path = os.path.join(self._personal_dir, PERSONAL_MEMORY_FILE)
        os.makedirs(self._personal_dir, exist_ok=True)

    @property
    def project_root(self) -> Optional[str]:
        return self._project_root

    @property
    def has_project(self) -> bool:
        return self._project_root is not None

    # ── 加载 ──

    def load_context(self) -> str:
        """
        加载全部项目记忆上下文，返回注入到 system prompt 的文本块。

        如果 .iqra.md 不存在，自动创建空的模板文件。

        Returns:
            格式化的上下文文本，无内容时返回空字符串
        """
        if not self._project_root:
            return ""

        parts = []

        # 1. 加载 .iqra.md
        md_content = self._load_project_md()
        if md_content:
            parts.append(md_content)

        # 2. 加载 .iqra/memory.json 个人偏好
        personal = self._load_personal()
        if personal.has_any():
            parts.append(self._format_personal(personal))
            self._personal = personal

        if not parts:
            return ""

        return "\n\n".join(parts)

    def _load_project_md(self) -> str:
        """读取 .iqra.md 内容并解析 sections"""
        self._sections = []

        if not self._project_md_path:
            return ""

        # 如果文件不存在，自动创建一个空模板
        if not os.path.isfile(self._project_md_path):
            self._init_empty_project_md()
            return ""

        try:
            with open(self._project_md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.warning("ProjectMemory: 读取 .iqra.md 失败: %s", e)
            return ""

        if not content.strip():
            return ""

        # 解析 sections
        self._parse_sections(content)

        return content.strip()

    def _parse_sections(self, content: str):
        """解析 Markdown 内容为 MemorySection 列表"""
        lines = content.split("\n")
        current_title = ""
        current_content: List[str] = []
        current_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                # 保存上一段
                if current_title:
                    self._sections.append(MemorySection(
                        title=current_title,
                        content="\n".join(current_content).strip(),
                        line_start=current_start,
                        line_end=i - 1,
                    ))
                current_title = stripped[3:].strip()
                current_content = []
                current_start = i
            else:
                if current_title:
                    current_content.append(line)

        # 最后一段
        if current_title:
            self._sections.append(MemorySection(
                title=current_title,
                content="\n".join(current_content).strip(),
                line_start=current_start,
                line_end=len(lines) - 1,
            ))

    def _init_empty_project_md(self):
        """创建空的 .iqra.md 模板文件"""
        if not self._project_md_path:
            return
        try:
            template = (
                "# 项目记忆\n\n"
                "<!-- 此文件随 Git 提交，记录项目级约定 -->\n\n"
                "## 技术栈\n\n\n"
                "## 代码规范\n\n\n"
                "## 架构决策\n\n\n"
                "## 常用命令\n\n"
            )
            with open(self._project_md_path, "w", encoding="utf-8") as f:
                f.write(template)
            logger.info("ProjectMemory: 自动创建 %s", self._project_md_path)
        except Exception as e:
            logger.warning("ProjectMemory: 创建 .iqra.md 失败: %s", e)

    def _load_personal(self) -> PersonalMemory:
        """加载 .iqra/memory.json"""
        if not self._personal_json_path or not os.path.isfile(self._personal_json_path):
            return PersonalMemory()

        try:
            with open(self._personal_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PersonalMemory.from_dict(data)
        except Exception as e:
            logger.warning("ProjectMemory: 读取 memory.json 失败: %s", e)
            return PersonalMemory()

    def _format_personal(self, p: PersonalMemory) -> str:
        """格式化个人偏好为注入文本"""
        lines = ["## 个人偏好"]
        if p.naming_style:
            lines.append(f"- 命名风格: {p.naming_style}")
        if p.preferred_model:
            lines.append(f"- 偏好模型: {p.preferred_model}")
        lines.append(f"- 权限级别: {p.permissions}")
        for key, val in p.custom_entries.items():
            lines.append(f"- {key}: {val}")
        return "\n".join(lines)

    # ── 写入 ──

    def write_entry(self, section_title: str, content: str, mode: str = "replace") -> bool:
        """
        写入项目记忆条目到 .iqra.md。

        Args:
            section_title: 段落标题（## 后的文字）
            content: 段落内容
            mode: "replace"（替换同名段落）| "append"（追加到段落末尾）

        Returns:
            是否写入成功
        """
        if not self._project_md_path:
            logger.warning("ProjectMemory: 未设置项目根，无法写入")
            return False

        # 确保文件存在
        if not os.path.isfile(self._project_md_path):
            self._init_empty_project_md()

        # 重新加载
        self._load_project_md()

        # 查找同名 section
        existing = None
        for s in self._sections:
            if s.title == section_title:
                existing = s
                break

        if existing and mode == "replace":
            return self._replace_section(existing, content)
        elif existing:
            return self._append_to_section(existing, content)
        else:
            return self._add_section(section_title, content)

    def _replace_section(self, section: MemorySection, new_content: str) -> bool:
        try:
            with open(self._project_md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 定位 section 内容行范围
            content_start = section.line_start + 1  # 标题下一行
            content_end = section.line_end + 1 if section.line_end < len(lines) else len(lines)

            new_lines = [
                f"## {section.title}\n",
                new_content.rstrip() + "\n",
                "\n",
            ]
            result = lines[:section.line_start] + new_lines + lines[content_end:]

            with open(self._project_md_path, "w", encoding="utf-8") as f:
                f.writelines(result)

            logger.info("ProjectMemory: 更新 '%s' 章节", section.title)
            return True
        except Exception as e:
            logger.warning("ProjectMemory: 替换章节失败: %s", e)
            return False

    def _append_to_section(self, section: MemorySection, content: str) -> bool:
        try:
            with open(self._project_md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            insert_at = section.line_end + 1 if section.line_end < len(lines) else len(lines)
            lines.insert(insert_at, content.rstrip() + "\n")
            with open(self._project_md_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            logger.info("ProjectMemory: 追加到 '%s' 章节", section.title)
            return True
        except Exception as e:
            logger.warning("ProjectMemory: 追加章节失败: %s", e)
            return False

    def _add_section(self, title: str, content: str) -> bool:
        try:
            with open(self._project_md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines.append(f"\n## {title}\n")
            lines.append(content.rstrip() + "\n")
            with open(self._project_md_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            logger.info("ProjectMemory: 新增 '%s' 章节", title)
            return True
        except Exception as e:
            logger.warning("ProjectMemory: 新增章节失败: %s", e)
            return False

    def write_personal(self, key: str, value: str) -> bool:
        """
        写入个人偏好到 .iqra/memory.json。

        Args:
            key: 预定义键名之一
              - naming_style: 命名风格
              - preferred_model: 偏好模型
              - permissions: 权限级别
              - 其他自定义键 → 存入 custom_entries
            value: 键值
        """
        if not self._personal_json_path:
            return False

        # 加载当前值
        self._personal = self._load_personal()

        predefined = {"naming_style", "preferred_model", "permissions"}
        if key in predefined:
            setattr(self._personal, key, value)
        else:
            self._personal.custom_entries[key] = value

        self._personal.last_updated = datetime.now().isoformat()

        try:
            os.makedirs(self._personal_dir, exist_ok=True)
            with open(self._personal_json_path, "w", encoding="utf-8") as f:
                json.dump(self._personal.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info("ProjectMemory: 写入个人偏好 '%s'='%s'", key, value)
            return True
        except Exception as e:
            logger.warning("ProjectMemory: 写入 memory.json 失败: %s", e)
            return False

    # ── 自动建议 ──

    def suggest(self, topic: str, hint: str, force: bool = False) -> Optional[str]:
        """
        自动建议记忆条目。仅当 force=True 时直接写入；
        否则返回建议文本，由调用方决定是否写入。

        Args:
            topic: 记忆主题（对应 ## 标题）
            hint: 建议内容

        Returns:
            建议文本字符串，供 UI 询问用户确认
        """
        suggestion = f"建议记忆：{topic}\n{hint}"

        if force:
            self.write_entry(topic, hint)
            return None

        return suggestion


def auto_detect_project_root(start_dir: str = None) -> Optional[str]:
    """
    便捷函数：自动检测项目根目录。

    从 start_dir（默认当前工作目录）向上扫描。

    Returns:
        项目根目录路径，未找到返回 None
    """
    pm = ProjectMemory()
    if start_dir:
        return pm.scan_up(start_dir)
    return pm.scan_up(os.getcwd())

```
