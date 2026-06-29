## 文件命名

| 类型 | 规约 | 示例 |
|------|------|------|
| 窗口/对话框 | `*_window.py` / `*_dialog.py` | `login_window.py`, `update_dialog.py` |
| 服务/管理器 | `*_service.py` / `*_manager.py` | `auth_service.py` |
| 核心库 | 简短名词 | `cosmic.py`, `agent.py`, `voice.py` |
| 数据层 | `*_base.py` | `order_base.py`（计划中） |


## 类命名

- PyQt 组件：`*Window(QMainWindow)` / `*Dialog(QDialog)` / `*Widget(QWidget)`
- 核心服务：`*Core` / `*Service` / `*Manager`
- 线程：`*Thread(QThread)`


## QSS 样式约定

- 所有样式用 `setStyleSheet()` 内联或对象名选择器（`#object_name`）
- 颜色统一用 `rgba()` 格式，避免 `#RRGGBB` 硬编码
- 辉光渐变统一用 `QRadialGradient` + `QLinearGradient`
- 禁止使用系统默认样式表覆盖


## 数据访问约定

- 所有 SQL 操作通过 `core/data.py` 提供的数据库路径常量访问
- 禁止在 UI 模块中硬编码数据库路径
- 事务性操作使用 `with db:` 上下文管理器

---

# 附录 D · 常见调试命令
