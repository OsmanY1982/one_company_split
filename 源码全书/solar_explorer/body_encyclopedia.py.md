# `solar_explorer/body_encyclopedia.py`

> 路径：`solar_explorer/body_encyclopedia.py` | 行数：340


---


```python
# -*- coding: utf-8 -*-
"""
天体百科数据 — 加载器 (306 天体)
从 body_data_entries 加载 33 颗主要天体的详细数据，
其余 273 颗小卫星通过模板自动生成简介。

优先从 planets/<body>/knowledge/ .md 文件加载深度图文内容。
"""
import math, os
from solar_explorer.body_data_entries import PLANET_ENTRIES, MOON_ENTRIES

# knowledge/ .md 文件根目录
_KNOWLEDGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "modules", "astronomy", "solar_system", "planets")

# body_id → planets 目录名的映射（SOLAR_CATALOG key → 子目录名）
_BODY_ID_TO_DIR = {
    "sun": "sun", "mercury": "mercury", "venus": "venus", "earth": "earth",
    "mars": "mars", "jupiter": "jupiter", "saturn": "saturn",
    "uranus": "uranus", "neptune": "neptune", "pluto": "pluto",
    "ceres": "ceres", "eris": "eris", "makemake": "makemake", "haumea": "haumea",
    "earth_moon_0": "moon",
    "jupiter_moon_0": "io", "jupiter_moon_1": "europa",
    "jupiter_moon_2": "ganymede", "jupiter_moon_3": "callisto",
    "saturn_moon_0": "titan", "saturn_moon_5": "enceladus",
}


def _load_knowledge_md(dir_name, filename):
    path = os.path.join(_KNOWLEDGE_ROOT, dir_name, "knowledge", filename)
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _load_knowledge_facts(dir_name):
    text = _load_knowledge_md(dir_name, "04_facts.md")
    if not text:
        return []
    facts = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line[0].isdigit() and (". " in line[:4] or "、" in line[:4]):
            line = line.split(" ", 1)[-1] if ". " in line[:4] else line.split("、", 1)[-1]
            line = line.strip()
        elif line.startswith("- "):
            line = line[2:].strip()
        if line:
            facts.append(line)
    return facts


def _extract_title(text, filename):
    """从 .md 文件内容第一行 h1 提取显示标题；fallback 用文件名"""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    name = os.path.splitext(filename)[0]
    if len(name) > 3 and name[:3].isdigit() and name[2] == '_':
        name = name[3:]
    return name


def _inject_knowledge(entry, body_id):
    """加载 knowledge/ 目录下所有 .md 文件，存入 knowledge_files 列表（供树状导航用）"""
    dir_name = _BODY_ID_TO_DIR.get(body_id)
    if not dir_name:
        return
    kdir = os.path.join(_KNOWLEDGE_ROOT, dir_name, "knowledge")
    if not os.path.isdir(kdir):
        return

    try:
        files = sorted(f for f in os.listdir(kdir) if f.endswith(".md") and f != "04_facts.md")
    except Exception:
        return

    knowledge_files = []
    parts = []
    for fn in files:
        text = _load_knowledge_md(dir_name, fn)
        if not text:
            continue
        # 合并文本保留给语音朗读使用
        if fn == "00_index.md" and len(text) < 500:
            # 索引太短不合并，但仍在树中显示
            pass
        else:
            parts.append(text)

        title = _extract_title(text, fn)
        knowledge_files.append({
            "filename": fn,
            "title": title,
            "content": text,
        })

    if parts:
        entry["summary"] = "\n\n---\n\n".join(parts)
    if knowledge_files:
        entry["knowledge_files"] = knowledge_files

    facts = _load_knowledge_facts(dir_name)
    if facts:
        entry["facts"] = facts

# ═══════════════════════════════════════════════════════
# 从 solar_system_data 获取天体目录
# ═══════════════════════════════════════════════════════

def _load_catalog():
    """加载 solar_system_data 中的 SOLAR_CATALOG"""
    import sys
    import os
    proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if proj not in sys.path:
        sys.path.insert(0, proj)
    from modules.intelligence.solar_system_data import SOLAR_CATALOG
    return SOLAR_CATALOG


# ═══════════════════════════════════════════════════════
# 小卫星模板生成器
# ═══════════════════════════════════════════════════════

def _gen_moon_summary(body):
    """为小卫星生成简介模板"""
    parent_name = body.get("parent_name", "")
    name = body.get("name", "")
    radius = body.get("radius_km", 0)
    orbit = body.get("orbit_km", 0)

    size_desc = _size_desc(radius)
    orbit_desc = _orbit_desc(orbit)
    return (
        f"{name}是{parent_name}的一颗{size_desc}卫星，直径约{int(radius * 2)}公里。"
        f"它沿{orbit_desc}轨道绕行{parent_name}，是IAU已命名的太阳系天体之一。"
    )


def _gen_moon_physics(body):
    """为小卫星生成物理特征"""
    radius = body.get("radius_km", 0)
    period = body.get("period_d", 0)
    lines = [
        f"直径约{int(radius * 2)}公里，由冰和岩石混合组成。表面布满撞击坑，没有大气层。",
    ]
    if period:
        if period < 1:
            lines.append(f"公转周期仅约{period * 24:.1f}小时，是{body.get('parent_name', '其母行星')}最内侧的卫星之一。")
        elif period < 10:
            lines.append(f"公转周期约{period:.1f}地球日，轨道稳定。")
        else:
            lines.append(f"公转周期约{period:.0f}地球日，属于外层卫星。")
    return " ".join(lines)


def _gen_moon_facts(body):
    """为小卫星生成趣味事实"""
    facts = ["是IAU（国际天文学联合会）正式命名的太阳系天体"]
    radius = body.get("radius_km", 0)
    orbit = body.get("orbit_km", 0)
    if radius < 10:
        facts.append(f"直径仅约{int(radius * 2)}公里，形状极不规则")
    if orbit > 10_000_000:
        facts.append(f"轨道距离母行星超过{orbit / 1_000_000:.0f}百万公里，属于远距离逆行卫星群")
    return facts


def _size_desc(radius_km):
    if radius_km >= 500:
        return "大型"
    elif radius_km >= 50:
        return "中型"
    elif radius_km >= 10:
        return "小型"
    else:
        return "微型不规则"


def _orbit_desc(orbit_km):
    if orbit_km < 100_000:
        return "极近的"
    elif orbit_km < 500_000:
        return "近距"
    elif orbit_km < 5_000_000:
        return "中距"
    else:
        return "远距"


def _parent_cn_name(parent_id):
    """获取母天体中文名"""
    mapping = {
        "sun": "太阳", "mercury": "水星", "venus": "金星", "earth": "地球",
        "mars": "火星", "jupiter": "木星", "saturn": "土星", "uranus": "天王星",
        "neptune": "海王星", "pluto": "冥王星", "eris": "阋神星",
        "ceres": "谷神星", "haumea": "妊神星", "makemake": "鸟神星",
    }
    return mapping.get(parent_id, parent_id)


def _parent_style(parent_id):
    mapping = {
        "sun": "sun", "mercury": "mercury", "venus": "venus", "earth": "earth",
        "mars": "mars", "jupiter": "jupiter", "saturn": "saturn", "uranus": "uranus",
        "neptune": "neptune", "pluto": "pluto", "eris": "pluto",
        "ceres": "mercury", "haumea": "mars", "makemake": "pluto",
    }
    return mapping.get(parent_id, "neptune")


# ═══════════════════════════════════════════════════════
# BODIES 构建
# ═══════════════════════════════════════════════════════
_BODIES = None


def _build_bodies():
    """懒加载：构建 306 天体的百科字典"""
    global _BODIES
    if _BODIES is not None:
        return _BODIES

    catalog = _load_catalog()
    bodies = {}

    for body_id, body in catalog.items():
        if body_id in PLANET_ENTRIES:
            # 行星/矮行星/太阳 — 使用详细数据
            entry = dict(PLANET_ENTRIES[body_id])
            # 补充物理数据字段
            entry.setdefault("diameter_km", body.get("radius_km", 0) * 2)
            entry.setdefault("mass_kg", "—")
            entry.setdefault("temp_surface_c", "—")
            entry.setdefault("distance_au", 0)
            entry.setdefault("orbit_period_days", body.get("period_d", 0))
            entry.setdefault("rotation_period_hours", 0)
            entry.setdefault("discovered_year", "—")
            entry.setdefault("discovered_by", "—")
            entry.setdefault("style", body.get("style", "neptune"))
            entry["catalog_id"] = body_id
            _inject_knowledge(entry, body_id)
            bodies[body_id] = entry

        elif body_id in MOON_ENTRIES:
            # 大卫星 — 使用详细数据
            entry = dict(MOON_ENTRIES[body_id])
            entry.setdefault("diameter_km", body.get("radius_km", 0) * 2)
            entry.setdefault("mass_kg", "—")
            entry.setdefault("temp_surface_c", "—")
            entry.setdefault("distance_au", 0)
            entry.setdefault("orbit_period_days", body.get("period_d", 0))
            entry.setdefault("rotation_period_hours", 0)
            entry.setdefault("discovered_year", "—")
            entry.setdefault("discovered_by", "—")
            entry.setdefault("style", body.get("style", _parent_style(body.get("parent", ""))))
            entry["catalog_id"] = body_id
            _inject_knowledge(entry, body_id)
            bodies[body_id] = entry

        else:
            # 小卫星 — 模板生成
            parent_id = body.get("parent", "")
            parent_name = _parent_cn_name(parent_id)
            body_with_parent = dict(body)
            body_with_parent["parent_name"] = parent_name

            entry = {
                "name": body.get("name_en", body.get("name", "")),
                "name_cn": body.get("name", ""),
                "type": "moon",
                "parent": parent_name,
                "summary": _gen_moon_summary(body_with_parent),
                "physics": _gen_moon_physics(body_with_parent),
                "exploration": (
                    f"{body.get('name', '这颗卫星')}目前仅通过望远镜观测，"
                    f"尚未有探测器近距离飞掠。其基本信息来源于地面天文观测和空间望远镜数据。"
                ),
                "facts": _gen_moon_facts(body_with_parent),
                "diameter_km": body.get("radius_km", 0) * 2,
                "mass_kg": "—",
                "temp_surface_c": "—",
                "distance_au": 0,
                "orbit_period_days": body.get("period_d", 0),
                "rotation_period_hours": 0,
                "discovered_year": "—",
                "discovered_by": "—",
                "style": _parent_style(parent_id),
                "catalog_id": body_id,
            }
            _inject_knowledge(entry, body_id)
            bodies[body_id] = entry

    _BODIES = bodies
    return bodies


def get_entry(body_id):
    """获取单个天体百科条目"""
    bodies = _build_bodies()
    return bodies.get(body_id)


def get_all_entries():
    """获取所有天体百科条目"""
    return list(_build_bodies().values())


def get_entries_by_type(body_type):
    """按类型筛选天体条目"""
    return [e for e in _build_bodies().values() if e.get("type") == body_type]


def get_entries_by_parent(parent_name):
    """按母天体筛选（卫星用）"""
    return [e for e in _build_bodies().values() if e.get("parent") == parent_name]


def get_statistics():
    """获取统计信息"""
    bodies = _build_bodies()
    stars = sum(1 for e in bodies.values() if e["type"] == "star")
    planets = sum(1 for e in bodies.values() if e["type"] == "planet")
    dwarfs = sum(1 for e in bodies.values() if e["type"] == "dwarf_planet")
    moons = sum(1 for e in bodies.values() if e["type"] == "moon")
    return {
        "total": len(bodies),
        "stars": stars,
        "planets": planets,
        "dwarfs": dwarfs,
        "moons": moons,
    }

```
