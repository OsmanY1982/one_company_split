# `iqra/core/_tokenizer.py`

> 路径：`iqra/core/_tokenizer.py` | 行数：88


---


```python
# -*- coding: utf-8 -*-
"""中英文混合分词器"""
import re
from typing import List

# 中文高频停用词（单字虚词，搜索无区分度）
_CN_STOP_CHARS = set("的了在是我有和就都不人也一个上很到说来你他会着没看要这那之为及与或但而因所已被其于将能可过以对从自当用中后前呢吧吗啊嘛哦嗯哈呵嘿嗨呀哎哟噢")

# 中文高频双字虚词（搜索无区分度）
_CN_STOP_BIGRAMS = {"可以", "这个", "那个", "一个", "什么", "怎么", "他们", "我们", "自己", "没有", "已经", "还是", "因为", "所以", "但是", "如果", "虽然", "不过", "然后", "而且", "并且", "或者", "只是", "就是", "还是", "起来", "出来", "下来", "过来", "过去", "的时候", "没有", "知道"}


class Tokenizer:
    """中英文混合分词器（轻量级，零依赖）"""

    # 中文 + 英文单词 + 标识符
    _CHINESE_RE = re.compile(r'[\u4e00-\u9fff]+')
    _WORD_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
    _NUMBER_RE = re.compile(r'\d+')

    @classmethod
    def tokenize(cls, text: str, precision: bool = False) -> List[str]:
        """将文本分词为 token 列表

        Args:
            text: 输入文本
            precision: True=跳过中文单字和虚词（提高搜索精度），False=全量（提高召回率）
        """
        tokens = []

        # 提取中文连续序列
        for m in cls._CHINESE_RE.finditer(text):
            chars = m.group()
            if precision:
                tokens.extend(cls._chinese_ngrams_precision(chars))
            else:
                tokens.extend(cls._chinese_ngrams(chars))

        # 提取英文标识符
        for m in cls._WORD_RE.finditer(text):
            word = m.group().lower()
            if len(word) > 1:  # 跳过单字母
                tokens.append(word)
                # 驼峰拆分: getUserInfo → [get, user, info]
                subtokens = cls._split_camel(word)
                if len(subtokens) > 1:
                    tokens.extend([t for t in subtokens if len(t) > 1])

        # 去重保持顺序（用于 IDF 计算）
        return list(dict.fromkeys(tokens))

    @classmethod
    def _chinese_ngrams(cls, text: str) -> List[str]:
        """中文分词：单字 + 双字 + 三字 n-gram（高召回模式）"""
        result = []
        for ch in text:
            if ch not in _CN_STOP_CHARS:
                result.append(ch)
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            if bigram not in _CN_STOP_BIGRAMS:
                result.append(bigram)
        for i in range(len(text) - 2):
            result.append(text[i:i+3])
        return result

    @classmethod
    def _chinese_ngrams_precision(cls, text: str) -> List[str]:
        """中文分词：仅双字 + 三字 n-gram + 4-gram（高精度模式，跳过单字）"""
        result = []
        # 双字
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            if bigram not in _CN_STOP_BIGRAMS:
                result.append(bigram)
        # 三字
        for i in range(len(text) - 2):
            result.append(text[i:i+3])
        # 四字（长词匹配）
        for i in range(len(text) - 3):
            result.append(text[i:i+4])
        return result

    @classmethod
    def _split_camel(cls, word: str) -> List[str]:
        """拆分驼峰命名：getUserInfo → ['get', 'User', 'Info']"""
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)', word)
        return [p.lower() for p in parts if len(p) > 1]

```
