## 第十六章 · 智能中心总控（intelligence_window.py）

### 星球导航

| 子星球ID | 名称 | 功能 | 文件 |
|----------|------|------|------|
| ai_chat | AI助手 | LLM接入+离线兜底 | ai_chat_window.py (224行) + 3子模块 |
| ai_center | 智能中心 | AI能力总览（轨道式滚动区+真实报表洞察） | ai_center_window.py (343行) |
| tools | 工具箱 | 4工具集 | tools_window.py (237行) |
| scan | 扫码工具 | 二维码生成/解析 | scan_window.py (223行) |

### AI助手（ai_chat_window.py）

656 行代码，2026-06-11 重写并模块化拆分。核心改进：

**模块化拆分（2026-06-11）**：原 656 行单文件拆为 4 个文件：
- `ai_chat_window.py`（224行）：核心 UI + LLM 管理 + 交互入口
- `ai_chat_styles.py`（45行）：样式常量 + 路径常量
- `llm_config_dialog.py`（163行）：LLM 配置对话框（API Key/Endpoint/Model）
- `offline_analyzer.py`（322行）：`gather_context()` 上下文收集 + `offline_analysis()` 离线引擎

**LLM 接入**：新增 `LLMConfigDialog` 配置对话框，支持用户填写 API Key / Endpoint / Model。LLM 配置持久化到 `data/llm_config.json`。对话时优先调用 LLM（通过 `core.llm_client`），调用失败自动降级为离线关键词匹配引擎。

**上下文注入**：`_gather_context` 方法在每次对话时收集当前业务数据（钱包余额、订单数、库存预警等）作为 LLM 上下文前缀，让 AI 无需用户解释背景即可回答业务问题。

**离线兜底**：保留原有关键词匹配引擎，LLM 不可用时自动切换，确保离线可用。右下角「LLM 设置」按钮可打开配置对话框。

### 知识库（vault_window.py）

用户可以把常用文档、合同模板、产品手册导入知识库。Agent 在回答时会从知识库检索相关内容。

实现：本地向量存储 + 关键词检索（目前是简单匹配，未来计划用 embedding 做语义搜索）。

### 扫码工具（scan_window.py）

223 行代码，支持：
- 文本输入生成二维码（qrcode 库，PNG 保存）
- 图片文件解析二维码（pyzbar + Pillow）
- 手动输入条码解析
- 解析历史记录表格（支持清空）

### 工具箱（tools_window.py）

237 行，4 工具导航入口（2×2 网格卡片布局）：
- **文本编辑器**：路由到 EditorWindow
- **密码保险箱**：路由到 VaultWindow
- **扫码工具**：路由到 ScanWindow
- **计算器**：内嵌 CalcDialog，支持四则运算 + 表达式求值

### 编辑器（editor_window.py）

287 行，Markdown 编辑器（2026-06-11 增强）：
- 打开/保存/加密保存文本文件（.txt / .md / .py / .json / .html / .csv）
- 加密文件使用 VLT 格式（PBKDF2 + XOR），支持密码验证
- **Markdown 实时预览**：QSplitter 拆分窗格（左编辑右预览），"预览"按钮开关，"实时"复选框控制即时刷新
- 自包含零依赖 _md_to_html() 渲染引擎，支持 10 种语法（标题/粗体/斜体/代码块/行内代码/列表/链接/引用/删除线/水平线）
- 状态栏显示字数和行数

---

## 悬浮球菜单三层架构（2026-06-22 对齐）

> 三个子项目共用同一套悬浮球框架（FloatingPlanetMenuMixin），但各自覆盖菜单定义，
> 形成独立的功能入口。

### 第一层：三个子项目

| 子项目 | 目录 | 定位 | 主分类数 |
|--------|------|------|---------|
| management-system | `management-system/` | 个人系统管理 | 5 |
| iqra | `iqra/` | Iqra AI 平台 | 1 |
| planetarium | `planetarium/` | 天文馆 | 1 |

### 第二层：主分类 → 第三层：子模块

#### management-system（个人系统管理）

| 主分类 | 子模块（module_id） |
|--------|-------------------|
| **业务管理** | order(订单), product(产品), customer(客户), finance(财务), distribution(分销), staff(员工), member(成员), wallet(钱包) |
| **数据中心** | report(报表中心), bi(商业智能), chart(可视化图表) |
| **账号与安全** | password(修改密码), upgrade(升级会员), backup(数据备份), update(检查更新) |
| **工具箱** | editor(编辑器), vault(保险箱), calculator(计算器), scanner(扫码工具) |
| **系统管理** | system_settings(系统设置), activation(激活码), cloud_sync(云端同步), cloud_server(云服务器), system_logs(系统日志), admin(后台管理) |

#### iqra（Iqra）

| 主分类 | 子模块（module_id） |
|--------|-------------------|
| **AI助手** | iqra_chat(AI对话), super_intelligence(超级智能), enhanced_chat(增强对话), knowledge_base(知识库), system_monitor(系统监控), quick_actions(快捷操作), anomaly_detector(异常检测), recommendation_engine(推荐引擎), data_visualization(数据可视化), smart_workflow(智能工作流), business_ai(商业AI), voice_interface(语音接口) |

#### planetarium（天文馆）

| 主分类 | 子模块（module_id） |
|--------|-------------------|
| **天文馆** | solar_system(太阳系浏览), star_catalog(星谱探索) |

### 菜单位置

| 子项目 | 菜单文件 |
|--------|---------|
| management-system | `modules/floating_planet_menu_mixin.py` |
| iqra | `intelligence/floating_planet_menu_mixin.py` |
| planetarium | `intelligence/floating_planet_menu_mixin.py` |

---

# 第五卷 · 数据与系统

> 数据是燃料，系统是引擎。这一卷涵盖数据可视化和系统维护。
