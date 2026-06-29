# `iqra/core/_backend_providers.py`

> 路径：`iqra/core/_backend_providers.py` | 行数：219


---


```python
"""
Iqra LLM Backend — 内置供应商模板 (25个)
"""
from ._backend_models import ProviderConfig


PROVIDER_TEMPLATES = {
    # ── 云端模型 ──
    "deepseek": ProviderConfig(
        name="DeepSeek",
        provider_type="openai_compatible",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        max_tokens=8192,              # DeepSeek-V3 最大输出 8K
        description="DeepSeek-V3 通用大模型, 性价比极高",
        available_models=["deepseek-chat", "deepseek-reasoner"],
    ),
    "deepseek_reasoner": ProviderConfig(
        name="DeepSeek Reasoner",
        provider_type="openai_compatible",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-reasoner",
        max_tokens=8192,              # DeepSeek-R1 最大输出 8K (推理 token 不计入)
        description="DeepSeek-R1 深度推理模型",
        available_models=["deepseek-chat", "deepseek-reasoner"],
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        provider_type="openai_compatible",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
        max_tokens=16384,             # GPT-4o 最大输出 16K
        description="GPT-4o / GPT-4 / GPT-3.5 系列",
        available_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"],
    ),
    "tongyi": ProviderConfig(
        name="通义千问",
        provider_type="openai_compatible",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        max_tokens=131072,            # Qwen3-235B 最大输出 128K, qwen-plus/turbo 为 8K
        description="阿里云通义千问 Qwen 系列",
        available_models=["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b", "qwen2.5-72b-instruct", "qwen2.5-32b-instruct", "qwen2.5-14b-instruct", "qwen2.5-7b-instruct"],
    ),
    "zhipu": ProviderConfig(
        name="智谱 GLM",
        provider_type="openai_compatible",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model="glm-4-plus",
        max_tokens=4096,              # GLM-4 系列最大输出 4K
        description="智谱 GLM-4 系列",
        available_models=["glm-4-plus", "glm-4-flash", "glm-4-air", "glm-4-long", "glm-4v-plus", "glm-4v-flash"],
    ),
    "moonshot": ProviderConfig(
        name="Moonshot",
        provider_type="openai_compatible",
        base_url="https://api.moonshot.cn/v1",
        model="moonshot-v1-8k",
        max_tokens=4096,              # Moonshot 最大输出约 4K
        description="月之暗面 Kimi / Moonshot",
        available_models=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    ),
    "wenxin": ProviderConfig(
        name="百度文心 (千帆)",
        provider_type="openai_compatible",
        base_url="https://qianfan.baidubce.com/v2",
        model="ernie-4.0-8k",
        max_tokens=2048,              # ERNIE 系列最大输出 2K
        description="百度千帆大模型平台 - ERNIE 系列 [需 API Key + Secret Key 换取 access_token]",
        available_models=["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k", "ernie-speed-8k", "ernie-lite-8k", "ernie-tiny-8k"],
    ),
    "xunfei": ProviderConfig(
        name="讯飞星火",
        provider_type="openai_compatible",
        base_url="https://spark-api-open.xf-yun.com/v1",
        model="4.0Ultra",
        max_tokens=8192,              # 星火 4.0 最大输出 8K
        description="讯飞星火认知大模型 [需 AppId + API Key + Secret]",
        available_models=["4.0Ultra", "generalv3.5", "generalv3", "spark-lite", "pro-128k", "max-32k"],
    ),
    "groq": ProviderConfig(
        name="Groq",
        provider_type="openai_compatible",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
        max_tokens=32768,             # Groq 最大输出 32K
        description="Groq LPU 高速推理",
        available_models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it", "deepseek-r1-distill-llama-70b"],
    ),
    "together": ProviderConfig(
        name="Together AI",
        provider_type="openai_compatible",
        base_url="https://api.together.xyz/v1",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        max_tokens=16384,             # Together 默认 16K，部分模型支持更高
        description="Together AI 多模型托管平台",
        available_models=["meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-3.1-405B-Instruct-Turbo", "meta-llama/Llama-3.1-70B-Instruct-Turbo", "meta-llama/Llama-3.1-8B-Instruct-Turbo", "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "google/gemma-2-27b-it"],
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        provider_type="openai_compatible",
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-4o",
        max_tokens=131072,            # OpenRouter 取上限，实际由底层模型决定
        description="OpenRouter 多模型聚合网关",
        available_models=["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-sonnet-4-20250514", "google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-r1"],
    ),
    "siliconflow": ProviderConfig(
        name="SiliconFlow",
        provider_type="openai_compatible",
        base_url="https://api.siliconflow.cn/v1",
        model="deepseek-ai/DeepSeek-V3",
        max_tokens=16384,             # SiliconFlow 默认 16K
        description="硅基流动 多模型推理平台",
        available_models=["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-32B-Instruct", "THUDM/glm-4-9b-chat", "meta-llama/Llama-3.3-70B-Instruct"],
    ),
    "mistral": ProviderConfig(
        name="Mistral AI",
        provider_type="openai_compatible",
        base_url="https://api.mistral.ai/v1",
        model="mistral-large-latest",
        max_tokens=131072,            # Mistral Large 最大输出 128K
        description="Mistral Large / Small / Codestral 系列",
        available_models=["mistral-large-latest", "mistral-small-latest", "codestral-latest", "mistral-saba"],
    ),
    "perplexity": ProviderConfig(
        name="Perplexity",
        provider_type="openai_compatible",
        base_url="https://api.perplexity.ai",
        model="sonar-pro",
        max_tokens=8192,              # Perplexity 最大输出 8K
        description="Perplexity Sonar 搜索增强模型 - 支持实时联网",
        available_models=["sonar-pro", "sonar", "sonar-reasoning"],
    ),
    "fireworks": ProviderConfig(
        name="Fireworks AI",
        provider_type="openai_compatible",
        base_url="https://api.fireworks.ai/inference/v1",
        model="accounts/fireworks/models/llama-v3p1-405b-instruct",
        max_tokens=16384,             # Fireworks 默认 16K
        description="Fireworks AI 高速推理 - Llama/Mixtral/DeepSeek 等",
        available_models=["accounts/fireworks/models/llama-v3p1-405b-instruct", "accounts/fireworks/models/llama-v3p1-70b-instruct", "accounts/fireworks/models/llama-v3p1-8b-instruct", "accounts/fireworks/models/mixtral-8x7b-instruct", "accounts/fireworks/models/deepseek-v3"],
    ),
    "cohere": ProviderConfig(
        name="Cohere",
        provider_type="openai_compatible",
        base_url="https://api.cohere.com/v1",
        model="command-r-plus",
        max_tokens=4096,              # Cohere 最大输出 4K
        description="Cohere Command R/R+ 企业级 RAG 模型",
        available_models=["command-r-plus", "command-r"],
    ),
    "minimax": ProviderConfig(
        name="MiniMax (海螺AI)",
        provider_type="openai_compatible",
        base_url="https://api.minimax.chat/v1",
        model="abab6.5s-chat",
        max_tokens=8192,              # MiniMax abab6.5 最大输出 8K
        description="MiniMax 海螺AI - ABAB 系列大模型",
        available_models=["abab6.5s-chat", "abab6.5-chat"],
    ),
    "stepfun": ProviderConfig(
        name="阶跃星辰 (StepFun)",
        provider_type="openai_compatible",
        base_url="https://api.stepfun.com/v1",
        model="step-2-16k",
        max_tokens=16384,             # Step-2 最大输出 16K
        description="阶跃星辰 Step 系列大模型",
        available_models=["step-2-16k", "step-1-8k", "step-1-32k", "step-1-128k", "step-1-flash"],
    ),
    # ── 本地模型 (Ollama / LM Studio / vLLM 等) ──
    "ollama": ProviderConfig(
        name="Ollama (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:11434/v1",
        model="qwen2.5:7b",
        max_tokens=131072,
        description="Ollama 本地推理服务 - 一键管理模型",
        available_models=[],  # 模型列表由 /api/tags 动态获取
    ),
    "lmstudio": ProviderConfig(
        name="LM Studio (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:1234/v1",
        model="local-model",
        max_tokens=131072,            # 本地模型取 128K
        description="LM Studio 本地推理服务 - 图形界面管理模型",
        available_models=["local-model"],
    ),
    "vllm": ProviderConfig(
        name="vLLM (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:8000/v1",
        model="default",
        max_tokens=131072,            # 本地模型取 128K，vLLM 启动参数控制
        description="vLLM 高性能推理引擎 - 适合生产环境",
        available_models=["default"],
    ),
    "llamacpp": ProviderConfig(
        name="llama.cpp (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:8080/v1",
        model="local",
        max_tokens=131072,
        description="llama.cpp server - 轻量 GGUF 模型推理",
        available_models=["local"],
    ),
    # ── 自定义 ──
    "custom": ProviderConfig(
        name="自定义 OpenAI 兼容",
        provider_type="openai_compatible",
        base_url="http://localhost:11434/v1",
        model="default",
        max_tokens=131072,            # 自定义端点取 128K，用户按需调整
        description="任意符合 OpenAI API 格式的端点",
        available_models=["default"],
    ),
    # ⚠️ bailian ProviderConfig 已移除（含 MaaS 端点）
}

```
