# 一人公司 · 宇宙版

> 一个人 + 一台电脑 = 能运转的最小企业。AI 不是插件，是副驾驶。

[![GitHub release](https://img.shields.io/github/v/release/OsmanY1982/one_company_cosmic?include_prereleases)](https://github.com/OsmanY1982/one_company_cosmic/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20arm64-lightgrey)](https://github.com/OsmanY1982/one_company_cosmic/releases)
[![Lines](https://img.shields.io/badge/code-261K%20lines-4488FF)]()

## 缘起

市面上有 ERP、有 CRM、有财务软件，但它们都是给「公司」用的。一个人用不了——太重、太贵、太多功能根本不需要。

而一个人的最大瓶颈不是功能缺位，是**没有人可以商量**。没有 CFO 帮你分析现金流，没有 CTO 帮你判断技术选型。

一人公司宇宙版就是为这个场景而生的：**一个人 + 一套系统 = 一个公司**。AI 能看见你的数据、理解你的业务、给你建议——它是副驾驶，不是聊天玩具。

---

## 世界观

系统有一个科幻外壳，目的不是炫技，是让非技术用户也能理解这套系统在做什么。

### 引擎舱

你与 AI 之间的翻译层。选择模型（燃料）、注入密钥、点火测试。就像宇宙飞船出发前，先确认引擎能转。

### 舰桥 / Dashboard

日常操作界面。数据、图表、订单、员工、报表全在这里。AI 副驾驶在侧边栏待命。底部快捷栏覆盖所有高频操作——激活许可证、升级账号、修改密码、数据备份、退出登录。

### 五颗星球

五个顶层模块各有「星球身份」，在舰桥中以轨道星球的形式呈现：

| 星球 | 名称 | 颜色 | 核心能力 |
|------|------|------|----------|
| 🟡 | 业务管理 | `#4488FF` | 订单 / 产品 / 客户 / 财务 / 发票 |
| 🟠 | 人员管理 | `#FF6644` | 员工 / 会员 / 钱包 / 分销 / 权限 |
| 🟣 | 智能中心 | `#AA44FF` | AI 助手 / 知识库 / 数字员工 / 扫码 |
| 🟢 | 数据中心 | `#00CCAA` | 报表 / BI 大屏 / 数据导出 |
| 🔵 | 系统设置 | `#8899AA` | 激活码 / 云同步 / 日志 / 备份 |

进入任一星球后，子模块以更小行星环绕展开——这套"递归宇宙"UI 范式是整个项目的视觉签名。

### 燃料体系

| 燃料 | 后端 | 特性 |
|------|------|------|
| 反物质核心 | Ollama（本地） | 离线可用，隐私优先 |
| 恒星聚变舱 | OpenAI | 推理能力最强 |
| 量子谐振器 | DeepSeek | 性价比极高 |
| 暗物质引擎 | Claude | 长文本理解 |
| 引力波核心 | 通义千问 | 中文最优 |

6 个后端统一封装为 LLMClient，一行代码切换。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 界面 | PyQt5 + QPainter | 手绘星空粒子渲染，深空辉光效果 |
| 数据库 | SQLite（本地）+ Supabase（云端） | 9 个独立 .db，域隔离架构 |
| AI | 6 后端统一 LLMClient | Ollama / OpenAI / DeepSeek / Claude / 通义千问 |
| 语音 | faster-whisper (CTranslate2) | 离线语音识别，tiny/base/small 三档 |
| OCR | pyzbar + Pillow | 条码 / 二维码识别 |
| 密码 | bcrypt (cost=12) | 密码哈希与验证 |
| 图表 | Matplotlib | 数据可视化绑定 PyQt |
| 依赖 | 自建 deps.py | wheel 离线安装，不走 pip |
| 打包 | PyInstaller | macOS .app + .dmg 分发 |

---

## 项目规模

| 指标 | 数值 |
|------|------|
| Python 模块 | 648+ 个 |
| 代码行数 | 261,921 行 |
| 数据库 | 9 个独立 .db |
| 第三方 wheel | 44 个（67MB） |
| AI 后端 | 6 个 |
| 顶层星球 | 5 个 + 19 个子星球 |
| 语音方案 | tiny / base / small 三档 |

---

## 下载安装

| 渠道 | 链接 |
|------|------|
| **GitHub Release** | [下载 DMG](https://github.com/OsmanY1982/one_company_cosmic/releases/latest) |
| Gitee（国内镜像） | [前往下载](https://gitee.com/opc1688/one_company_cosmic/releases) |

> **系统要求**：macOS 14+、Apple Silicon（M1/M2/M3/M4）

1. 下载 `OneCompanyCosmic-v*-arm64.dmg`
2. 双击打开，将「一人公司宇宙版.app」拖入 Applications
3. 首次运行若提示"无法验证开发者"，前往 **系统设置 → 隐私与安全性 → 仍要打开**

---

## 参与开发

欢迎贡献代码、反馈问题、提交需求。

```bash
git clone https://github.com/OsmanY1982/one_company_cosmic.git
cd one_company_cosmic
pip install -r requirements.txt
python main.py
```

1. Fork → 2. `git checkout -b feature/xxx` → 3. `git commit -m "feat: xxx"` → 4. Push → 5. PR

---

## 赞助支持

[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-ff69b4)](https://github.com/OsmanY1982)

所有赞助者将列入致谢名单。

---

## 开源协议

[MIT License](LICENSE)

---

**一人公司宇宙版** —— 一个人，也能星辰大海。
