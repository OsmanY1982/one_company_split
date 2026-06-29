# -*- coding: utf-8 -*-
"""
Ollama 本地模型管理器 — 检测、启动、列出、删除、下载
从 _model_manager.py 拆分，独立为 _model_manager_ollama.py
"""

import json
import urllib.request
import urllib.error


class OllamaManager:
    """管理本地 LLM 模型（llama.cpp server / llama-proxy）"""

    SERVER_URL = "http://localhost:8080"

    @classmethod
    def is_installed(cls) -> bool:
        """检查 llama.cpp server 或 llama-proxy 是否可用"""
        return cls.is_running()

    @classmethod
    def is_running(cls) -> bool:
        """检查 llama.cpp 服务是否运行"""
        try:
            req = urllib.request.Request(
                f"{cls.SERVER_URL}/v1/models",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def start_service(cls) -> bool:
        """llama.cpp server 应手动启动，此处仅检查状态"""
        if cls.is_running():
            return True
        print("[OllamaManager] llama.cpp server 未运行，请手动启动 llama-proxy.py")
        return False

    @classmethod
    def list_models(cls) -> list:
        """获取已加载的模型列表（通过 /v1/models）"""
        try:
            req = urllib.request.Request(
                f"{cls.SERVER_URL}/v1/models",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_models = data.get("data", [])
                return [{"name": m.get("id", ""), "size": 0} for m in raw_models]
        except Exception as e:
            print(f"[OllamaManager] 获取模型列表失败: {e}")
            return []

    @classmethod
    def delete_model(cls, model_name: str) -> bool:
        """删除模型（llama-proxy 不支持，请手动删除 gguf 文件）"""
        print(f"[OllamaManager] llama-proxy 不支持远程删除模型，请手动删除 ~/.llama-models/ 下的 {model_name}.gguf")
        return False

    @classmethod
    def pull_model(cls, model_name: str, progress_callback=None) -> bool:
        """下载模型（llama-proxy 不支持，请手动下载 gguf）"""
        print(f"[OllamaManager] llama-proxy 不支持远程下载模型，请手动下载 gguf 到 ~/.llama-models/")
        return False
