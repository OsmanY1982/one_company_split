# `iqra/modules/dashboard/dashboard_window/_planets.py`

> 路径：`iqra/modules/dashboard/dashboard_window/_planets.py` | 行数：30


---


```python
"""
模块星球定义 — 常量数据，与 UI 无关
"""
from PyQt5.QtGui import QColor


# ═══════════ 模块星球定义（真实纹理） ═══════════
ALL_PLANETS = [
    {"id": "business",     "name": "业务管理", "style": "earth",   "radius": 56, "orbit": 160},
    {"id": "personnel",    "name": "人员管理", "style": "mars",    "radius": 48, "orbit": 205},
    {"id": "intelligence", "name": "智能中心", "style": "jupiter", "radius": 60, "orbit": 142},
    {"id": "data",         "name": "数据中心", "style": "neptune", "radius": 50, "orbit": 248},
    {"id": "system",       "name": "系统设置", "style": "moon",    "radius": 44, "orbit": 288},
    {"id": "account",      "name": "账号与安全", "style": "saturn",  "radius": 48, "orbit": 330},
    {"id": "admin",        "name": "管理后台", "style": "sun",     "radius": 52, "orbit": 370},
]

# 会员可见模块（业务管理 + 智能中心）
MEMBER_PLANET_IDS = {"business", "intelligence", "account"}

# ── 会员等级徽章配色 ──
MEMBERSHIP_BADGE_COLORS = {
    "trial":     QColor(0, 200, 255),     # 青色
    "vip":       QColor(255, 180, 50),    # 金色
    "permanent": QColor(140, 80, 255),    # 紫色
}

MEMBERSHIP_LABELS = {
    "trial": "体验会员", "vip": "VIP会员", "permanent": "永久会员",
}

```
