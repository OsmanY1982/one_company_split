## 身份认证（auth 相关）

### `member.db` — members 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| username | TEXT UNIQUE | 登录用户名 |
| password_hash | TEXT | bcrypt 哈希（cost=12） |
| role | TEXT | admin / member |
| membership | TEXT | trial / vip / permanent |
| expire_at | TEXT | 到期时间（ISO 格式） |
| company_name | TEXT | 企业名称 |
| contact_email | TEXT | 联系邮箱 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### `member.db` — sessions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| username | TEXT | 关联用户名 |
| login_time | TEXT | 登录时间 |
| ip_address | TEXT | 登录 IP |
| is_active | INTEGER | 是否活跃（0/1） |


## 业务运营

### `order.db` — orders 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 订单号 |
| customer_name | TEXT | 客户名称 |
| product_name | TEXT | 商品名称 |
| amount | REAL | 金额 |
| status | TEXT | 待处理/已完成/已取消 |
| order_date | TEXT | 下单日期 |
| notes | TEXT | 备注 |

### `product.db` — products 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 产品编号 |
| name | TEXT | 产品名称 |
| category | TEXT | 分类 |
| price | REAL | 单价 |
| stock | INTEGER | 库存数量 |
| min_stock | INTEGER | 最低库存阈值 |
| barcode | TEXT | 条码 |
| created_at | TEXT | 创建时间 |

### `customer.db` — customers 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 客户编号 |
| name | TEXT | 姓名 |
| phone | TEXT | 手机号 |
| email | TEXT | 邮箱 |
| notes | TEXT | 备注（自由文本） |
| last_contact | TEXT | 最后联系时间 |
| created_at | TEXT | 创建时间 |

### `finance.db` — finance_records 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 记录编号 |
| type | TEXT | income / expense |
| category | TEXT | 分类 |
| amount | REAL | 金额 |
| description | TEXT | 说明 |
| record_date | TEXT | 日期 |
| related_order_id | INTEGER | 关联订单（可空） |
| created_at | TEXT | 创建时间 |


## 人员管理

### `staff.db` — staff 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 员工编号 |
| name | TEXT | 姓名 |
| gender | TEXT | 性别 |
| position | TEXT | 职位 |
| hire_date | TEXT | 入职日期 |
| salary | REAL | 薪资 |
| phone | TEXT | 联系电话 |
| notes | TEXT | 备注 |

### `wallet.db` — transactions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 交易编号 |
| type | TEXT | income / expense / transfer |
| amount | REAL | 金额 |
| category | TEXT | 分类 |
| description | TEXT | 说明 |
| trans_date | TEXT | 交易日期 |
| balance_after | REAL | 交易后余额 |

### `distribution.db` — distribution_records 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 记录编号 |
| channel_name | TEXT | 渠道名称 |
| product_name | TEXT | 分销产品 |
| commission_rate | REAL | 佣金比例 |
| sales_amount | REAL | 销售金额 |
| commission | REAL | 佣金金额 |
| record_date | TEXT | 日期 |
| status | TEXT | 待结算/已结算 |


## 系统配置

### `settings.db` — settings 表

| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT PK | 配置键 |
| value | TEXT | 配置值 |
| updated_at | TEXT | 更新时间 |

常用配置键：
- `theme` — 界面主题（cosmic/dark/light）
- `default_fuel` — 默认 AI 后端类型
- `voice_model` — 语音模型档位（tiny/base/small）
- `backup_dir` — 备份目录路径
- `auto_backup` — 是否开启自动备份（0/1）
- `license_key` — 激活许可证密钥
- `activation_status` — 激活状态
- `last_update_check` — 上次检查更新时间

---

# 附录 B · 打包与分发
