# `iqra/core/config_validator.py`

> 路径：`iqra/core/config_validator.py` | 行数：192


---


```python
# -*- coding: utf-8 -*-
"""
Iqra 配置校验模块
验证配置文件的完整性、一致性和合理性
"""
import json
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConfigValidationResult:
    """校验结果"""
    def __init__(self):
        self.ok = True
        self.errors = []
        self.warnings = []
        self.fixes = []

    def add_error(self, msg: str):
        self.ok = False
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_fix(self, msg: str):
        self.fixes.append(msg)

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"[ERROR] {len(self.errors)} error(s):")
            for e in self.errors:
                lines.append(f"   - {e}")
        if self.warnings:
            lines.append(f"[WARN] {len(self.warnings)} warning(s):")
            for w in self.warnings:
                lines.append(f"   - {w}")
        if self.fixes:
            lines.append(f"[FIX] {len(self.fixes)} auto-fix(es):")
            for f in self.fixes:
                lines.append(f"   - {f}")
        if self.ok and not self.fixes:
            lines.append("[OK] Config validation passed")
        return "\n".join(lines)


class ConfigValidator:
    REQUIRED_FIELDS = ["active_provider_id", "active_provider_type"]
    RECOMMENDED_FIELDS = {
        "general.max_tool_rounds": (int, 5, lambda v: 1 <= v <= 20),
        "general.font_size": (int, 14, lambda v: 10 <= v <= 30),
        "general.theme": (str, "light", lambda v: v in ("light", "dark")),
        "general.auto_save": (bool, True, None),
    }
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.data_dir = os.path.dirname(config_path)
        
    def load(self) -> dict:
        if not os.path.exists(self.config_path):
            logger.error(f"配置文件不存在: {self.config_path}")
            return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 JSON 格式错误: {e}")
            return {}
    
    def validate(self, config: dict = None) -> ConfigValidationResult:
        result = ConfigValidationResult()
        if not os.path.exists(self.config_path):
            result.add_error(f"配置文件不存在: {self.config_path}")
            return result
        if config is None:
            config = self.load()
        if not config:
            result.add_error("无法加载配置文件（JSON 解析失败或文件为空）")
            return result
        for field in self.REQUIRED_FIELDS:
            if field not in config or config[field] is None or config[field] == "":
                result.add_error(f"缺少必填配置项: {field}")
        if not result.ok:
            return result
        active_id = config.get("active_provider_id")
        active_type = config.get("active_provider_type")
        if active_type == "cloud" and "cloud_providers" in config:
            providers = config.get("cloud_providers", {})
            if active_id not in providers:
                result.add_error(f"active_provider_id='{active_id}' 在 cloud_providers 中不存在")
            else:
                self._validate_provider(providers[active_id], result, "cloud_providers")
        elif active_type == "local" and "local_providers" in config:
            providers = config.get("local_providers", {})
            if active_id not in providers:
                result.add_error(f"active_provider_id='{active_id}' 在 local_providers 中不存在")
            else:
                self._validate_provider(providers[active_id], result, "local_providers")
        for field_path, (field_type, default, validator_fn) in self.RECOMMENDED_FIELDS.items():
            parts = field_path.split(".")
            value = config
            for p in parts:
                if isinstance(value, dict):
                    value = value.get(p)
                else:
                    value = None
                    break
            if value is None:
                result.add_fix(f"缺少配置项 {field_path}，将使用默认值: {default}")
            elif not isinstance(value, field_type):
                result.add_warning(f"配置项 {field_path} 类型错误，期望 {field_type.__name__}，实际 {type(value).__name__}")
            elif validator_fn and not validator_fn(value):
                result.add_warning(f"配置项 {field_path} 的值不在合理范围内: {value}")
        disabled = config.get("disabled_skills", [])
        if not isinstance(disabled, list):
            result.add_warning(f"disabled_skills 应为列表，实际为 {type(disabled).__name__}")
        if active_type in ("cloud", "local") and active_id:
            providers = config.get(f"{active_type}_providers", {})
            if active_id in providers:
                provider = providers[active_id]
                api_key = provider.get("api_key", "")
                if not api_key:
                    result.add_warning(f"当前 Provider ({active_id}) 的 api_key 为空，AI 功能可能无法使用")
        return result
    
    def _validate_provider(self, provider: dict, result: ConfigValidationResult, provider_type: str):
        required = ["name", "provider_type", "base_url", "model"]
        for field in required:
            if not provider.get(field):
                result.add_error(f"Provider {provider.get('name', '?')} 缺少必填字段: {field}")
        base_url = provider.get("base_url", "")
        if base_url and not (base_url.startswith("http://") or base_url.startswith("https://")):
            result.add_error(f"Provider {provider.get('name')} 的 base_url 格式无效: {base_url}")
    
    def get_recommended_defaults(self) -> dict:
        return {
            "active_provider_id": "ollama",
            "active_provider_type": "local",
            "cloud_providers": {},
            "local_providers": {
                "ollama": {
                    "name": "Ollama (本地)",
                    "provider_type": "openai_compatible",
                    "base_url": "http://localhost:11434/v1",
                    "model": "qwen2.5:7b",
                    "api_key": ""
                }
            },
            "disabled_skills": [],
            "general": {
                "theme": "light",
                "auto_save": True,
                "max_tool_rounds": 5,
                "font_size": 14
            }
        }
    
    def apply_fixes(self, dry_run: bool = False) -> ConfigValidationResult:
        if self.config is None:
            self.config = self.load()
        result = self.validate(self.config)
        defaults = self.get_recommended_defaults()
        # 只补缺失的顶层 key，不覆盖已有数据（保护用户通过 UI 设置的本地/云端 provider 配置）
        _PROTECTED_KEYS = {"local_providers", "cloud_providers", "active_provider_id", "active_provider_type"}
        for key, default_value in defaults.items():
            if key not in self.config:
                self.config[key] = default_value
                result.add_fix(f"添加缺失配置项: {key}")
            elif key in _PROTECTED_KEYS:
                # 已有配置，不覆盖
                continue
            elif key == "general" and isinstance(default_value, dict):
                for sub_key, sub_value in default_value.items():
                    if sub_key not in self.config[key]:
                        self.config[key][sub_key] = sub_value
                        result.add_fix(f"添加缺失配置项: general.{sub_key}")
        if not dry_run and result.fixes:
            backup_path = self.config_path + ".bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            result.fixes.append(f"已保存到: {self.config_path}")
            result.fixes.append(f"备份到: {backup_path}")
        return result


```
