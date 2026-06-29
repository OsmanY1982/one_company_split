"""
模型配置面板常量 — 预设供应商、模型列表、样式、配置路径、工具函数。
"""
import os
import json
import re

from PyQt5.QtWidgets import QComboBox

# ── 预设供应商模板 ──
PRESET_PROVIDERS = [
    {"id": "deepseek",        "name": "DeepSeek",         "base_url": "https://api.deepseek.com/v1",                "model": "deepseek-chat",     "desc": "DeepSeek-V3 通用大模型，性价比极高",           "local": False, "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"id": "openai",          "name": "OpenAI",            "base_url": "https://api.openai.com/v1",                  "model": "gpt-4o",            "desc": "GPT-4o / GPT-4 / GPT-3.5 系列",              "local": False, "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"]},
    {"id": "claude",          "name": "Anthropic Claude",  "base_url": "https://api.anthropic.com/v1",               "model": "claude-sonnet-4-20250514", "desc": "Claude Sonnet 4 / Opus 4 系列",          "local": False, "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]},
    {"id": "tongyi",          "name": "通义千问 (阿里云)",   "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus",   "desc": "阿里云通义千问 Qwen 系列",                     "local": False, "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b"]},
    {"id": "zhipu",           "name": "智谱 GLM",          "base_url": "https://open.bigmodel.cn/api/paas/v4",       "model": "glm-4-plus",       "desc": "智谱 GLM-4 系列",                              "local": False, "models": ["glm-4-plus", "glm-4-flash", "glm-4v-plus"]},
    {"id": "moonshot",        "name": "Moonshot (月之暗面)", "base_url": "https://api.moonshot.cn/v1",                 "model": "moonshot-v1-8k",   "desc": "月之暗面 Kimi / Moonshot",                    "local": False, "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]},
    {"id": "groq",            "name": "Groq",              "base_url": "https://api.groq.com/openai/v1",              "model": "llama-3.3-70b-versatile", "desc": "Groq LPU 高速推理",                    "local": False, "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]},
    {"id": "together",        "name": "Together AI",       "base_url": "https://api.together.xyz/v1",                 "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "desc": "Together AI 多模型托管", "local": False, "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo"]},
    {"id": "openrouter",      "name": "OpenRouter",        "base_url": "https://openrouter.ai/api/v1",                "model": "openai/gpt-4o",    "desc": "OpenRouter 多模型聚合网关",                   "local": False, "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4-20250514"]},
    {"id": "siliconflow",     "name": "SiliconFlow",       "base_url": "https://api.siliconflow.cn/v1",               "model": "deepseek-ai/DeepSeek-V3", "desc": "硅基流动 多模型推理平台",             "local": False, "models": ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]},
    {"id": "mistral",         "name": "Mistral AI",        "base_url": "https://api.mistral.ai/v1",                   "model": "mistral-large-latest", "desc": "Mistral Large / Small / Codestral",     "local": False, "models": ["mistral-large-latest", "codestral-latest"]},
    {"id": "minimax",         "name": "MiniMax (海螺AI)",   "base_url": "https://api.minimax.chat/v1",                "model": "abab6.5s-chat",    "desc": "MiniMax 海螺AI - ABAB 系列",                "local": False, "models": ["abab6.5s-chat", "abab6.5-chat"]},
    {"id": "cohere",          "name": "Cohere",            "base_url": "https://api.cohere.com/v1",                   "model": "command-r-plus",   "desc": "Cohere Command R/R+ 企业级 RAG",             "local": False, "models": ["command-r-plus", "command-r"]},
    {"id": "stepfun",         "name": "阶跃星辰 StepFun",   "base_url": "https://api.stepfun.com/v1",                  "model": "step-2-16k",       "desc": "阶跃星辰 Step 系列大模型",                   "local": False, "models": ["step-2-16k", "step-1-flash"]},
]

# ── 硬编码供应商模型列表（无需网络即可显示）──
PROVIDER_MODELS = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o4-mini", "o3", "o3-mini"],
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "Google": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
    "Anthropic Claude": ["claude-sonnet-4-20250514", "claude-3.5-sonnet", "claude-3.5-haiku"],
    "Groq": ["llama-4-scout-17b-16e", "llama-3.3-70b", "deepseek-r1-distill-llama-70b"],
    "Together AI": ["meta-llama/Llama-4-Maverick-17B", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "deepseek-ai/DeepSeek-R1"],
    "智谱 GLM": ["glm-4-plus", "glm-4-flash", "glm-4-air"],
    "Moonshot (月之暗面)": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    "通义千问 (阿里云)": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b"],
    "MiniMax (海螺AI)": ["abab7-chat", "abab6.5s-chat"],
    "SiliconFlow": ["Qwen/Qwen3-235B-A22B", "Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-V3"],
    "OpenRouter": ["openai/gpt-4o", "anthropic/claude-sonnet-4", "google/gemini-2.5-pro", "meta-llama/llama-4-maverick"],
    "Mistral AI": ["mistral-large-latest", "codestral-latest"],
    "Cohere": ["command-r-plus", "command-r"],
    "阶跃星辰 StepFun": ["step-2-16k", "step-1-flash"],
}

LOCAL_SERVICES = [
    {"id": "ollama",    "name": "Ollama",     "base_url": "http://localhost:11434/v1", "desc": "本地开源大模型运行平台，完全离线",                  "models": []},
    {"id": "lmstudio",  "name": "LM Studio",  "base_url": "http://localhost:1234/v1",  "desc": "图形界面管理模型，开箱即用",                       "models": ["local-model"]},
    {"id": "vllm",      "name": "vLLM",       "base_url": "http://localhost:8000/v1",  "desc": "高性能推理引擎，适合生产环境",                      "models": ["default"]},
    {"id": "llamacpp",  "name": "llama.cpp",  "base_url": "http://localhost:8080/v1",  "desc": "轻量 GGUF 模型推理",                              "models": ["local"]},
]

# ── 配置路径 ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IQRA_CONFIG_PATH = os.path.join(DATA_DIR, "iqra_config.json")


def _save_iqra_config(config_dict: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IQRA_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)


def _load_iqra_config() -> dict:
    try:
        if os.path.exists(IQRA_CONFIG_PATH):
            with open(IQRA_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[model_config_panel] 加载配置失败: {e}")
    return {}


# ── 模型过滤 ──

_DEPRECATED_PREFIXES = [
    "text-davinci", "text-ada", "text-babbage", "text-curie",
    "code-davinci", "code-cushman",
    "gpt-3.5-turbo-instruct", "davinci", "curie", "babbage", "ada",
]


def _filter_usable_models(models: list) -> list:
    """过滤掉过期/快照/废弃/非对话模型，只保留可用的对话模型。"""
    date_pattern = re.compile(r'-\d{4}$')

    _NON_CHAT_PREFIXES = [
        "text-embedding-", "bge-", "embedding-",
        "text-moderation-", "omni-moderation-",
        "tts-", "whisper-", "text-to-speech",
    ]
    _NON_CHAT_KEYWORDS = [
        "-tts-", "embedding", "moderation", "whisper",
        "dall-e", "dalle",
        "-edit",
        "-similarity", "-search-",
    ]
    _BLACKLIST_SUFFIXES = [
        "-search-doc", "-search-query", "-code-search-",
        "-similarity", "-insert",
    ]

    result = []
    for m in models:
        if any(m.startswith(p) or m == p for p in _DEPRECATED_PREFIXES):
            continue
        if date_pattern.search(m):
            continue
        if any(m.startswith(p) for p in _NON_CHAT_PREFIXES):
            continue
        m_lower = m.lower()
        if any(kw in m_lower for kw in _NON_CHAT_KEYWORDS):
            continue
        if any(m_lower.endswith(s) for s in _BLACKLIST_SUFFIXES):
            continue
        result.append(m)

    return result


def _populate_model_combo(combo: QComboBox, models: list, saved_model: str = ""):
    """用模型列表填充下拉框，并尝试恢复之前选中的模型。"""
    combo.clear()
    if not models:
        combo.addItem("（无可用的活跃模型）", "")
        if saved_model:
            combo.setEditText(saved_model)
        return
    for m in models:
        combo.addItem(m, m)
    if saved_model:
        idx = combo.findText(saved_model)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setEditText(saved_model)


# ── 样式 ──
INPUT_STYLE = """
    QLineEdit {
        background: rgba(8, 16, 32, 220);
        color: #99ccff;
        border: 1px solid rgba(60, 140, 240, 45);
        border-radius: 18px;
        padding: 10px 18px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid rgba(0, 200, 255, 160);
        background: rgba(10, 20, 40, 240);
    }
    QLineEdit::placeholder {
        color: #334466;
    }
"""

COMBO_STYLE = """
    QComboBox {
        background: rgba(8, 16, 32, 220);
        color: #99ccff;
        border: 1px solid rgba(60, 140, 240, 45);
        border-radius: 18px;
        padding: 10px 18px;
        font-size: 13px;
    }
    QComboBox:hover { border: 1px solid rgba(0, 200, 255, 140); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: rgba(10, 18, 36, 245);
        color: #99ccff;
        selection-background-color: rgba(40, 100, 200, 80);
        border: 1px solid rgba(60, 140, 240, 50);
        outline: none;
    }
"""

LABEL_STYLE = "color: #6688aa; font-size: 11px; letter-spacing: 2px; background: transparent;"

BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0055cc, stop:1 #0088ff);
        color: white; border: none; border-radius: 22px;
        padding: 10px 40px; font-size: 14px; font-weight: 700;
        letter-spacing: 4px;
    }
    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0077ee, stop:1 #00aaff); }
    QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0044aa, stop:1 #0066cc); }
"""

BTN_SECONDARY = """
    QPushButton {
        background: rgba(30, 40, 60, 200);
        color: #8899aa; border: 1px solid rgba(70, 90, 120, 50);
        border-radius: 22px; padding: 9px 32px; font-size: 13px;
        font-weight: 600; letter-spacing: 3px;
    }
    QPushButton:hover { background: rgba(40, 55, 80, 220); color: #aaccee; }
"""
