---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b11c9da246eaa2aacfce94adf18e4927_e957212073b211f1897e5254002afed2
    ReservedCode1: mZ7v56spHyuDRKzmFlveFftZyhgVFkY8Y0EcWcLMBBO0ggjc3JV8AF4HB6H6XvVNE/8CZfELFawijnfDQ7j3MMBRRRJg+lFuzPBI+Ux/MBeY5FCHK0EIdEI1HB6yVU+pQmBZ5m/pr6L1nD5bOlh6uwEM8I5oONMDqwiN7+EfvfeW8/+fDlOfkWX24Bg=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b11c9da246eaa2aacfce94adf18e4927_e957212073b211f1897e5254002afed2
    ReservedCode2: mZ7v56spHyuDRKzmFlveFftZyhgVFkY8Y0EcWcLMBBO0ggjc3JV8AF4HB6H6XvVNE/8CZfELFawijnfDQ7j3MMBRRRJg+lFuzPBI+Ux/MBeY5FCHK0EIdEI1HB6yVU+pQmBZ5m/pr6L1nD5bOlh6uwEM8I5oONMDqwiN7+EfvfeW8/+fDlOfkWX24Bg=
---

# iqra vs Codex vs Claude Code：差异化能力设计

> 2026-06-29，基于三款产品最新状态

---

## 一、竞品能力矩阵

| 维度 | Codex (OpenAI) | Claude Code (Anthropic) | iqra (当前) |
|------|---------------|------------------------|-------------|
| **运行模式** | 桌面 App（GUI 原生） | 终端 CLI | Python 库 + CLI |
| **模型策略** | GPT-5 云端 | Claude Opus/Sonnet 云端 | **任意后端**（Ollama本地 / 云端API） |
| **离线可用** | 否 | 否 | **是（Ollama）** |
| **Sub-Agent** | 并行 Agent（沙盒隔离） | Agent Teams（分工协作） | 无 |
| **工具扩展** | 90+ Plugins + MCP | MCP 协议 | 35 个内置工具，无 MCP |
| **项目记忆** | 偏好学习 | CLAUDE.md | 无 |
| **权限控制** | 隐式 | 5 级显式模式 | 无 |
| **Computer Use** | 沙盒虚拟桌面（macOS） | 屏幕读取 + 有限操控 | 无 |
| **内置浏览器** | 有（前端迭代） | 无 | 无 |
| **SSH 远程** | 有 | MCP 间接 | 无 |
| **Hooks/自动化** | 排程任务 | Hooks + Routines + Skills | 无 |
| **CONTEXT窗口** | 中等 | **1M token** | 取决于后端模型 |
| **代码质量定位** | 快速迭代、vibe coding | 深度推理、工程严谨 | 待定义 |
| **工作区隔离** | 虚拟桌面沙盒 | Git Worktree (-w) | 无 |
| **后台运行** | 有（Automations） | 有（--bg） | 无 |
| **会话管理** | 有（记忆） | 有（sessions list/resume） | 无 |
| **管道/CI集成** | 有限 | 强（-p 模式 + JSON输出） | 无 |

---

## 二、iqra 的不可替代定位

两者共同的致命弱点：**必须联网 + 必须付费 + 数据离境**。

iqra 唯一能做到的：
1. **完全离线** — Ollama 本地推理，代码永不离开本机
2. **零成本** — 无 API 账单，无 token 计费
3. **数据主权** — NDA 代码、金融数据、医疗记录无需上传
4. **模型自由** — 今天用 qwen2.5:7b，明天切 gemma4:hermes，后天接 deepseek API

这是 iqra 的"根能力"。所有差异化设计必须从这个根长出来。

---

## 三、核心能力架构设计

### 第一层：地基 — 模型无关的 Agent 引擎

**现状**：AgentLoop 硬上限 5 轮，无自主规划。

**目标**：

```
用户输入
  │
  ├─ 意图分类器（本地小模型，<100ms）
  │   ├─ 闲聊 / 问答 → 直接对话模式
  │   ├─ 简单操作（单文件读写）→ 1-3 轮工具调用
  │   └─ 复杂任务（多步规划）→ 进入 Agent Loop
  │
  └─ Agent Loop（自主规划引擎）
      ├─ 任务分解（Think 阶段）
      ├─ 工具选择 + 执行（Act 阶段）
      ├─ 结果验证（Observe 阶段）
      └─ 循环直到完成或超限
          ├─ 默认上限：30 轮（可配置）
          ├─ 卡死检测：连续 3 轮无进展 → 请求用户介入
          └─ 成本控制：每轮 token 预算检查（云端模式）
```

**关键设计决策**：
- 不用固定轮数上限，改用**目标完成度判定** + **卡死检测**
- 复杂任务自动降级：本地模型能力不够 → 提示切换云端模型
- Think 阶段输出对用户可见（透明度）

---

### 第二层：Sub-Agent 多智能体协作

**对标**：Claude Code Agent Teams + Codex 并行 Agent

**设计**：

```
Main Agent（编排者）
  │
  ├─ Code Agent      — 代码读写、重构、测试生成
  ├─ Search Agent    — 代码库搜索、文档检索、RAG
  ├─ Shell Agent     — 命令执行、环境管理、git 操作
  ├─ Review Agent    — 代码审查、安全检查、最佳实践
  └─ File Agent      — 文件整理、格式转换、批量操作
```

**两套模式**：
1. **顺序模式**（默认）：Agent 按依赖关系串行执行，结果逐级传递
2. **并行模式**（--parallel）：多个独立 Agent 同时跑（Codex 风格），用文件锁避免冲突

**Agent 通信协议**：
- 每个 Sub-Agent 有自己的 System Prompt + 工具白名单
- Agent 间通过结构化消息传递结果（JSON）
- 主 Agent 负责合并输出、冲突裁决

**与 Claude Code Sub-Agent 的本质区别**：
- Claude Code 的 Sub-Agent 共享同一个 Claude 模型
- iqra 的 Sub-Agent **可以跑不同模型**：Review Agent 用 gemma4:hermes（推理强），Shell Agent 用 qwen2.5:7b（快），主 Agent 用 qwen3.6:35b（大局观）

---

### 第三层：项目记忆系统 (.iqra.md)

**对标**：CLAUDE.md + Codex Memory

**设计**：

```
项目根目录
├── .iqra.md              ← 项目级记忆（提交到 Git）
│   ├── 技术栈
│   ├── 代码规范
│   ├── 架构决策
│   └── 常用命令
│
└── .iqra/
    ├── memory.json       ← 个人偏好（不提交 Git）
    │   ├── 命名习惯
    │   ├── 偏好模型
    │   └── 权限设置
    │
    └── sessions/         ← 会话存档
        ├── 2026-06-29_refactor-auth.json
        └── 2026-06-28_fix-login-bug.json
```

**自动学习机制**：
- 用户连续 3 次纠正同一类错误 → 写入 `.iqra/memory.json`
- 用户说"记住：XXX" → 立即写入
- 每次 Agent 启动自动加载 `.iqra.md` + `.iqra/memory.json`
- 跨会话记忆：上次改了什么文件、用了什么命令、卡在什么问题

**与 CLAUDE.md 的区别**：
- CLAUDE.md 是纯手动编写；iqra 会自动建议记忆条目
- CLAUDE.md 只有项目级；iqra 分离项目约定（提交 Git）与个人偏好（本地）

---

### 第四层：MCP 协议支持

**对标**：两者都支持 MCP

**设计**：

```
.iqra/mcp.json
{
  "mcpServers": {
    "github": {
      "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "$GITHUB_TOKEN" }
    },
    "postgres": {
      "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
    },
    "filesystem": {
      "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    }
  }
}
```

**实现路径**：
- 内嵌 MCP 客户端（Python 实现，不依赖 Node.js）—— 对本地模型是关键优化
- MCP 工具自动注册到 Tool Registry
- MCP 工具调用走 Agent Loop 的权限检查

---

### 第五层：权限与安全模式

**对标**：Claude Code 5 级权限

**设计**：

| 模式 | 文件读写 | Shell 执行 | 网络访问 | 适用场景 |
|------|---------|-----------|---------|---------|
| `restricted` | 只读 | 禁止 | 禁止 | 代码审查 |
| `ask`（默认） | 每次确认 | 每次确认 | 每次确认 | 日常开发 |
| `auto-edit` | 自动 | 确认 | 确认 | 信任项目 |
| `auto` | 自动 | 自动 | 自动 | 个人项目 |
| `sandbox` | Docker 隔离 | 容器内 | 白名单 | 不信任代码 |

**与 Claude Code 的区别**：
- 新增 `restricted` 模式（更安全的下限）
- 新增 `sandbox` 模式（Docker 隔离执行）—— 本地模型跑不受信代码的最后防线

---

### 第六层：工作区隔离

**对标**：Codex 虚拟桌面 + Claude Code Worktree

**设计**：

```
iqra --sandbox          # Git Worktree 隔离（轻量）
iqra --sandbox=docker   # Docker 容器隔离（安全）
```

- **Git Worktree 模式**：`iqra -w feature-x`，在独立 worktree 操作，不影响当前工作区
- **Docker Sandbox 模式**：所有文件操作和命令在容器内执行，宿主机只读

---

### 第七层：Hooks 与自动化管道

**对标**：Claude Code Hooks + Codex Automations

**设计**：

```json
// .iqra/hooks.json
{
  "pre_edit": "echo 'About to edit files...'",
  "post_edit": "git diff --stat",
  "pre_commit": "pytest -x --lf",
  "post_commit": "git log -1 --oneline",
  "on_error": "echo 'Agent failed' | terminal-notifier -title iqra"
}
```

**事件钩子**：
- `pre_task` / `post_task` — 任务前后
- `pre_edit` / `post_edit` — 文件修改前后
- `pre_exec` / `post_exec` — 命令执行前后
- `on_error` / `on_success` — 任务结果
- `on_idle` — 长时间无输入时的提醒

**定时任务**（Codex Automations 对标）：
```bash
iqra --cron "0 9 * * 1" "整理上周 PR review 并生成周报"
iqra --bg "监控 CI 状态，失败时通知我"
```

---

### 第八层：内置浏览器

**对标**：Codex 内置浏览器

**设计**：
- 不绑 Chromium（太重），用 Playwright 按需启动
- 前端开发场景：Agent 改完 CSS → 截图对比 → 继续迭代
- Web 操作场景：登录、表单填写、数据抓取
- 浏览器操作走权限检查

---

### 第九层：会话与对话管理

**对标**：Claude Code sessions + Codex 会话记忆

**设计**：

```bash
iqra session list              # 列出历史会话
iqra session resume <id>       # 恢复会话
iqra session fork <id>         # 分叉会话
iqra session export <id>       # 导出会话（JSON）
iqra --continue                # 继续最近会话
```

**跨会话上下文**：
- 自动记录：修改了哪些文件、遇到了什么错误、用户做了什么决策
- 新会话自动加载最近 N 次会话的摘要

---

## 四、三阶段实施路线

### Phase 1：核心 Agent 能力（1-2 周）

1. **Agent Loop 升级**：移除 5 轮上限 → 目标驱动 + 卡死检测
2. **Sub-Agent 架构**：基础设施（Agent 注册、通信协议、工具白名单）
3. **项目记忆 .iqra.md**：读写 + 自动加载
4. **权限模式**：`restricted` / `ask` / `auto` 三级

**交付标准**：能跑完整的多步骤编程任务，不卡死在 5 轮。

### Phase 2：工程化能力（2-4 周）

5. **MCP 客户端**：内嵌 Python 实现，至少对接 GitHub / Filesystem / Postgres
6. **Worktree 隔离**：`-w` 模式
7. **Hooks 系统**：pre/post 钩子 + 定时任务
8. **会话管理**：list / resume / fork / export
9. **管道模式**：`-p` 非交互执行 + JSON 输出

**交付标准**：可替代 Claude Code 做日常开发的 80% 场景。

### Phase 3：高级能力（4-8 周）

10. **内置浏览器**：Playwright 集成 + 前端迭代工作流
11. **Docker Sandbox**：全隔离执行环境
12. **模型路由**：自动按任务类型选择最优本地模型
13. **IDE 插件**：VSCode / PyCharm 集成
14. **并行 Agent**：多 Agent 同时跑不冲突

**交付标准**：完整对标 Claude Code + Codex，且离线可用。

---

## 五、差异化总结

| | Codex | Claude Code | iqra（设计目标） |
|---|---|---|---|
| 离线 | 否 | 否 | **是** |
| 免费 | 否 | 否 | **是（本地模型）** |
| 模型自由 | 仅 OpenAI | 仅 Anthropic | **任意后端** |
| 多模型 Agent | 否 | 否 | **是（不同 Agent 用不同模型）** |
| 数据主权 | 云端 | 云端 | **本地** |
| 代码开源 | 否 | 否 | **是** |

**iqra 不是"另一个 Codex 或 Claude Code"**。它是**本地优先、模型无关、隐私至上的自主编程 Agent**。在上述基线上，叠加 MCP/Hooks/Sub-Agent/Sandbox 等现代 Agent 工程实践，但始终保持"离线可用"这条红线不妥协。
*（内容由AI生成，仅供参考）*
