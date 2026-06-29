# `planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_web_tools.py`

> 路径：`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_web_tools.py` | 行数：189


---


```python
"""网络工具 Mixin：web_search / web_fetch_page / web_scrape / batch_scrape"""

import urllib.request
import urllib.parse
from html.parser import HTMLParser


class _WebToolsMixin:
    """网络工具注册"""

    # ── 11. web_search ──
    def _reg_web_search(self):
        def handler(query: str, max_results: int = 8) -> dict:
            try:
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
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
                return {"query": query, "count": len(parser.results[:max_results]), "results": parser.results[:max_results]}
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
                },
                "required": ["query"],
            },
            category="web",
        )(handler)

    # ── 12. web_fetch_page ──
    def _reg_web_fetch_page(self):
        def handler(url: str) -> dict:
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                # 简易正文提取
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
                return {"url": url, "chars": len(content), "content": content[:8000]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="web_fetch_page",
            description="抓取网页正文内容（提取纯文本）",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL（含 https://）"},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12b. web_scrape（Iqra 智能爬虫）──
    def _reg_web_scrape(self):
        """Iqra 智能单页爬虫：JS 渲染 + 代理轮转 + 频率限制 + 重试"""
        def handler(url: str, use_selenium: bool = False, max_paragraphs: int = 20) -> dict:
            try:
                from iqra import Iqra, IqraConfig
                config = IqraConfig(
                    use_selenium=use_selenium,
                    output_format="dict",
                    timeout=30,
                )
                scraper = Iqra(config)
                result = scraper.scrape_url(url)
                scraper.close()
                if isinstance(result, dict) and "paragraphs" in result:
                    result["paragraphs"] = result["paragraphs"][:max_paragraphs]
                return result
            except Exception as e:
                return {"url": url, "error": str(e), "status": "failed"}

        self.registry.register(
            name="web_scrape",
            description="Iqra 智能网页爬虫：带 JS 渲染、代理轮转、频率限制、指数退避重试。返回标题/元描述/段落。适合需要 JS 渲染的动态页面。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标网页 URL（含 https://）"},
                    "use_selenium": {"type": "boolean", "description": "是否启用 Selenium JS 渲染", "default": False},
                    "max_paragraphs": {"type": "integer", "description": "最大返回段落数", "default": 20},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12c. batch_scrape（Iqra 批量爬虫）──
    def _reg_batch_scrape(self):
        """Iqra 批量爬虫：一次抓取多个 URL"""
        def handler(urls: list, use_selenium: bool = False) -> dict:
            try:
                from iqra import Iqra, IqraConfig
                config = IqraConfig(
                    use_selenium=use_selenium,
                    output_format="dict",
                    timeout=30,
                )
                scraper = Iqra(config)
                results = scraper.batch_scrape(urls)
                scraper.close()
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                return {
                    "total": len(urls),
                    "success": success_count,
                    "failed": len(urls) - success_count,
                    "results": results,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="batch_scrape",
            description="Iqra 批量网页爬虫：一次性抓取多个 URL，返回汇总统计和逐页结果。",
            parameters={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "目标网页 URL 列表"},
                    "use_selenium": {"type": "boolean", "description": "是否启用 Selenium JS 渲染", "default": False},
                },
                "required": ["urls"],
            },
            category="web",
        )(handler)

```
