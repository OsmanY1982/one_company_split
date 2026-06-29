## PyInstaller 配置

项目使用 PyInstaller 打包为 macOS .app：

```
pyinstaller --windowed --name "一人公司" \
  --add-data "deps:deps" \
  --add-data "data:data" \
  --hidden-import PyQt5 \
  --hidden-import sounddevice \
  --hidden-import ctranslate2 \
  main.py
```

关键注意事项：
1. `deps/` 和 `data/` 目录必须随包分发
2. macOS 代码签名：`--codesign-identity` + entitlements
3. WAL 模式数据库的 `.db-wal` 和 `.db-shm` 文件需特殊处理


## 已知打包问题

| 问题 | 状态 | 解决方案 |
|------|------|----------|
| faster-whisper 模型包体过大 | ✅ 已解决 | 按需下载，不在打包时包含 |
| .db-wal 签名被清 | ✅ 已解决 | data.py 自动修复逻辑 |
| macOS Gatekeeper 警告 | ⚠️ 持续 | 需 Apple Developer 证书 |
| PyQt5 在 macOS 15+ 的渲染异常 | 🔲 待观察 | 暂无用户报告 |


## 启动流程

```
用户双击 .app
  → main.py 入口
  → deps.py 检测依赖（按需安装 wheel）
  → data.py 初始化所有数据库（含自动修复）
  → LoginWindow 显示登录界面
  → 用户登录 → ConnectWindow（引擎舱）
  → 配置 AI 引擎 → DashboardWindow（舰桥）
```

---

# 附录 C · 代码规范与约定
