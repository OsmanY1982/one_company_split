## 第三章 · 依赖管理（deps.py）

### 故事从一次启动报错开始

项目开发环境用了 miniconda3 的 Python 3.11。但 `.command` 启动脚本里写死了 `/usr/bin/python3`（系统自带的 Python 3.9）。结果：

- conda 环境装了一堆包（PyQt5、sounddevice、whisper）
- 启动脚本调用系统 Python，系统 Python 什么都没有
- 报错：`ModuleNotFoundError: No module named 'PyQt5'`

修复了启动脚本指向 conda Python 后，下一个问题来了：**打包成 .app 后，应用内部没有 pip**。用户点击语音按钮，代码里 `subprocess.run(['pip', 'install', 'faster-whisper'])` 直接报错。

### deps.py 的诞生

核心思路：**把所有第三方依赖的 wheel 文件预下载到项目里，运行时按需安装——不走 pip，直接解压 zip**。

技术细节：
- `_find_deps_dir()`：自动定位 deps 目录。开发模式下是项目根目录的 `deps/`，打包模式下是 `sys._MEIPASS/deps/`
- `ensure(*module_names)`：检查模块是否已可导入 → 不可用则从 deps 找对应的 wheel → zipfile 解压到 site-packages → 再次验证导入
- 模块级单例缓存：用 `_installed` 集合记录已成功的模块，避免重复操作
- `_get_site_packages()`：兼容虚拟环境和系统环境

### 为什么不用 pip？

1. 打包后的 .app 没有 pip 可执行文件
2. pip 会联网，离线环境不可用
3. pip 安装过程不可控（可能升级依赖、修改其他包）

直接用 zipfile 解压 wheel 是最简单、最可靠的方式。wheel 本质就是一个 zip 文件，解压到 site-packages 就等于「安装」。

### 当前库存：44 个 wheel，67MB

| 功能域 | 依赖 |
|--------|------|
| 语音识别 | sounddevice, faster-whisper, ctranslate2, onnxruntime, huggingface-hub, tokenizers |
| 扫码 | pyzbar, qrcode, Pillow |
| 网络请求 | httpx, requests, urllib3, certifi |
| 安全加密 | bcrypt, cryptography |
| 工具 | PyYAML, beautifulsoup4, numpy |

打包策略：deps/ 随 .app 一起打包（`--add-data deps:deps`），默认不安装。用户第一次使用某功能时自动触发安装，之后持久化到 site-packages。未用到的依赖不占空间。

### 未来计划

- 加入版本管理：当前所有 wheel 是手动下载的，没有锁定版本号。后续应该用 `requirements-freeze.txt` 管理
- 去重：有些 wheel 的依赖有重叠（如 numpy 被多个包依赖），目前会重复解压

---
