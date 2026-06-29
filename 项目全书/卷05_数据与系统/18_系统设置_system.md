## 第十八章 · 系统设置（system/）

### 总控（system_window.py）

306 行代码，4 颗小星球导航：

| 子星球ID | 名称 | 功能 | 文件 |
|----------|------|------|------|
| base_info | 基础信息 | 企业信息配置 | base_info_window.py (161行) |
| activation | 激活码 | 许可证激活 | activation_window.py (219行) |
| cloud | 云端同步 | 本地数据zip备份/恢复 | cloud_window.py (326行) |
| logs | 系统日志 | 日志查看+过滤 | logs_window.py (210行) |

### 基础信息（base_info_window.py）

161 行代码，企业基本配置：公司名、地址、联系方式、Logo（未来支持）。

### 激活码（activation_window.py）

219 行代码，许可证激活系统：
- 输入激活码 → 验证 → 解锁功能
- 显示当前许可证状态和到期时间
- 支持离线激活（本地密钥校验）

### 云端同步（cloud_window.py）— 2026-06-11 重构

326 行代码，本地数据备份与恢复：
- 导出：`zipfile.ZIP_DEFLATED` 压缩整个 `data/` 目录为 zip，QFileDialog 选择保存位置
- 导入：解压 zip 到临时目录 → 覆盖合并到 `data/`（含二次确认对话框），完成自动清理临时目录
- 存储信息卡片：实时显示数据目录大小（B/KB/MB）和数据库文件数
- 操作日志：`_log_op()` 写入 `system_logs.db` 中 `sync_logs` 表（自动建表，记录 sync_type / status / detail）
- 三套按钮 QSS：BTN_BLUE（浏览）、BTN_GREEN（导出）、BTN_AMBER（导入）

### 系统日志（logs_window.py）

210 行代码，日志查看器：
- 实时滚动 + 级别过滤（INFO/WARNING/ERROR/DEBUG）
- 关键字搜索
- 导出日志文件

### 检查更新（update_dialog.py）— 2026-06-11 重构

318 行代码，独立的 QDialog：
- 显示当前版本号（从 version.txt 读取，不存在则显示 "1.0.0"）
- 读取项目根目录 `CHANGELOG.md` 并解析为 HTML 展示在 QTextEdit 中
- `_parse_changelog()` 正则解析 `## vX.Y.Z — 日期` / `### 标题` / `- 条目` 三层结构
- `_format_changelog_html()` 将解析结果转换为 QTextEdit HTML（版本号绿色、标题紫色、条目灰色）
- 「刷新日志」按钮手动重载 CHANGELOG.md，显示文件修改时间
- 移除了原 QProgressBar / QTimer 模拟 / 硬编码占位文本

---

# 第六卷 · 舰桥主控面板

> 所有模块的指挥中心。Dashboard 是整个应用的第一界面。
