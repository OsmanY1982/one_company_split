# `planetarium/core/modules/intelligence/agent_bridge/agent_bridge_models.py`

> 路径：`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_models.py` | 行数：229


---


```python
"""AgentBridge 模型管理 Mixin（从 agent_bridge.py 拆出）

提供模型查询、切换、配置持久化能力。
AgentBridge 继承本 Mixin 后即可获得 get_model / switch_model 等方法。
"""

import os
import json


class AgentBridgeModelMixin:
    """模型管理：配置读取/持久化、模型列表、模型切换"""

    # ── 类级别配置路径（staticmethod，不依赖实例）──

    @staticmethod
    def _config_path() -> str:
        """iqra_config.json 的绝对路径"""
        # __file__: .../core/modules/intelligence/agent_bridge/agent_bridge_models.py
        # 向上 4 级到项目根目录（core/）
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "iqra", "data", "iqra_config.json"
        )

    @staticmethod
    def _load_config() -> dict:
        """加载 iqra_config.json"""
        try:
            cfg_path = AgentBridgeModelMixin._config_path()
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"cloud_providers": {}, "local_providers": {}}

    @staticmethod
    def _save_config(config_dict: dict):
        """持久化 iqra_config.json"""
        try:
            cfg_path = AgentBridgeModelMixin._config_path()
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AgentBridge] 保存配置失败: {e}")

    def get_model(self) -> str:
        """获取当前使用的模型名"""
        return getattr(self.backend.config, "model", "") if hasattr(self.backend, "config") else ""

    def get_provider_info(self) -> dict:
        """获取当前供应商信息"""
        if hasattr(self.backend, "config"):
            cfg = self.backend.config
            return {
                "model": getattr(cfg, "model", ""),
                "provider_type": getattr(cfg, "provider_type", ""),
                "base_url": getattr(cfg, "base_url", ""),
                "name": getattr(cfg, "name", ""),
            }
        return {}

    @staticmethod
    def list_all_models() -> list:
        """
        从 iqra_config.json 读取所有已配置的模型（云端+自定义+本地+Ollama动态发现）。
        返回: [{"provider_id": str, "provider_name": str, "model": str, "category": str, "base_url": str}, ...]
          category: "cloud" | "local"
        """
        config = AgentBridgeModelMixin._load_config()
        models = []

        # 云端供应商
        for pid, pdata in config.get("cloud_providers", {}).items():
            pname = pdata.get("name", pid)
            model = pdata.get("model", "")
            base_url = pdata.get("base_url", "")
            if model:
                models.append({
                    "provider_id": pid,
                    "provider_name": pname,
                    "model": model,
                    "category": "cloud",
                    "base_url": base_url,
                })

        # 本地供应商
        for pid, pdata in config.get("local_providers", {}).items():
            pname = pdata.get("name", pid)
            model = pdata.get("model", "")
            base_url = pdata.get("base_url", "")

            # 本地 provider：通过 /v1/models 动态发现模型
            if base_url and "localhost" in base_url:
                discovered = AgentBridgeModelMixin.discover_local_models()
                if discovered:
                    for m in discovered:
                        models.append({
                            "provider_id": pid,
                            "provider_name": pname,
                            "model": m["name"],
                            "category": "local",
                            "base_url": base_url,
                            "size": m.get("size", 0),
                        })
                    continue  # 跳过静态 model 字段

            if model:
                models.append({
                    "provider_id": pid,
                    "provider_name": pname,
                    "model": model,
                    "category": "local",
                    "base_url": base_url,
                })

        return models

    @staticmethod
    def discover_local_models() -> list:
        """自动发现本地 provider 已加载的模型（从配置读取 base_url）"""
        try:
            import urllib.request
            import urllib.parse
            config = AgentBridgeModelMixin._load_config()
            # 从本地 provider 配置中取第一个有效的 base_url
            base_url = ""
            provider_type = ""
            for _pid, pdata in config.get("local_providers", {}).items():
                url = pdata.get("base_url", "")
                if url:
                    base_url = url
                    provider_type = pdata.get("provider_type", "")
                    break
            if not base_url:
                base_url = "http://localhost:8080/v1"

            # Ollama 用 /api/tags，其他用 /v1/models
            if "11434" in base_url or "ollama" in provider_type.lower():
                # Ollama 的 /api/tags 在根路径，不在 base_url 的 /v1 下
                parsed = urllib.parse.urlparse(base_url)
                origin = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 11434}"
                endpoint = urllib.parse.urljoin(origin + "/", "api/tags")
            else:
                endpoint = urllib.parse.urljoin(base_url.rstrip("/") + "/", "models")

            resp = urllib.request.urlopen(endpoint, timeout=5)
            data = json.loads(resp.read())

            # Ollama 返回 {"models": [{"name": "...", ...}]}
            if "models" in data:
                models = data["models"]
                if models and "name" in models[0]:
                    return [{"name": m["name"], "size": m.get("size", 0)} for m in models]

            # OpenAI 兼容格式返回 {"data": [{"id": "...", ...}]}
            return [
                {"name": m["id"], "size": 0}
                for m in data.get("data", [])
            ]
        except Exception:
            return []

    def switch_model(self, provider_id: str, model: str) -> bool:
        """
        切换模型：从 iqra_config.json 查找供应商配置，
        更新 backend config（name/base_url/api_key/model/provider_type），
        重建 ChatEngine 保留对话历史。
        """
        if not hasattr(self.backend, "config"):
            return False

        config = AgentBridgeModelMixin._load_config()
        provider_data = (
            config.get("cloud_providers", {}).get(provider_id)
            or config.get("local_providers", {}).get(provider_id)
        )
        if not provider_data:
            print(f"[AgentBridge] 未找到供应商: {provider_id}")
            return False

        old_model = self.get_model()
        old_messages = self._engine.messages
        cfg = self.backend.config

        # 更新 backend config 全部字段
        cfg.name = provider_data.get("name", provider_id)
        cfg.base_url = provider_data.get("base_url", "")
        cfg.api_key = provider_data.get("api_key", "")
        cfg.model = model
        cfg.provider_type = provider_data.get("provider_type", "openai_compatible")

        # 重建 ChatEngine，继承对话历史
        from iqra.core.chat_engine import ChatEngine
        from iqra.core.agent_loop import AgentLoop

        self._engine = ChatEngine(
            backend=self.backend,
            registry=self.registry,
            system_prompt=self._build_system_prompt(""),
            memory_store=self._memory,
            auto_save=True,
            session_id=self.session_id,
        )
        self._engine.messages = old_messages
        self._agent_loop = AgentLoop(
            engine=self._engine,
            max_iterations=50,
            max_retries=3,
            timeout_seconds=900,
            verbose=True,
        )

        # ── 持久化当前模型选择，重启后自动恢复 ──
        is_cloud = provider_id in config.get("cloud_providers", {})
        is_local = provider_id in config.get("local_providers", {})
        config["active_provider_id"] = provider_id
        if is_cloud:
            config["active_provider_type"] = "cloud"
            config["cloud_providers"][provider_id]["model"] = model
        elif is_local:
            config["active_provider_type"] = "local"
            config["local_providers"][provider_id]["model"] = model
        AgentBridgeModelMixin._save_config(config)

        print(f"[AgentBridge] 模型切换: {old_model} → {model} (供应商: {cfg.name})")
        return True

```
