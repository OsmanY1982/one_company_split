## 第四章 · 大模型客户端（llm_client.py）

### 不能只接一个模型

最初只接了 OpenAI。但很快意识到这是死路——用户不愿意把自己的业务数据发给美国的服务器，而且 API Key 需要外币信用卡。

所以设计了一个统一的 `LLMClient`，支持六个后端：

| 燃料类型 | 后端 | 特点 |
|----------|------|------|
| 反物质核心 | Ollama | 本地运行，完全离线，免费 |
| 恒星聚变舱 | OpenAI | 最强，但需要 API Key 和联网 |
| 量子谐振器 | DeepSeek | 中文表现最好，国内可访问 |
| 暗物质引擎 | Claude | 长文本理解最强 |
| 引力波核心 | 通义千问 | 阿里系，国内生态 |
| 未知能源舱 | 自定义 | 兼容 OpenAI API 格式的任何服务 |

### 统一接口设计

所有后端都封装成一致的接口：`chat(messages)` → `response_text`。内部处理：
- 流式/非流式响应的统一（Ollama 是流式，OpenAI 可以选）
- 超时和重试（网络不稳定时自动重试 3 次）
- 错误降级（一个后端挂了，提示用户切到其他后端）

### ModelConfig 数据结构

```python
@dataclass
class ModelConfig:
    model_name: str          # 模型标识（如 gpt-4o, qwen2.5）
    provider: str            # 燃料类型（ollama/openai/deepseek/claude/qwen/custom）
    api_key: str = ""        # API 密钥
    base_url: str = ""       # 自定义服务地址
    temperature: float = 0.7
    max_tokens: int = 2048
```

### 翻车：Ollama 本地模型扫描第一次失败了

`connect_window` 里有一个「扫描本地模型」按钮，调用 `http://localhost:11434/api/tags`。但第一次测试时，Ollama 服务没启动，URL 打不开，整个窗口卡了 15 秒（默认超时）。

修复：加了一个 `ConnectionTestThread(QThread)`，在后台线程做连接测试。测试中按钮显示「测试中...」，测试完显示「畅通 ✓」或「失联」。主线程不再阻塞。

---
