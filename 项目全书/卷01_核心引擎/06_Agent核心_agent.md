## 第六章 · Agent 核心（agent.py）

### AI 不是聊天框，是操作中枢

市面上大多数「AI 软件」的做法是：一个聊天框 + 一个 LLM。用户打字，AI 回复。仅此而已。

一人公司的 Agent 不同。它能**操作**：创建订单、查询库存、生成报表、打开窗口。

`agent.py` 的核心是 `AgentCore` 类 + `CommandIntent` 数据结构：

```
用户输入 → 规则引擎解析意图 → 匹配命令 → 执行操作 → 返回结果
```

### CommandIntent 设计

```python
@dataclass
class CommandIntent:
    action: str      # open / query / create / delete / analyze / system_query / help / exit
    target: str      # 目标模块或对象
    params: dict     # 附加参数
```

规则引擎不是 LLM，是硬编码的正则 + 关键词匹配。为什么不用 LLM 做意图识别？因为：

1. **延迟**：LLM 响应 2-5 秒，规则引擎 1 毫秒
2. **确定性**：「帮我查一下库存」必须 100% 触发库存查询，不能有概率
3. **离线可用**：Ollama 没启动时，规则引擎照样工作

### 处理器注册机制

`register_handler(action, callback)` — 每个 action 对应一个 handler。Dashboard 在初始化时注册了 8 个 handler（open/query/create/delete/analyze/system_query/help/exit）。这种注册机制让 Agent 核心保持通用性，各模块自行决定如何处理命令。

### 双引擎架构

Dashboard 收到用户输入后：
1. 如果有 LLM 配置 → LLM 生成回复文本 + 规则引擎并行检查是否需要打开模块
2. 如果无 LLM → 纯规则引擎处理
3. LLM 异常时自动降级到规则引擎

未来计划：LLM 作为规则引擎的 fallback。规则引擎没匹配到时，才走 LLM。这样既保证了常用操作的响应速度，又保持了对模糊指令的兼容。

---

# 第二卷 · 认证与人事

> 有人才能有公司。第一卷造好了飞船引擎，这一卷解决「谁在开这艘飞船」。
