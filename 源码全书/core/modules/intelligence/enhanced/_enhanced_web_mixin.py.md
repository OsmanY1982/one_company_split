# `core/modules/intelligence/enhanced/_enhanced_web_mixin.py`

> 路径：`core/modules/intelligence/enhanced/_enhanced_web_mixin.py` | 行数：263


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 代码执行 + 浏览器操作 Mixin
  run_code / browser_navigate / web_fetch_page / web_search / browser_screenshot / browser_extract
"""

import os
import sys
import subprocess
import webbrowser
from typing import Dict, Any

from ._enhanced_base import _safe_path, _PROJECT_ROOT


class EnhancedWebMixin:
    """代码执行 + 浏览器/网页工具集"""

    def _tool_run_code(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """在独立进程中执行 Python 代码"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=_PROJECT_ROOT,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() or "(无输出)",
                "stderr": result.stderr.strip() or "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"执行超时（{timeout} 秒）"}
        except FileNotFoundError:
            return {"success": False, "error": "Python 解释器不可用"}

    def _tool_browser_navigate(self, url: str) -> Dict[str, Any]:
        """在默认浏览器中打开 URL"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return {"success": True, "url": url, "message": f"已在浏览器中打开: {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_web_fetch_page(self, url: str) -> Dict[str, Any]:
        """抓取网页正文内容"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            return {"success": False, "error": f"网络错误: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

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

        if len(content) > 8000:
            content = content[:8000] + "\n\n... [已截断]"

        return {
            "success": True,
            "url": url,
            "chars": len(content),
            "content": content,
        }

    def _tool_web_search(self, query: str) -> Dict[str, Any]:
        """网页搜索 — 通过 DuckDuckGo HTML 搜索结果页获取标题/链接/摘要"""
        import urllib.request
        import urllib.parse
        import urllib.error
        from html.parser import HTMLParser

        encoded_query = urllib.parse.quote(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        try:
            req = urllib.request.Request(search_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            return {"success": False, "error": f"网络错误: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self._current = {"title": "", "link": "", "snippet": ""}
                self._in_result = False
                self._in_title = False
                self._in_snippet = False
                self._snippet_div_depth = 0
                self._pending_link = ""

            def handle_starttag(self, tag, attrs):
                attr_dict = dict(attrs)
                cls = attr_dict.get("class", "")

                if tag == "a" and "result__a" in cls:
                    self._in_title = True
                    self._pending_link = attr_dict.get("href", "")
                elif tag == "a" and "result__snippet" in cls:
                    self._in_snippet = True
                elif tag == "div" and "result__body" in cls:
                    self._in_result = True
                    self._current = {"title": "", "link": "", "snippet": ""}

            def handle_endtag(self, tag):
                if self._in_title and tag == "a":
                    self._in_title = False
                    self._current["title"] = self._current["title"].strip()
                    self._current["link"] = self._pending_link
                    self._pending_link = ""
                if self._in_snippet and tag == "a":
                    self._in_snippet = False
                    self._current["snippet"] = self._current["snippet"].strip()
                if self._in_result and tag == "div" and self._current["title"]:
                    self._in_result = False
                    self.results.append(dict(self._current))
                    self._current = {"title": "", "link": "", "snippet": ""}

            def handle_data(self, data):
                if self._in_title:
                    self._current["title"] += data
                if self._in_snippet:
                    self._current["snippet"] += data

        parser = DDGParser()
        parser.feed(html)

        results = parser.results[:20]

        if not results:
            import re
            fallback = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            snippets = re.findall(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            for i, (link, title) in enumerate(fallback[:20]):
                t = re.sub(r"<[^>]+>", "", title).strip()
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
                results.append({"title": t, "link": link, "snippet": snippet})

        if not results:
            return {"success": False, "error": "未获取到搜索结果", "query": query}

        lines = [f"搜索: {query}", f"共 {len(results)} 条结果", ""]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   {r['link']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            lines.append("")

        formatted = "\n".join(lines)
        if len(formatted) > 8000:
            formatted = formatted[:8000] + "\n\n... [已截断]"

        return {
            "success": True,
            "query": query,
            "source": "duckduckgo",
            "results": results,
            "count": len(results),
            "formatted": formatted,
        }

    def _tool_browser_screenshot(self) -> Dict[str, Any]:
        """网页截图"""
        try:
            import importlib
            importlib.import_module("playwright")
            return {"success": True, "message": "Playwright 可用，可执行截图"}
        except ImportError:
            return {
                "success": True,
                "message": (
                    "网页截图需要 Playwright 支持。请安装：\n"
                    "  pip install playwright\n"
                    "  playwright install chromium\n\n"
                    "当前已降级为浏览器打开模式。"
                ),
                "degraded": True,
            }

    def _tool_browser_extract(self, url: str = "") -> Dict[str, Any]:
        """提取网页文本"""
        if not url:
            return {"success": False, "error": "请提供目标 URL"}
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            return {"success": False, "error": f"网络错误: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        import re
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > 10000:
            text = text[:10000] + "\n\n... [已截断]"

        return {
            "success": True,
            "url": url,
            "text": text,
            "length": len(text),
        }

```
