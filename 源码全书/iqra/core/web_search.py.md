# `iqra/core/web_search.py`

> 路径：`iqra/core/web_search.py` | 行数：598


---


```python
"""
网络搜索能力
支持多种搜索引擎和搜索模式
"""

import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
import html


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    source: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class WebSearchEngine:
    """网页搜索引擎基类"""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.rate_limit_delay = 1.0  # 请求间隔（秒）
        self.last_request_time = 0
    
    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            SearchResponse
        """
        raise NotImplementedError
    
    def _fetch_url(self, url: str, headers: Dict = None, timeout: int = 30) -> str:
        """获取 URL 内容"""
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        if headers:
            default_headers.update(headers)
        
        request = urllib.request.Request(url, headers=default_headers)
        
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error: {str(e)}"


class DuckDuckGoSearch(WebSearchEngine):
    """DuckDuckGo 搜索（无需 API Key）"""
    
    def __init__(self):
        super().__init__("DuckDuckGo")
        self.base_url = "https://html.duckduckgo.com/html/"
    
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        """执行 DuckDuckGo 搜索"""
        self._rate_limit()
        
        start_time = time.time()
        
        # 构建搜索 URL
        params = {'q': query}
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            html_content = self._fetch_url(url)
            results = self._parse_results(html_content, num_results)
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=time.time() - start_time,
                source=self.name
            )
        except Exception as e:
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time=time.time() - start_time,
                source=self.name
            )
    
    def _parse_results(self, html_content: str, num_results: int) -> List[SearchResult]:
        """解析搜索结果"""
        results = []
        
        # 简单的正则解析（实际使用建议用 BeautifulSoup）
        # 这里使用基本的字符串匹配
        result_blocks = re.findall(
            r'<div class="result[^"]*">.*?<h[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</div>',
            html_content,
            re.DOTALL | re.IGNORECASE
        )
        
        for i, (url, title) in enumerate(result_blocks[:num_results]):
            # 清理标题
            title = re.sub(r'<[^>]+>', '', title)
            title = html.unescape(title)
            
            # 提取摘要
            snippet_match = re.search(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                html_content
            )
            snippet = ""
            if snippet_match:
                snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1))
                snippet = html.unescape(snippet)
            
            results.append(SearchResult(
                title=title.strip(),
                url=html.unescape(url),
                snippet=snippet.strip(),
                source=self.name
            ))
        
        return results


class BingSearch(WebSearchEngine):
    """Bing 搜索（需要 API Key）"""
    
    def __init__(self, api_key: str):
        super().__init__("Bing", api_key)
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
    
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        """执行 Bing 搜索"""
        if not self.api_key:
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time=0,
                source=self.name
            )
        
        self._rate_limit()
        start_time = time.time()
        
        headers = {'Ocp-Apim-Subscription-Key': self.api_key}
        params = {'q': query, 'count': num_results}
        
        try:
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            response = self._fetch_url(url, headers=headers)
            data = json.loads(response)
            
            results = []
            for item in data.get('webPages', {}).get('value', []):
                results.append(SearchResult(
                    title=item.get('name', ''),
                    url=item.get('url', ''),
                    snippet=item.get('snippet', ''),
                    source=self.name,
                    timestamp=item.get('dateLastCrawled')
                ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=data.get('webPages', {}).get('totalEstimatedMatches', 0),
                search_time=time.time() - start_time,
                source=self.name
            )
        except Exception as e:
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time=time.time() - start_time,
                source=self.name
            )


class WebSearchManager:
    """
    网络搜索管理器
    统一管理多个搜索引擎
    """
    
    def __init__(self):
        self.engines: Dict[str, WebSearchEngine] = {}
        self.default_engine: Optional[str] = None
        self.cache: Dict[str, SearchResponse] = {}
        self.cache_ttl = 3600  # 缓存时间（秒）
        self.search_history: List[Dict] = []
    
    def register_engine(self, engine: WebSearchEngine, set_default: bool = False):
        """注册搜索引擎"""
        self.engines[engine.name] = engine
        if set_default or self.default_engine is None:
            self.default_engine = engine.name
    
    def search(self, query: str, 
               engine_name: str = None,
               num_results: int = 10,
               use_cache: bool = True,
               **kwargs) -> SearchResponse:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            engine_name: 搜索引擎名称
            num_results: 结果数量
            use_cache: 是否使用缓存
            
        Returns:
            SearchResponse
        """
        # 检查缓存
        cache_key = f"{engine_name or self.default_engine}:{query}:{num_results}"
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - datetime.fromisoformat(cached.timestamp).timestamp() < self.cache_ttl:
                return cached
        
        # 选择搜索引擎
        engine_name = engine_name or self.default_engine
        if engine_name not in self.engines:
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time=0,
                source="error",
                timestamp=datetime.now().isoformat()
            )
        
        # 执行搜索
        engine = self.engines[engine_name]
        response = engine.search(query, num_results, **kwargs)
        
        # 缓存结果
        if use_cache:
            self.cache[cache_key] = response
        
        # 记录历史
        self.search_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'engine': engine_name,
            'results_count': len(response.results)
        })
        
        return response
    
    def multi_search(self, query: str, 
                     engines: List[str] = None,
                     num_results: int = 10) -> List[SearchResponse]:
        """
        多引擎搜索
        
        Args:
            query: 搜索查询
            engines: 搜索引擎列表（None 表示全部）
            num_results: 每个引擎的结果数量
            
        Returns:
            SearchResponse 列表
        """
        if engines is None:
            engines = list(self.engines.keys())
        
        responses = []
        for engine_name in engines:
            if engine_name in self.engines:
                response = self.search(query, engine_name, num_results)
                responses.append(response)
        
        return responses
    
    def aggregate_search(self, query: str,
                        num_results: int = 10,
                        deduplicate: bool = True) -> SearchResponse:
        """
        聚合搜索（多引擎结果合并）
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            deduplicate: 是否去重
            
        Returns:
            SearchResponse
        """
        responses = self.multi_search(query, num_results=num_results)
        
        all_results = []
        seen_urls = set()
        
        for response in responses:
            for result in response.results:
                if deduplicate:
                    url_key = result.url.rstrip('/').lower()
                    if url_key in seen_urls:
                        continue
                    seen_urls.add(url_key)
                all_results.append(result)
        
        # 按相关性排序（简化：按来源多样性）
        all_results = all_results[:num_results]
        
        return SearchResponse(
            query=query,
            results=all_results,
            total_results=len(all_results),
            search_time=sum(r.search_time for r in responses) / len(responses) if responses else 0,
            source="aggregate"
        )
    
    def quick_answer(self, query: str) -> Optional[str]:
        """
        快速获取答案（取第一个结果的摘要）
        
        Args:
            query: 搜索查询
            
        Returns:
            答案文本或 None
        """
        response = self.search(query, num_results=3)
        
        if response.results:
            # 合并前 3 个结果的摘要
            snippets = [r.snippet for r in response.results[:3] if r.snippet]
            return " ".join(snippets) if snippets else None
        
        return None
    
    def search_with_context(self, query: str, 
                           context: str,
                           num_results: int = 10) -> SearchResponse:
        """
        带上下文的搜索
        
        Args:
            query: 搜索查询
            context: 上下文信息
            num_results: 结果数量
            
        Returns:
            SearchResponse
        """
        # 将上下文融入查询
        enhanced_query = f"{context} {query}"
        return self.search(enhanced_query, num_results=num_results)
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        获取搜索建议
        
        Args:
            query: 搜索查询
            
        Returns:
            建议列表
        """
        # 这里可以实现实际的搜索建议 API
        # 简化版本：返回一些常见变体
        suggestions = [
            f"{query} 教程",
            f"{query} 文档",
            f"{query} 示例",
            f"{query} 最佳实践",
            f"{query} vs"
        ]
        return suggestions
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取搜索历史"""
        return self.search_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取搜索统计"""
        if not self.search_history:
            return {
                'total_searches': 0,
                'unique_queries': 0,
                'average_results': 0
            }
        
        total = len(self.search_history)
        unique = len(set(h['query'] for h in self.search_history))
        avg_results = sum(h['results_count'] for h in self.search_history) / total
        
        return {
            'total_searches': total,
            'unique_queries': unique,
            'average_results': round(avg_results, 2),
            'engines': list(self.engines.keys())
        }


class SearchResultProcessor:
    """搜索结果处理器"""
    
    @staticmethod
    def format_for_llm(response: SearchResponse, max_length: int = 2000) -> str:
        """
        格式化搜索结果供 LLM 使用
        
        Args:
            response: 搜索响应
            max_length: 最大长度
            
        Returns:
            格式化文本
        """
        lines = [
            f"搜索结果: {response.query}",
            f"来源: {response.source}",
            f"找到 {len(response.results)} 个结果",
            ""
        ]
        
        current_length = sum(len(line) for line in lines)
        
        for i, result in enumerate(response.results, 1):
            result_text = f"{i}. {result.title}\n   URL: {result.url}\n   {result.snippet}\n\n"
            
            if current_length + len(result_text) > max_length:
                lines.append(f"... 还有 {len(response.results) - i + 1} 个结果")
                break
            
            lines.append(result_text)
            current_length += len(result_text)
        
        return "\n".join(lines)
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fa5]{2,}\b', text)
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # 返回频率最高的词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
    
    @staticmethod
    def filter_by_domain(results: List[SearchResult], 
                        domains: List[str]) -> List[SearchResult]:
        """按域名过滤结果"""
        return [r for r in results if any(d in r.url for d in domains)]
    
    @staticmethod
    def filter_by_date(results: List[SearchResult],
                      days: int) -> List[SearchResult]:
        """按日期过滤结果"""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = []
        for result in results:
            if result.timestamp:
                try:
                    result_date = datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
                    if result_date >= cutoff:
                        filtered.append(result)
                except:
                    pass
            else:
                filtered.append(result)
        
        return filtered


# ════════════════════════════════════════════════════════════
# 便捷函数
# ════════════════════════════════════════════════════════════

# 全局搜索管理器
_search_manager = None

def get_search_manager() -> WebSearchManager:
    """获取全局搜索管理器"""
    global _search_manager
    if _search_manager is None:
        _search_manager = WebSearchManager()
        # 注册默认引擎
        _search_manager.register_engine(DuckDuckGoSearch(), set_default=True)
    return _search_manager


def web_search(query: str, num_results: int = 5) -> str:
    """
    便捷函数：执行网页搜索
    
    Args:
        query: 搜索查询
        num_results: 结果数量
        
    Returns:
        格式化的搜索结果文本
    """
    manager = get_search_manager()
    response = manager.search(query, num_results=num_results)
    return SearchResultProcessor.format_for_llm(response)


def quick_search(query: str) -> Optional[str]:
    """便捷函数：快速搜索获取答案"""
    return get_search_manager().quick_answer(query)


def multi_engine_search(query: str, num_results: int = 3) -> str:
    """便捷函数：多引擎搜索"""
    manager = get_search_manager()
    response = manager.aggregate_search(query, num_results=num_results)
    return SearchResultProcessor.format_for_llm(response)


# ════════════════════════════════════════════════════════════
# 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("网络搜索模块测试")
    print("=" * 50)
    
    # 初始化
    manager = get_search_manager()
    print(f"已注册引擎: {list(manager.engines.keys())}")
    print()
    
    # 测试搜索
    print("测试搜索: Python 数据分析")
    result = web_search("Python 数据分析教程", num_results=3)
    print(result[:500])
    print("...")
    print()
    
    # 测试快速答案
    print("测试快速答案: Python 是什么")
    answer = quick_search("Python programming language")
    print(f"答案: {answer[:200] if answer else '无结果'}...")
    print()
    
    # 统计
    print("搜索统计:")
    print(manager.get_stats())

```
