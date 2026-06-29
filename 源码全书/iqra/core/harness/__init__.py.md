# `iqra/core/harness/__init__.py`

> 路径：`iqra/core/harness/__init__.py` | 行数：278


---


```python
"""
Harness — iqra Agent 设计器核心

提供 Agent 配置的加载、保存、验证、热应用、克隆、列表等核心功能。
配置文件统一存储于项目根目录的 config/agents/ 下，支持 YAML 和 JSON 格式。

Usage:
    from iqra.core.harness import load_agent_config, save_agent_config, list_agents

    config = load_agent_config("my_agent")
    save_agent_config(config, "my_agent")
    agents = list_agents()
"""

import os
import json
import re
import shutil
from typing import List, Dict, Any, Optional, Tuple

from .config_schema import AgentConfig, MemoryConfig, ModelConfig, TriggerConfig

# ── 配置目录 ──
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONFIG_DIR = os.path.join(_project_root, "config", "agents")
os.makedirs(_CONFIG_DIR, exist_ok=True)


# ═══════════════════════════════════════════
# 核心 API
# ═══════════════════════════════════════════

def load_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """加载 Agent 配置文件。

    优先查找 .yaml/.yml，其次 .json。

    Args:
        agent_id: Agent 标识名（与文件名对应，不含扩展名）

    Returns:
        AgentConfig 对象，不存在则返回 None
    """
    for ext in (".yaml", ".yml", ".json"):
        path = os.path.join(_CONFIG_DIR, f"{agent_id}{ext}")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                if ext.endswith((".yaml", ".yml")):
                    import yaml
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)
            return AgentConfig.from_dict(data)
    return None


def save_agent_config(config: AgentConfig, config_path: Optional[str] = None) -> str:
    """保存 Agent 配置到文件。

    若 config_path 未指定，自动使用 agent_name 作为文件名存入 config/agents/。

    Args:
        config: AgentConfig 对象
        config_path: 可选，完整文件路径（若提供则忽略 agent_name）

    Returns:
        写入的文件路径
    """
    if config_path:
        filepath = config_path
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    else:
        _validate_agent_id(config.agent_name)
        filepath = os.path.join(_CONFIG_DIR, f"{config.agent_name}.yaml")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(config.to_yaml())

    return filepath


def list_agents() -> List[str]:
    """列出所有已配置的 Agent 名称（不含扩展名）。"""
    agents = set()
    if not os.path.isdir(_CONFIG_DIR):
        return []
    for fname in os.listdir(_CONFIG_DIR):
        name, ext = os.path.splitext(fname)
        if ext.lower() in (".yaml", ".yml", ".json"):
            agents.add(name)
    return sorted(agents)


def delete_agent(agent_id: str) -> bool:
    """删除 Agent 配置。

    Args:
        agent_id: Agent 标识名

    Returns:
        是否成功删除
    """
    for ext in (".yaml", ".yml", ".json"):
        path = os.path.join(_CONFIG_DIR, f"{agent_id}{ext}")
        if os.path.exists(path):
            os.remove(path)
            return True
    return False


def clone_agent(agent_id: str, new_name: str) -> Optional[AgentConfig]:
    """克隆 Agent 配置。

    Args:
        agent_id: 源 Agent 名称
        new_name: 新 Agent 名称

    Returns:
        克隆后的 AgentConfig，源不存在则返回 None
    """
    src = load_agent_config(agent_id)
    if src is None:
        return None
    src.agent_name = new_name
    src.description = f"[克隆自 {agent_id}] {src.description}"
    save_agent_config(src)
    return src


def apply_config(agent_id: str, config: AgentConfig) -> Dict[str, Any]:
    """热应用配置到运行中的 Agent。

    此方法委托给 engine 层的 `harness_apply_agent` 工具实现。
    此处仅做预验证和状态记录。

    Args:
        agent_id: 目标 Agent 标识
        config: AgentConfig 对象

    Returns:
        {"status": "ok", "agent_id": agent_id} 或 {"status": "error", "errors": [...]}
    """
    errors = validate_config(config)
    if errors:
        return {"status": "error", "errors": errors, "agent_id": agent_id}

    # 保存配置
    path = save_agent_config(config)

    return {
        "status": "ok",
        "agent_id": agent_id,
        "path": path,
        "message": f"Agent '{agent_id}' 配置已保存到 {path}，需重启或重新加载引擎以生效。",
    }


def validate_config(config: AgentConfig) -> List[str]:
    """验证 Agent 配置完整性。

    Args:
        config: AgentConfig 对象

    Returns:
        错误列表，空列表表示通过
    """
    return config.validate()


def get_config_path(agent_id: str) -> Optional[str]:
    """获取 Agent 配置文件的完整路径。"""
    for ext in (".yaml", ".yml", ".json"):
        path = os.path.join(_CONFIG_DIR, f"{agent_id}{ext}")
        if os.path.exists(path):
            return path
    return None


# ═══════════════════════════════════════════
# 工具/Skill/模型 枚举（供 UI 调用）
# ═══════════════════════════════════════════

def get_available_tools() -> List[Dict[str, str]]:
    """获取引擎可用工具列表（名称 + 描述）。

    从 ToolRegistry 全局实例中动态读取；若不可用则返回静态内置列表。
    """
    try:
        from iqra.core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        tools = []
        for entry in registry.list_all():
            tools.append({
                "name": entry.get("name", ""),
                "description": entry.get("description", ""),
                "category": entry.get("category", "general"),
            })
        if tools:
            return sorted(tools, key=lambda t: t.get("category", ""))
    except Exception:
        pass

    # 兜底：内置核心工具列表
    return [
        {"name": "read_file", "description": "读取文件内容", "category": "file"},
        {"name": "write_file", "description": "写入文件", "category": "file"},
        {"name": "edit_file", "description": "编辑文件", "category": "file"},
        {"name": "search_files", "description": "搜索文件", "category": "file"},
        {"name": "execute_shell", "description": "执行 Shell 命令", "category": "system"},
        {"name": "web_search", "description": "网络搜索", "category": "web"},
        {"name": "web_fetch_page", "description": "抓取网页", "category": "web"},
        {"name": "git_operation", "description": "Git 操作", "category": "vc"},
        {"name": "audit_codebase", "description": "代码审计", "category": "code"},
        {"name": "audit_module", "description": "模块审计", "category": "code"},
    ]


def get_available_skills() -> List[Dict[str, str]]:
    """获取引擎可用技能列表。"""
    try:
        from iqra.core.skill_system import SkillSystem
        ss = SkillSystem()
        result = [{"name": s, "description": ""} for s in ss.list_skills()]
        if result:
            return result
    except Exception:
        pass

    try:
        from iqra.core.skill_loader import SkillLoader
        sl = SkillLoader()
        skills = []
        for s in sl.list_all():
            skills.append({
                "name": s.get("name", ""),
                "description": s.get("description", ""),
            })
        return skills if skills else _static_skills()
    except Exception:
        return _static_skills()


def _static_skills():
    return [
        {"name": "excel-processing-and-analysis", "description": "Excel 处理与分析"},
        {"name": "pdf", "description": "PDF 操作"},
        {"name": "docx", "description": "Word 文档操作"},
        {"name": "pptx", "description": "PPT 演示文稿操作"},
        {"name": "image-search", "description": "图片语义搜索"},
        {"name": "file-search", "description": "文档语义搜索"},
        {"name": "file-organizer", "description": "文件整理"},
        {"name": "invoice-retrieval", "description": "发票检索"},
        {"name": "document-writer", "description": "文档撰写"},
        {"name": "chart-visualization", "description": "图表可视化"},
    ]


def get_available_models() -> List[str]:
    """获取可用模型列表。"""
    try:
        from iqra.core.llm_backend import BaseLLMBackend
        return BaseLLMBackend.list_models()
    except Exception:
        return [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
            "claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku",
            "gemini-2.0-flash", "gemini-1.5-pro",
            "deepseek-v3", "deepseek-r1",
        ]


# ═══════════════════════════════════════════
# 内部辅助
# ═══════════════════════════════════════════

def _validate_agent_id(agent_id: str):
    if not agent_id or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', agent_id):
        raise ValueError(f"无效的 Agent 名称: '{agent_id}'，只能包含字母、数字、下划线和连字符")

```
