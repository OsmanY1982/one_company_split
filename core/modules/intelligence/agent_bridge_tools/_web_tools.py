"""网络工具 Mixin：web_search / web_fetch_page / web_scrape / batch_scrape

v2.0 — Obscura 集成：
  - 所有网页抓取优先走 Obscura（JS 渲染 + stealth）
  - Obscura 不可用时自动回退 urllib/httpx
  - backend 参数控制后端选择：auto（默认）/ obscura / httpx
"""

import urllib.request
import urllib.parse
from html.parser import HTMLParser

from core.obscura_provider import get_provider

_DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def _resolve_backend(requested: str, provider) -> str:
    """解析 backend 参数：auto → obscura 优先，不可用则回退 httpx"""
    if requested == "obscura":
        if provider.available:
            return "obscura"
        return "httpx"
    if requested == "httpx":
        return "httpx"
    # auto
    return "obscura" if provider.available else "httpx"


class _WebToolsMixin:
    """网络工具注册"""

    # ── 11. web_search ──
    def _reg_web_search(self):
        def handler(query: str, max_results: int = 8, backend: str = "auto") -> dict:
            try:
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={"User-Agent": _DEFAULT_UA})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")

                class P(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._cur = {}
                        self._in_result = self._in_link = self._in_snippet = False

                    def handle_starttag(self, tag, attrs):
                        d = dict(attrs)
                        cls = d.get("class", "")
                        if tag == "div" and "result" in cls:
                            self._in_result = True
                            self._cur = {"title": "", "link": "", "snippet": ""}
                        if self._in_result and tag == "a" and "result__a" in cls:
                            self._in_link = True
                            self._cur["link"] = d.get("href", "")
                        if self._in_result and tag == "a" and "result__snippet" in cls:
                            self._in_snippet = True

                    def handle_endtag(self, tag):
                        if tag == "div" and self._cur:
                            self.results.append(self._cur)
                            self._cur = {}
                            self._in_result = False
                        if tag == "a":
                            self._in_link = self._in_snippet = False

                    def handle_data(self, data):
                        if self._in_link:
                            self._cur["title"] += data
                        if self._in_snippet:
                            self._cur["snippet"] += data

                parser = P()
                parser.feed(html)
                return {
                    "query": query,
                    "count": len(parser.results[:max_results]),
                    "results": parser.results[:max_results],
                    "backend": "httpx",
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="web_search",
            description="DuckDuckGo 网页搜索，获取实时信息",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 8},
                    "backend": {"type": "string", "description": "后端：auto/obscura/httpx", "default": "auto"},
                },
                "required": ["query"],
            },
            category="web",
        )(handler)

    # ── 12. web_fetch_page ──
    def _reg_web_fetch_page(self):
        def handler(url: str, backend: str = "auto") -> dict:
            provider = get_provider()
            actual = _resolve_backend(backend, provider)

            if actual == "obscura":
                try:
                    result = provider.fetch(url)
                    return {
                        "url": result.get("url", url),
                        "title": result.get("title", ""),
                        "chars": result.get("chars", 0),
                        "content": result.get("content", ""),
                        "backend": "obscura",
                    }
                except Exception:
                    pass

            # httpx / urllib 回退
            try:
                req = urllib.request.Request(url, headers={"User-Agent": _DEFAULT_UA})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")

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
                return {"url": url, "chars": len(content), "content": content[:8000], "backend": "httpx"}
            except Exception as e:
                return {"error": str(e), "backend": "httpx"}

        self.registry.register(
            name="web_fetch_page",
            description="抓取网页正文内容（优先 JS 渲染、反检测，自动回退纯文本）",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL（含 https://）"},
                    "backend": {"type": "string", "description": "后端：auto/obscura/httpx，auto 优先 Obscura", "default": "auto"},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12b. web_scrape ──
    def _reg_web_scrape(self):
        def handler(url: str, backend: str = "auto", max_paragraphs: int = 20) -> dict:
            provider = get_provider()
            actual = _resolve_backend(backend, provider)

            if actual == "obscura":
                try:
                    result = provider.fetch(url)
                    content = result.get("content", "")
                    title = result.get("title", "")
                    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
                    paragraphs = paragraphs[:max_paragraphs]
                    return {
                        "url": url,
                        "title": title,
                        "paragraphs": paragraphs,
                        "status": "success",
                        "backend": "obscura",
                    }
                except Exception:
                    pass

            # httpx 回退
            try:
                try:
                    import httpx
                    headers = {"User-Agent": _DEFAULT_UA}
                    with httpx.Client(timeout=15, follow_redirects=True) as client:
                        resp = client.get(url, headers=headers)
                        resp.raise_for_status()
                        html = resp.text
                except Exception:
                    return {"url": url, "error": "httpx 抓取失败", "status": "failed", "backend": "httpx"}

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
                paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
                paragraphs = paragraphs[:max_paragraphs]
                return {
                    "url": url,
                    "paragraphs": paragraphs,
                    "status": "success",
                    "backend": "httpx",
                }
            except Exception as e:
                return {"url": url, "error": str(e), "status": "failed", "backend": "httpx"}

        self.registry.register(
            name="web_scrape",
            description="智能网页爬虫：JS 渲染 + stealth 反检测 + 自动回退。返回标题和段落列表。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标网页 URL（含 https://）"},
                    "backend": {"type": "string", "description": "后端：auto/obscura/httpx，auto 优先 Obscura", "default": "auto"},
                    "max_paragraphs": {"type": "integer", "description": "最大返回段落数", "default": 20},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12c. batch_scrape ──
    def _reg_batch_scrape(self):
        def handler(urls: list, backend: str = "auto", concurrency: int = 5) -> dict:
            provider = get_provider()
            actual = _resolve_backend(backend, provider)

            if actual == "obscura":
                try:
                    result = provider.batch_scrape(urls, concurrency=concurrency)
                    return result
                except Exception:
                    pass

            # httpx 回退
            try:
                import httpx

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

                results = []
                headers = {"User-Agent": _DEFAULT_UA}
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    for url in urls:
                        try:
                            resp = client.get(url, headers=headers)
                            resp.raise_for_status()
                            ex = TextExtractor()
                            ex.feed(resp.text)
                            content = "\n".join(ex.text)
                            results.append({
                                "url": url,
                                "content": content[:8000],
                                "backend": "httpx",
                            })
                        except Exception as e:
                            results.append({"url": url, "error": str(e), "backend": "httpx"})

                success = sum(1 for r in results if "error" not in r)
                return {
                    "total": len(urls),
                    "success": success,
                    "failed": len(urls) - success,
                    "results": results,
                    "backend": "httpx",
                }
            except Exception as e:
                return {"error": str(e), "backend": "httpx"}

        self.registry.register(
            name="batch_scrape",
            description="批量网页抓取：并发抓取多个 URL（Obscura 并发原生支持），自动回退 httpx 串行。",
            parameters={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "目标网页 URL 列表"},
                    "backend": {"type": "string", "description": "后端：auto/obscura/httpx，auto 优先 Obscura", "default": "auto"},
                    "concurrency": {"type": "integer", "description": "并发数（Obscura 模式有效）", "default": 5},
                },
                "required": ["urls"],
            },
            category="web",
        )(handler)
