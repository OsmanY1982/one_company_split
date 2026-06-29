## 第九章 · 人员管理（personnel/）

### 不是 HR 系统，是「你的团队」

一人公司的「人员管理」不是大企业的 HR 模块。它更轻量：**一个人的公司，可能只有 2-3 个人**。不需要组织架构图，不需要复杂的权限体系。

### 人员管理总控（personnel_window.py）

736 行代码，采用小星球导航模式。4 颗子星球环绕中心运行：

| 子星球ID | 名称 | 功能 | 对应文件 |
|----------|------|------|----------|
| staff | 员工管理 | 员工档案/考勤 | staff_window.py (290行) |
| member | 会员管理 | 会员列表/到期 | member_window.py (439行) |
| wallet | 钱包管理 | 企业钱包/充值/提现审核 | wallet_window.py (485行) |
| distribution | 分销管理 | 链接追踪+佣金+团队结构 | distribution_window.py (373行) |

### 暖橙主题

人员管理采用暖橙色（#FF6644）配色。不是深空蓝、不是科技紫。因为「人」相关的模块应该给人温暖的感觉——这是一个有意的设计选择，和系统其他模块的冷科幻风格形成对比。

### 员工管理（staff_window.py）

`staff.db` 真实 CRUD，字段包括：姓名、电话、邮箱、职位、薪资、状态、备注。支持 CSV 导入导出。290 行代码，对接 personnel_window.py DAO 共享层。

### 会员管理（member_window.py）

管理企业会员的等级、到期时间、续费记录。439 行代码，对接 member.db 真实 CRUD，包含会员列表、等级筛选、统计卡片、管理员升级功能。

### 钱包管理（wallet_window.py） — 485行

2026-06-11 重写：导入 personnel_window DAO 共享层（staff_get_all/wallet_create/wallet_recharge/wallet_withdraw_request/wallet_get_trans/wallet_stats），不再自建独立数据库。完整功能：充值、提现申请 + 审核流程（WithdrawAuditDialog）、余额卡片、交易流水查询。审核流程为 pending→approved/rejected 状态流转。

### 分销管理（distribution_window.py） — 373行

2026-06-11 重写：适配 personnel_window DAO 新表结构（dist_links 链接追踪 / dist_commissions 佣金明细 / dist_team 团队结构）。三模块：链接列表（7列：用户/邀请码/链接/点击/注册/时间/状态）、佣金明细弹窗（按用户+状态筛选）、团队结构弹窗。代码行数从 545 精简至 373，职责更清晰。

### 2026-06-27 修复：DistributionWindow / WalletWindow 启动方式

DistributionWindow 和 WalletWindow 继承自 QMainWindow（非 QDialog），之前在 `personnel_window.py` 和 `business_window.py` 中误调用了 `exec_()`（QDialog 模态阻塞方法），导致窗口无法打开。已改为 `.show()`。同时 `wallet_window/__init__.py` 补充了 `_do_export_csv` 方法（CSV + QFileDialog，导出钱包列表 + 交易记录双表）。

---
