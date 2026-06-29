# `iqra/core/obscura_provider.py`

> 路径：`iqra/core/obscura_provider.py` | 行数：717


---


```python
"""
Obscura 浏览器提供者 — 为 iqra 提供 headless browser 后端。

两种内部模式：
  1. CLI 模式（默认）：obscura fetch / scrape 子命令，轻量高效
  2. CDP 模式（高级）：obscura serve + WebSocket CDP 协议，精细控制

所有网页工具优先走 Obscura，不可用时自动回退 httpx。

依赖：
  - obscura 二进制（/Volumes/D盘工作区/工具/obscura/obscura 或系统 PATH）
  - websocket-client（CDP 模式）
  - httpx（回退模式）

Author: iqra + obscura integration
Version: 1.1
"""

import os
import sys
import json
import time
import signal
import atexit
import logging
import subprocess
import threading
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ── Obscura 二进制路径 ──
_OBSCURA_CANDIDATES = [
    "/Volumes/D盘工作区/工具/obscura/obscura",
    os.path.expanduser("~/obscura/obscura"),
    os.path.expanduser("~/.local/bin/obscura"),
    "obscura",
]


def _find_obscura_binary() -> Optional[str]:
    for candidate in _OBSCURA_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    try:
        result = subprocess.run(
            ["which", "obscura"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


OBSCURA_BIN = _find_obscura_binary()


def is_obscura_available() -> bool:
    return OBSCURA_BIN is not None


# ── CDP 客户端（WebSocket）─ ─


class _CDPConnection:
    """单个 WebSocket CDP 连接的低层收发封装。"""

    def __init__(self, ws_url: str, timeout: float = 30.0):
        self.ws_url = ws_url
        self.timeout = timeout
        self._ws = None
        self._msg_id = 0
        self._lock = threading.Lock()
        self._pending: Dict[int, Dict] = {}

    def connect(self) -> bool:
        try:
            import websocket
            self._ws = websocket.create_connection(self.ws_url, timeout=self.timeout)
            self._recv_thread = threading.Thread(
                target=self._recv_loop, daemon=True, name="cdp-recv"
            )
            self._recv_thread.start()
            return True
        except Exception as e:
            logger.warning(f"CDP 连接失败 ({self.ws_url}): {e}")
            return False

    def _recv_loop(self):
        import websocket
        while self._ws:
            try:
                msg = self._ws.recv()
                if not msg:
                    break
                data = json.loads(msg)
                msg_id = data.get("id")
                if msg_id and msg_id in self._pending:
                    self._pending[msg_id]["result"] = data
                    self._pending[msg_id]["event"].set()
            except (websocket.WebSocketConnectionClosedException, OSError, Exception):
                break

    def send(self, method: str, params: dict = None) -> dict:
        import websocket
        if not self._ws:
            raise RuntimeError("CDP 未连接")

        with self._lock:
            self._msg_id += 1
            msg_id = self._msg_id

        payload = {"id": msg_id, "method": method, "params": params or {}}
        event = threading.Event()
        self._pending[msg_id] = {"event": event, "result": None}

        try:
            self._ws.send(json.dumps(payload))
        except Exception as e:
            self._pending.pop(msg_id, None)
            raise RuntimeError(f"CDP 发送失败: {e}")

        if not event.wait(timeout=self.timeout):
            self._pending.pop(msg_id, None)
            raise TimeoutError(f"CDP 命令超时: {method}")

        result = self._pending.pop(msg_id, None)
        if result is None:
            raise RuntimeError("CDP 响应丢失")

        data = result["result"]
        if "error" in data:
            raise RuntimeError(f"CDP 错误: {data['error']}")
        return data.get("result", {})

    def close(self):
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None


class CDPClient:
    """Chrome DevTools Protocol 客户端。

    Obscura CDP 有两层 WebSocket：
      - Browser 级：ws://127.0.0.1:9222/devtools/browser（Target 管理）
      - Page 级：  ws://127.0.0.1:9222/devtools/page/{pageId}（页面操作）

    本客户端内部管理两层连接，对外暴露统一的 navigate / evaluate 接口。
    """

    def __init__(self, ws_url: str, timeout: float = 30.0):
        self.browser_url = ws_url
        self.timeout = timeout
        self._browser: Optional[_CDPConnection] = None
        self._page: Optional[_CDPConnection] = None
        self._page_id: Optional[str] = None

    def connect(self) -> bool:
        self._browser = _CDPConnection(self.browser_url, self.timeout)
        if not self._browser.connect():
            return False
        # 创建新页面 Target
        try:
            result = self._browser.send("Target.createTarget", {"url": "about:blank"})
            self._page_id = result.get("targetId", "")
        except Exception:
            # 如果 createTarget 不支持，使用已有的第一个页面
            try:
                targets = self._browser.send("Target.getTargets", {})
                for t in targets.get("targetInfos", []):
                    if t.get("type") == "page":
                        self._page_id = t.get("targetId", "")
                        break
            except Exception:
                pass

        if not self._page_id:
            raise RuntimeError("CDP: 无法获取页面 Target")

        # 连接页面级 WebSocket
        page_url = self.browser_url.replace("/devtools/browser", f"/devtools/page/{self._page_id}")
        self._page = _CDPConnection(page_url, self.timeout)
        if not self._page.connect():
            raise RuntimeError("CDP: 无法连接页面 WebSocket")

        # 启用必要 domain
        self._page.send("Page.enable")
        self._page.send("Runtime.enable")
        return True

    def navigate(self, url: str, wait_until: str = "load") -> dict:
        if not self._page:
            raise RuntimeError("CDP 未连接")
        return self._page.send("Page.navigate", {"url": url})

    def evaluate(self, expression: str) -> Any:
        if not self._page:
            raise RuntimeError("CDP 未连接")
        result = self._page.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        rr = result.get("result", {})
        if rr.get("type") == "string":
            return rr.get("value", "")
        if rr.get("subtype") == "error":
            return f"[Error] {rr.get('description', '')}"
        return rr.get("value", rr.get("description", ""))

    def get_text(self) -> str:
        return self.evaluate("document.body ? document.body.innerText : ''") or ""

    def get_html(self) -> str:
        return self.evaluate("document.documentElement.outerHTML") or ""

    def close(self):
        if self._page:
            self._page.close()
            self._page = None
        if self._browser:
            self._browser.close()
            self._browser = None


# ── Obscura 进程管理器（serve 模式）─ ─


class ObscuraServer:
    """管理 Obscura serve 进程生命周期。"""

    _instance: Optional["ObscuraServer"] = None

    def __init__(
        self,
        port: int = 9222,
        stealth: bool = True,
        host: str = "127.0.0.1",
        workers: int = 2,
        quiet: bool = True,
    ):
        self.port = port
        self.stealth = stealth
        self.host = host
        self.workers = workers
        self.quiet = quiet
        self._process: Optional[subprocess.Popen] = None
        self._started = False

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}/devtools/browser"

    @property
    def http_base(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> bool:
        if not OBSCURA_BIN:
            logger.error("Obscura 二进制未找到")
            return False
        if self._started:
            return True

        cmd = [
            OBSCURA_BIN, "serve",
            "--port", str(self.port),
            "--host", self.host,
            "--workers", str(self.workers),
        ]
        if self.stealth:
            cmd.append("--stealth")
        if self.quiet:
            cmd.append("--quiet")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL if self.quiet else None,
                stderr=subprocess.DEVNULL if self.quiet else None,
                stdin=subprocess.DEVNULL,
                preexec_fn=os.setsid if sys.platform != "win32" else None,
            )
        except Exception as e:
            logger.error(f"启动 Obscura serve 失败: {e}")
            return False

        for _ in range(30):
            time.sleep(0.1)
            if self._check_ready():
                self._started = True
                logger.info(f"Obscura serve started on port {self.port}")
                return True

        logger.error("Obscura serve 启动超时")
        self.stop()
        return False

    def _check_ready(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.http_base}/json/version")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                return "webSocketDebuggerUrl" in data
        except Exception:
            return False

    def stop(self):
        if self._process:
            try:
                if sys.platform == "win32":
                    self._process.terminate()
                else:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
        self._started = False
        logger.info("Obscura serve stopped")

    def create_cdp_client(self) -> CDPClient:
        client = CDPClient(self.ws_url)
        if not client.connect():
            raise RuntimeError("无法连接到 CDP 端点")
        return client

    @classmethod
    def get_instance(
        cls, port: int = 9222, stealth: bool = True, auto_start: bool = True
    ) -> Optional["ObscuraServer"]:
        if cls._instance is None:
            cls._instance = cls(port=port, stealth=stealth)
            if auto_start:
                if cls._instance.start():
                    atexit.register(cls._instance.stop)
                else:
                    cls._instance = None
        return cls._instance


# ── Obscura Provider ──


class ObscuraProvider:
    """Obscura 浏览器提供者 — 统一网页抓取接口。

    后端优先级：obscura CLI → httpx 回退
    """

    def __init__(
        self,
        stealth: bool = True,
        timeout: int = 30,
        wait: int = 3,
        user_agent: Optional[str] = None,
    ):
        self.stealth = stealth
        self.timeout = timeout
        self.wait = wait
        self.user_agent = user_agent
        self._available = is_obscura_available()

    @property
    def available(self) -> bool:
        return self._available

    # ── 核心抓取 ──

    def fetch(
        self,
        url: str,
        eval_js: Optional[str] = None,
        selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """抓取单个网页。

        - 不带 eval_js：返回页面文本内容（title + body text）
        - 带 eval_js：直接返回 eval 结果
        - selector：进一步限定提取范围
        """
        if not self._available:
            return self._fallback_fetch(url)

        user_eval = bool(eval_js)

        if eval_js:
            eval_expr = eval_js
        else:
            eval_expr = (
                "JSON.stringify({"
                "title: document.title,"
                "text: (document.body ? document.body.innerText : '').substring(0, 10000)"
                "})"
            )

        if selector:
            eval_expr = (
                "JSON.stringify({"
                "title: document.title,"
                "text: (function(){"
                f"  var el = document.querySelector('{selector}');"
                "  return el ? el.innerText : document.body ? document.body.innerText : '';"
                "})().substring(0, 10000)"
                "})"
            )

        return self._fetch_with_eval(url, eval_expr, user_eval=user_eval)

    def fetch_html(self, url: str) -> Dict[str, Any]:
        """抓取完整 HTML（JS 渲染后）。"""
        if not self._available:
            return self._fallback_fetch(url)

        eval_expr = (
            "JSON.stringify({"
            "title: document.title,"
            "html: document.documentElement.outerHTML.substring(0, 50000)"
            "})"
        )
        return self._fetch_with_eval(url, eval_expr)

    def _fetch_with_eval(self, url: str, eval_expr: str, user_eval: bool = False) -> Dict[str, Any]:
        """底层：用 obscura fetch --eval 抓取。

        user_eval=True 时，stdout 直接存为 eval_result（用户自定义 JS 返回值）。
        """
        cmd = [
            OBSCURA_BIN, "fetch",
            "--wait", str(self.wait),
            "--timeout", str(self.timeout),
            "--eval", eval_expr,
            "--quiet",
        ]
        if self.stealth:
            cmd.append("--stealth")
        if self.user_agent:
            cmd.extend(["--user-agent", self.user_agent])
        cmd.append(url)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,
            )
        except subprocess.TimeoutExpired:
            return {"url": url, "error": "抓取超时", "backend": "obscura"}

        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()

        # 从 stderr 解析标题
        title = ""
        for line in stderr.split("\n"):
            if "Page loaded:" in line:
                parts = line.split(" - ", 2)
                if len(parts) >= 3:
                    title = parts[2].strip('"').strip()
                elif len(parts) >= 2 and not parts[1].startswith("http"):
                    title = parts[1].strip('"').strip()
                break

        # 用户自定义 eval：raw stdout 就是结果
        if user_eval:
            eval_result = stdout
            try:
                parsed = json.loads(stdout)
                eval_result = parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return {
                "url": url,
                "title": title,
                "content": "",
                "chars": 0,
                "backend": "obscura",
                "eval_result": eval_result,
            }

        # 默认模式：stdout 是 {title, text} JSON
        content = ""
        try:
            data = json.loads(stdout)
            content = data.get("text", data.get("html", ""))
            if not title:
                title = data.get("title", "")
        except (json.JSONDecodeError, TypeError):
            content = stdout[:10000]

        resp = {
            "url": url,
            "title": title,
            "content": content,
            "chars": len(content),
            "backend": "obscura",
        }
        return resp

    # ── 批量抓取 ──

    def batch_scrape(
        self,
        urls: List[str],
        eval_js: Optional[str] = None,
        concurrency: int = 5,
    ) -> Dict[str, Any]:
        """批量抓取多个网页。"""
        if not self._available:
            return self._fallback_batch_scrape(urls)

        eval_expr = eval_js or "document.title"

        cmd = [
            OBSCURA_BIN, "scrape",
            "--concurrency", str(concurrency),
            "--timeout", str(self.timeout),
            "--format", "json",
            "--eval", eval_expr,
        ]
        cmd.extend(urls)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=(self.timeout + 10) * max(1, len(urls) // concurrency or 1),
            )
        except subprocess.TimeoutExpired:
            return {"error": "批量抓取超时", "backend": "obscura"}

        stdout = result.stdout.strip()
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return {
                "error": "JSON 解析失败",
                "raw": stdout[:500],
                "backend": "obscura",
            }

        results = data.get("results", [])
        success_count = sum(
            1 for r in results if r.get("eval") is not None
        )

        formatted = []
        for r in results:
            furl = r.get("url", "")
            formatted.append({
                "url": furl,
                "title": r.get("title", ""),
                "content": r.get("eval", ""),
                "eval_result": r.get("eval"),
                "time_ms": r.get("time_ms", 0),
                "backend": "obscura",
            })

        return {
            "total": len(urls),
            "success": success_count,
            "failed": len(results) - success_count,
            "results": formatted,
            "total_time_ms": data.get("total_time_ms", 0),
            "backend": "obscura",
        }

    # ── 回退机制 ──

    def _fallback_fetch(self, url: str) -> Dict[str, Any]:
        try:
            import httpx
            headers = {
                "User-Agent": self.user_agent
                or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                html = resp.text

                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self._skip = False

                    def handle_starttag(self, tag, attrs):
                        if tag in ("script", "style", "noscript"):
                            self._skip = True

                    def handle_endtag(self, tag):
                        if tag in ("script", "style", "noscript"):
                            self._skip = False

                    def handle_data(self, data):
                        if not self._skip:
                            t = data.strip()
                            if t:
                                self.text.append(t)

                ex = TextExtractor()
                ex.feed(html)
                content = "\n".join(ex.text)

                return {
                    "url": url,
                    "content": content[:8000],
                    "chars": len(content),
                    "backend": "httpx",
                }
        except Exception as e:
            return {"url": url, "error": str(e), "backend": "httpx"}

    def _fallback_batch_scrape(self, urls: List[str]) -> Dict[str, Any]:
        results = []
        for url in urls:
            results.append(self._fallback_fetch(url))
        success = sum(1 for r in results if "error" not in r)
        return {
            "total": len(urls),
            "success": success,
            "failed": len(urls) - success,
            "results": results,
            "backend": "httpx",
        }


# ── 全局单例 ──

_provider: Optional[ObscuraProvider] = None


def get_provider(
    stealth: bool = True,
    timeout: int = 30,
    wait: int = 3,
) -> ObscuraProvider:
    global _provider
    if _provider is None:
        _provider = ObscuraProvider(stealth=stealth, timeout=timeout, wait=wait)
    return _provider


def fetch_page(url: str, eval_js: Optional[str] = None) -> Dict[str, Any]:
    return get_provider().fetch(url, eval_js=eval_js)


def batch_fetch(
    urls: List[str],
    eval_js: Optional[str] = None,
    concurrency: int = 5,
) -> Dict[str, Any]:
    return get_provider().batch_scrape(urls, eval_js=eval_js, concurrency=concurrency)


# ════════════════════════════════════════════
# 测试
# ════════════════════════════════════════════

if __name__ == "__main__":
    print("ObscuraProvider 测试")
    print("=" * 50)
    print(f"Obscura 二进制: {OBSCURA_BIN}")
    print(f"是否可用: {is_obscura_available()}")

    if not is_obscura_available():
        print("Obscura 不可用，跳过测试")
        sys.exit(1)

    provider = ObscuraProvider(stealth=True, timeout=15, wait=2)

    # 测试 1: 基本抓取
    print("\n[测试 1] 抓取 example.com")
    result = provider.fetch("https://www.example.com")
    print(f"  标题: {result.get('title', 'N/A')}")
    print(f"  内容预览: {(result.get('content', '') or '')[:100]}")
    print(f"  后端: {result.get('backend')}")

    # 测试 2: 自定义 eval
    print("\n[测试 2] 自定义 eval")
    result = provider.fetch(
        "https://www.example.com",
        eval_js="JSON.stringify({title: document.title, links: document.querySelectorAll('a').length})"
    )
    print(f"  结果: {result.get('eval_result', 'N/A')}")

    # 测试 3: Stealth
    print("\n[测试 3] Stealth 验证")
    result = provider.fetch(
        "https://www.example.com",
        eval_js="JSON.stringify({webdriver: navigator.webdriver, plugins: navigator.plugins.length})"
    )
    print(f"  检测: {result.get('eval_result', 'N/A')}")

    # 测试 4: 批量
    print("\n[测试 4] 批量抓取")
    result = provider.batch_scrape(
        ["https://www.example.com", "https://httpbin.org/ip"],
        eval_js="document.title",
        concurrency=2,
    )
    print(f"  成功: {result.get('success')}/{result.get('total')}")
    for r in result.get("results", []):
        print(f"    - {r.get('url', '?')}: {r.get('title', 'N/A')}")

```
