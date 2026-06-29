## 第二章 · 数据层（data.py）

### SQLite 的选择

一开始就确定了 SQLite。原因是：

- **单人系统不需要并发**：MySQL/PostgreSQL 的并发优势在这里完全没用
- **零配置**：用户不用装数据库、不用起服务、不用配端口
- **便携**：整个数据库就是一个文件，备份就是 `cp`

但 SQLite 有一个陷阱：WAL 模式下的 `.db-wal` 和 `.db-shm` 文件。如果不理解 WAL 的工作原理，打包和迁移时会丢数据。花了一个下午研究 WAL checkpoint 机制，最终在关闭连接时强制 `PRAGMA wal_checkpoint(TRUNCATE)`。

### 数据库设计原则

一人公司的数据库设计有一个铁律：**每个业务域独立建库**。

| 数据库文件 | 用途 | 核心表 |
|-----------|------|--------|
| `member.db` | 企业成员身份 | members, sessions |
| `staff.db` | 员工档案 | staff, attendance |
| `wallet.db` | 财务钱包 | transactions, wallets |
| `distribution.db` | 分销/业务数据 | distribution_records |
| `settings.db` | 系统配置 | settings, theme |
| `order.db` | 订单数据 | orders, order_items |
| `product.db` | 产品库存 | products, inventory_log |
| `customer.db` | 客户信息 | customers, follow_ups |
| `finance.db` | 财务流水 | income, expense |

为什么不用一个库多个表？因为：
1. 单人身量下，每个域的数据量不大，分开管理更清晰
2. 备份时可以按域选择性备份（比如只备份财务数据）
3. 迁移方便——可以直接把 `wallet.db` 拷贝到新版本

### 翻车：db-wal 文件丢失导致数据损坏

打包时 `.spec` 文件没有正确处理 `.db-wal` 文件。用户第一次安装后，macOS 的代码签名机制误删了 WAL 日志，导致数据库提示 `database disk image is malformed`。

修复方案：在 `data.py` 的 `init_all_dbs()` 中加入了自动修复逻辑——捕获 `sqlite3.DatabaseError`，自动执行 `PRAGMA integrity_check`，如果失败则从 WAL 恢复或重建。

---
