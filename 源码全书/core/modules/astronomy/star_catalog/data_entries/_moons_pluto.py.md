# `core/modules/astronomy/star_catalog/data_entries/_moons_pluto.py`

> 路径：`core/modules/astronomy/star_catalog/data_entries/_moons_pluto.py` | 行数：42


---


```python
# 4f. 冥王星的卫星 — 直径 > 1000km
# ═══════════════════════════════════════════════════════

MOON_CHARON = {
    "name": "Charon",
    "name_cn": "冥卫一",
    "type": "moon",
    "parent": "Pluto",
    "summary": (
        "冥卫一是冥王星最大的卫星，大小接近冥王星的一半（直径比约1:2），使两者形成独特的'双矮行星'系统。"
        "两者围绕共同的质心旋转——该质心位于冥王星之外。New Horizons飞掠揭示冥卫一表面有巨大的峡谷（Serenity Chasma，"
        "深9公里、长1800公里）和暗红色的极冠。"
    ),
    "physics": (
        "冥卫一直径约1212公里，由冰和岩石组成。表面以水冰为主，极区暗红色冠盖（Mordor Macula）"
        "由从冥王星逃逸的甲烷被辐射转化的索林（tholins）物质形成。Serenity Chasma大峡谷深度达9公里，"
        "是太阳系最壮观的峡谷之一，比地球大峡谷深5倍。"
    ),
    "exploration": (
        "冥卫一于1978年由James Christy发现。New Horizons探测器于2015年飞掠冥王星系统时，"
        "同时获得了冥卫一的全球高分辨率图像，揭示了其多样的地质特征，包括峡谷、极冠和类似月海的光滑平原。"
        "目前尚无专门探测冥卫一的后续计划。"
    ),
    "facts": [
        "冥卫一和冥王星的公共质心在冥王星之外——罕见的真正双星系统",
        "Serenity Chasma大峡谷是太阳系最深峡谷之一，深9公里",
        "冥卫一极区的暗红色物质来自冥王星逃逸的甲烷",
        "冥卫一表面几乎没有撞击坑——暗示近期（地质意义上）曾发生过表面重塑",
    ],
    "diameter_km": 1212,
    "mass_kg": "1.59e21",
    "temp_surface_c": -220,
    "distance_au": 39.48,
    "orbit_period_days": 6.39,
    "rotation_period_hours": 153.3,
    "discovered_year": "1978",
    "discovered_by": "James Christy",
    "style": "pluto",
}


# ═══════════════════════════════════════════════════════

```
