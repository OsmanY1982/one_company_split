# `core/modules/auth/model_config_panel/_workers.py`

> 路径：`core/modules/auth/model_config_panel/_workers.py` | 行数：65


---


```python
"""
模型配置面板 — 后台拉取线程。
"""
import json
import urllib.request
import urllib.parse
import ssl

from PyQt5.QtCore import QThread, pyqtSignal

from ._constants import _filter_usable_models


class _ManualModelFetcher(QThread):
    """后台线程：手动触发从 OpenAI 兼容端点获取可用模型列表。"""
    finished = pyqtSignal(list, str)  # (model_list, error_msg)

    def __init__(self, base_url: str, api_key: str = "", timeout: int = 15):
        super().__init__()
        self._base_url = base_url
        self._api_key = api_key
        self._timeout = timeout

    def run(self):
        try:
            from iqra.core.llm_backend import get_available_models
            raw = get_available_models(self._base_url, self._api_key, timeout=self._timeout)
            usable = _filter_usable_models(raw)
            self.finished.emit(usable, "")
        except Exception as e:
            self.finished.emit([], str(e))


class _OllamaModelFetcher(QThread):
    """后台线程：从 Ollama /api/tags 端点获取本地模型列表。"""
    finished = pyqtSignal(list, str)  # (model_list, error_msg)

    def __init__(self, base_url: str, timeout: int = 15):
        super().__init__()
        self._base_url = base_url
        self._timeout = timeout

    def run(self):
        try:
            parsed = urllib.parse.urlparse(self._base_url)
            origin = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 11434}"
            endpoint = urllib.parse.urljoin(origin + "/", "api/tags")

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(endpoint, method="GET")
            with urllib.request.urlopen(req, context=ctx, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                if name:
                    size = m.get("size", 0)
                    size_str = f" ({size / 1024 / 1024 / 1024:.1f}GB)" if size else ""
                    models.append(f"{name}{size_str}")
            self.finished.emit(models, "")
        except Exception as e:
            self.finished.emit([], str(e))

```
