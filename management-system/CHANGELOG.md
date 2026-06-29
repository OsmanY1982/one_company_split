---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b11c9da246eaa2aacfce94adf18e4927_9b506ce8653111f1af8f5254002afed2
    ReservedCode1: +YIxB8tkA7SfR/531DgWVsXBOLB/l3RNb5g75oE61jp9bfN7zLsmPasmapg8/jD86QECillSE6Lal804T8RvkgbqOhnhcar4/sEimc/iy2zEGJTOARy0Gp6S2EDvW6Sr6sHJzcuwuo8KABvPol0/XPYcm+U2lqEWcblMHcMPh7U0tdlWoxdTLIetXhQ=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b11c9da246eaa2aacfce94adf18e4927_9b506ce8653111f1af8f5254002afed2
    ReservedCode2: +YIxB8tkA7SfR/531DgWVsXBOLB/l3RNb5g75oE61jp9bfN7zLsmPasmapg8/jD86QECillSE6Lal804T8RvkgbqOhnhcar4/sEimc/iy2zEGJTOARy0Gp6S2EDvW6Sr6sHJzcuwuo8KABvPol0/XPYcm+U2lqEWcblMHcMPh7U0tdlWoxdTLIetXhQ=
---

# 版本更新日志

## v1.0.0 — 2026-06-11

### HUD 穿透修复全覆盖（7 文件）
修复所有模块中交互控件父级为 CosmicBackground（设有 WA_TransparentForMouseEvents）导致 macOS 26.x 鼠标事件被拦截的问题。涉及 system_window、data_window、intelligence_window、tools_window、login_window、connect_window、dashboard_window。

### AI设计规范移至项目根目录
设计规范文件从桌面移至项目根目录 `AI设计规范.txt`，每个项目独立持有自己的宪法。

### 文档体系深度模块化
项目全书从单文件拆分为 33 个按章独立的分片文件（7 卷子目录），源码全书拆分为 55 个按模块独立的分片文件。查找粒度从翻几十页降至直接打开对应文件。

### 回滚管控系统上线
新增 rollback_control.py（278 行），三条铁律：禁止全局回滚、逐模块申请、审计日志。受保护区域：core/、main.py、gen_book.py、data/、项目全书/、源码全书/。

### 检查更新 UI 模块
新增 update_dialog.py，支持版本号显示和更新日志查看。

### 底部快捷栏
Dashboard 新增底部功能栏：激活许可证、升级账号、检查更新、修改密码、数据备份、退出登录。

---

## v0.9.0 — 2026-06-10

### 初始宇宙构建
核心引擎（cosmic.py 深空渲染、data.py 多库架构、deps.py 依赖懒安装、llm_client.py 6 后端统一、agent.py 规则引擎、voice.py faster-whisper）、认证人事（login_window 地球仪登录、connect_window 引擎舱、personnel 人员四模块）、业务运营（business 订单/产品/客户/财务）、智能中枢（intelligence AI助手/数字员工/扫码/知识库/工具箱）、数据中心（data_center 报表/BI大屏）、系统管理（system 基础信息/激活码/云端同步/系统日志）。
*（内容由AI生成，仅供参考）*
