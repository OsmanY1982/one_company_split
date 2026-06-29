---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b11c9da246eaa2aacfce94adf18e4927_738fbefc656911f19ad75254007bceed
    ReservedCode1: 1zkHLyBUNnUPg0jJpybf5SJHoKnWwn21FRfR6mX34odv3QwLStl/8iGx7PtZcllj3Sj+b0u+12oi0JMgewaiiqmWtz1kTqC5obmIjsi6Puu+eVehvST40vabzggZ25MhXv5o7nk4CtAd36RJeE8yD9KFaU4Lh4shK2e/8AdiQwh/Vs9cv960EE91jcM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b11c9da246eaa2aacfce94adf18e4927_738fbefc656911f19ad75254007bceed
    ReservedCode2: 1zkHLyBUNnUPg0jJpybf5SJHoKnWwn21FRfR6mX34odv3QwLStl/8iGx7PtZcllj3Sj+b0u+12oi0JMgewaiiqmWtz1kTqC5obmIjsi6Puu+eVehvST40vabzggZ25MhXv5o7nk4CtAd36RJeE8yD9KFaU4Lh4shK2e/8AdiQwh/Vs9cv960EE91jcM=
---

# 依赖管理

打包时默认不装任何第三方依赖。首次运行 `main.py` 时自动检测并安装核心依赖，
其余按需分组安装（语音、AI、图像等）。

## 目录结构

```
deps/
├── requirements.txt    # 完整依赖清单（分模块注释）
├── install_deps.py     # 按需安装器
├── README.md           # 本文件
└── *.whl               # 离线安装包（44个）
```

## 使用方式

```bash
# 查看所有依赖状态
python deps/install_deps.py --list

# 安装核心依赖（main.py 启动时自动执行）
python deps/install_deps.py

# 安装指定模块
python deps/install_deps.py --group voice   # 语音识别
python deps/install_deps.py --group ai      # AI/大模型
python deps/install_deps.py --group image   # 图像处理

# 安装全部
python deps/install_deps.py --all
```

## 集成

`main.py` 启动时自动调用 `ensure_core_deps()`，无需手动干预。
业务模块可按需调用：

```python
from deps.install_deps import install_group, _check_installed

# 语音模块启动时
if not _check_installed("faster_whisper"):
    install_group("voice")
```
*（内容由AI生成，仅供参考）*
