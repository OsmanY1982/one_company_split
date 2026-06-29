# -*- coding: utf-8 -*-
from __future__ import annotations
"""
模型配置 — 云端 + 本地
所有用户可在 APP 内自由选择，云端需输入自己的 API Key

⚠️ 百炼 MaaS 模型（含 ws-h8l0vt3djouffqk7 端点 / 共享管理员 Key）已全部移除
"""

# ── 云端模型 ─────────────────
CLOUD_MODELS = [
    {
        "id": "openai_gpt4o",
        "name": "☁️ OpenAI GPT-4o",
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o",
        "hint": "输入你的 OpenAI API Key（sk-开头）",
    },
    {
        "id": "deepseek_v3",
        "name": "☁️ DeepSeek V3（官方）",
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "model_name": "deepseek-chat",
        "hint": "输入你的 DeepSeek API Key（sk-开头）",
    },
]

# ── 本地模型（llama.cpp，免费）───────────────────
LOCAL_MODELS = [
    {
        "id": "llama_qwen25_1.5b",
        "name": "💻 本地 qwen2.5:1.5b",
        "provider": "llama_proxy",
        "model_name": "qwen2.5:1.5b",
        "hint": "需先启动 llama.cpp server 并下载模型",
    },
    {
        "id": "llama_qwen25_0.5b",
        "name": "💻 本地 qwen2.5:0.5b",
        "provider": "llama_proxy",
        "model_name": "qwen2.5:0.5b",
        "hint": "需先启动 llama.cpp server 并下载模型",
    },
]

# ── 合并列表（用于下拉框）─────────────────────────
ALL_MODELS = CLOUD_MODELS + LOCAL_MODELS


def get_model_by_id(model_id: str) -> dict | None:
    """根据 ID 查找模型配置"""
    for m in ALL_MODELS:
        if m["id"] == model_id:
            return m
    return None


def is_cloud_model(model_id: str) -> bool:
    """判断是否为云端模型（需要 API Key）"""
    m = get_model_by_id(model_id)
    return m is not None and m["provider"] != "llama_proxy"


def is_local_model(model_id: str) -> bool:
    """判断是否为本地模型"""
    m = get_model_by_id(model_id)
    return m is not None and m["provider"] == "llama_proxy"


def get_system_prompt() -> str:
    """系统提示词"""
    return (
        "你是一个友好的AI助手，名字叫小Q。"
        "请用中文回答，回答简洁清晰，不超过300字。"
    )
