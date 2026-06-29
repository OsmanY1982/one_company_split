# `core/modules/auth/model_config_panel/_panel_config.py`

> 路径：`core/modules/auth/model_config_panel/_panel_config.py` | 行数：84


---


```python
"""
模型配置面板 — 配置构建与操作 Mixin。
"""
from PyQt5.QtWidgets import QMessageBox

from ._constants import PRESET_PROVIDERS, LOCAL_SERVICES, _save_iqra_config


class _PanelConfigMixin:
    """Mixin: 配置构建、保存、跳过、引擎重初始化。"""

    def _get_config(self) -> dict:
        active_tab = self._stack.currentIndex()
        config = {
            "active_provider_id": "",
            "active_provider_type": "",
            "cloud_providers": {},
            "local_providers": {},
        }
        if active_tab == 0:  # 预设模式
            pid = self._preset_provider.currentData()
            key = self._preset_key.text().strip()
            model = self._preset_model.currentText().strip() or self._preset_model.currentData() or ""
            provider = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
            if not provider:
                return None
            config["active_provider_id"] = pid
            config["active_provider_type"] = "cloud"
            config["cloud_providers"][pid] = {
                "name": provider["name"],
                "provider_type": "openai_compatible",
                "base_url": provider["base_url"],
                "api_key": key,
                "model": model,
            }
        elif active_tab == 1:  # 自定义模式
            url = self._custom_inputs["custom_url"].text().strip()
            key = self._custom_inputs["custom_key"].text().strip()
            model = self._custom_inputs["custom_model"].currentText().strip()
            if not url or not model:
                QMessageBox.warning(self, "参数缺失", "请填写 API Base URL 和模型名称")
                return None
            config["active_provider_id"] = "custom"
            config["active_provider_type"] = "cloud"
            config["cloud_providers"]["custom"] = {
                "name": "自定义 OpenAI 兼容",
                "provider_type": "openai_compatible",
                "base_url": url,
                "api_key": key,
                "model": model,
            }
        elif active_tab == 2:  # 本地模式
            sid = self._local_service.currentData()
            url = self._local_url.text().strip()
            model = self._local_model.currentData() or self._local_model.currentText().strip() or ""
            svc = next((s for s in LOCAL_SERVICES if s["id"] == sid), None)
            if not svc:
                return None
            config["active_provider_id"] = sid
            config["active_provider_type"] = "local"
            config["local_providers"][sid] = {
                "name": svc["name"],
                "provider_type": "openai_compatible",
                "base_url": url,
                "model": model,
                "api_key": "",
            }
        return config

    def _on_action(self):
        config = self._get_config()
        if config is None:
            return
        _save_iqra_config(config)
        self.config_saved.emit(config)

    def _skip(self):
        """跳过配置（仅 standalone 模式）"""
        config = {"active_provider_id": "", "active_provider_type": "none"}
        self.config_saved.emit(config)

    def _reinit_engine(self, config: dict):
        """已废弃 — 旧版引擎初始化方法，当前架构下不再使用。"""
        pass

```
