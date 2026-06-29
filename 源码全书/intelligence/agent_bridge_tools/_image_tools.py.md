# `intelligence/agent_bridge_tools/_image_tools.py`

> 路径：`intelligence/agent_bridge_tools/_image_tools.py` | 行数：167


---


```python
"""图片工具 Mixin：analyze_image / search_image"""

import os
import base64
import glob as _glob
from typing import Optional


class _ImageToolsMixin:
    """图片分析 / 搜索工具注册"""

    # ── 1. analyze_image（视觉理解）──
    def _reg_analyze_image(self):
        def handler(
            image_path: str,
            prompt: str = "请详细描述这张图片的内容",
        ) -> dict:
            """调用视觉大模型分析图片内容"""
            try:
                if not os.path.isfile(image_path):
                    return {"error": f"文件不存在: {image_path}"}

                # 读取图片 → base64
                ext = os.path.splitext(image_path)[1].lower()
                mime_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".bmp": "image/bmp",
                }
                mime = mime_map.get(ext, "image/png")

                with open(image_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")

                # 构建 vision 消息
                vision_messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{img_data}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ]

                # 调用 LLM（需要 backend 实例）
                backend = getattr(self, "_backend", None)
                if backend is None:
                    return {"error": "LLM 后端未初始化，无法分析图片"}

                response = backend.chat(vision_messages, token_saver_mode="off")
                content = response.get("content", "") if isinstance(response, dict) else str(response)

                return {
                    "image": image_path,
                    "analysis": content,
                    "prompt": prompt,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="analyze_image",
            description=(
                "分析图片内容。调用视觉大模型理解图片中的文字、物体、场景等。"
                "支持 PNG/JPG/GIF/WebP/BMP 格式。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "图片文件绝对路径",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "分析提示词（如'提取图中所有文字'、'描述图中场景'）",
                        "default": "请详细描述这张图片的内容",
                    },
                },
                "required": ["image_path"],
            },
            category="image",
        )(handler)

    # ── 2. search_image（图片搜索）──
    def _reg_search_image(self):
        def handler(
            directory: str,
            pattern: str = "*",
            recursive: bool = True,
            max_results: int = 50,
        ) -> dict:
            """搜索图片文件"""
            image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg", ".tiff", ".heic"}
            try:
                if not os.path.isdir(directory):
                    return {"error": f"不是有效目录: {directory}"}

                results = []
                if recursive:
                    for root, _, files in os.walk(directory):
                        for fname in files:
                            ext = os.path.splitext(fname)[1].lower()
                            if ext in image_exts and _glob.fnmatch.fnmatch(fname, pattern):
                                results.append(os.path.join(root, fname))
                                if len(results) >= max_results:
                                    break
                        if len(results) >= max_results:
                            break
                else:
                    for fname in os.listdir(directory):
                        full = os.path.join(directory, fname)
                        ext = os.path.splitext(fname)[1].lower()
                        if os.path.isfile(full) and ext in image_exts and _glob.fnmatch.fnmatch(fname, pattern):
                            results.append(full)

                return {
                    "directory": directory,
                    "pattern": pattern,
                    "count": len(results),
                    "images": results[:max_results],
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_image",
            description=(
                "搜索目录中的图片文件。自动识别常见图片格式（PNG/JPG/GIF/WebP/BMP/ICO/SVG/TIFF/HEIC）。"
                "支持通配符过滤（如 '*.png'、'发票*'）。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "搜索根目录绝对路径",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件名通配符，默认 * 匹配所有图片",
                        "default": "*",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归子目录",
                        "default": True,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大返回数",
                        "default": 50,
                    },
                },
                "required": ["directory"],
            },
            category="image",
        )(handler)

```
