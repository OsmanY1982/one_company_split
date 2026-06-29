# `iqra/core/harness/config_schema.py`

> 路径：`iqra/core/harness/config_schema.py` | 行数：172


---


```python
"""
Harness — iqra Agent 配置 Schema

定义 Agent 的 tool / skill / prompt / memory 配置数据模型及验证逻辑。
"""

import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════
# 子配置数据类
# ═══════════════════════════════════════════

@dataclass
class MemoryConfig:
    """记忆配置"""
    type: str = "short_term"          # short_term / long_term / rag / buffered
    max_tokens: int = 4096            # 最大 token 数
    ttl: int = 3600                   # 存活时间（秒），0=永久

    def validate(self) -> List[str]:
        errors = []
        allowed = {"short_term", "long_term", "rag", "buffered"}
        if self.type not in allowed:
            errors.append(f"memory.type 必须是 {allowed} 之一，当前: '{self.type}'")
        if self.max_tokens < 256:
            errors.append(f"memory.max_tokens 不能小于 256，当前: {self.max_tokens}")
        if self.ttl < 0:
            errors.append(f"memory.ttl 不能为负数，当前: {self.ttl}")
        return errors


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str = "gpt-4o"        # 模型名
    temperature: float = 0.7          # 温度
    max_tokens: int = 262144           # 最大输出 token

    def validate(self) -> List[str]:
        errors = []
        if not self.model_name or not self.model_name.strip():
            errors.append("model.model_name 不能为空")
        if not (0.0 <= self.temperature <= 2.0):
            errors.append(f"model.temperature 必须在 0.0-2.0 之间，当前: {self.temperature}")
        if self.max_tokens < 128:
            errors.append(f"model.max_tokens 不能小于 128，当前: {self.max_tokens}")
        return errors


@dataclass
class TriggerConfig:
    """触发条件配置"""
    event: str                        # 事件类型: on_startup / on_message / on_schedule / on_file_change
    condition: str = ""               # 触发条件表达式
    action: str = ""                  # 触发动作

    def validate(self) -> List[str]:
        errors = []
        allowed = {"on_startup", "on_message", "on_schedule", "on_file_change"}
        if self.event not in allowed:
            errors.append(f"trigger.event 必须是 {allowed} 之一，当前: '{self.event}'")
        return errors


# ═══════════════════════════════════════════
# 主配置数据类
# ═══════════════════════════════════════════

@dataclass
class AgentConfig:
    """Agent 完整配置"""
    agent_name: str = ""
    description: str = ""
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)       # 工具白名单
    skills: List[str] = field(default_factory=list)       # 技能列表
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    permissions: List[str] = field(default_factory=list)  # 权限列表
    triggers: List[TriggerConfig] = field(default_factory=list)

    # ── 引擎注册表引用（验证时注入）──
    _known_tools: Optional[set] = field(default=None, repr=False)
    _known_skills: Optional[set] = field(default=None, repr=False)
    _known_models: Optional[set] = field(default=None, repr=False)

    def validate(self) -> List[str]:
        """验证配置完整性，返回错误列表（空列表表示通过）"""
        errors = []

        # 必填字段
        if not self.agent_name or not self.agent_name.strip():
            errors.append("agent_name 不能为空")
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', self.agent_name):
            errors.append("agent_name 只能包含字母、数字、下划线和连字符，且以字母或下划线开头")

        if not self.system_prompt or not self.system_prompt.strip():
            errors.append("system_prompt 不能为空")

        # 子配置验证
        errors.extend(self.memory.validate())
        errors.extend(self.model.validate())

        # 触发条件验证
        for i, trigger in enumerate(self.triggers):
            for e in trigger.validate():
                errors.append(f"triggers[{i}].{e}")

        # 工具白名单验证
        if self._known_tools is not None and self.tools:
            unknown = [t for t in self.tools if t not in self._known_tools]
            if unknown:
                errors.append(f"未知工具: {', '.join(unknown)}")

        # 技能验证
        if self._known_skills is not None and self.skills:
            unknown = [s for s in self.skills if s not in self._known_skills]
            if unknown:
                errors.append(f"未知技能: {', '.join(unknown)}")

        # 模型名验证
        if self._known_models is not None and self.model.model_name:
            if self.model.model_name not in self._known_models:
                errors.append(f"未知模型: '{self.model.model_name}'")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """序列化为纯字典"""
        d = {
            "agent_name": self.agent_name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "skills": self.skills,
            "memory": asdict(self.memory),
            "model": asdict(self.model),
            "permissions": self.permissions,
            "triggers": [asdict(t) for t in self.triggers],
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """从字典反序列化"""
        memory = MemoryConfig(**data.get("memory", {}))
        model = ModelConfig(**data.get("model", {}))
        triggers = [TriggerConfig(**t) for t in data.get("triggers", [])]
        return cls(
            agent_name=data.get("agent_name", ""),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            memory=memory,
            model=model,
            permissions=data.get("permissions", []),
            triggers=triggers,
        )

    def to_yaml(self) -> str:
        """导出为 YAML 格式字符串（使用 PyYAML）"""
        try:
            import yaml
            return yaml.dump(self.to_dict(), default_flow_style=False,
                             allow_unicode=True, sort_keys=False)
        except ImportError:
            import json
            return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

```
