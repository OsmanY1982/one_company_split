# `core/shapes/__init__.py`

> 路径：`core/shapes/__init__.py` | 行数：144


---


```python
# -*- coding: utf-8 -*-
"""
shapes 模块 — 悬浮球变形形态绘制器
全部宇宙主题：星球和外星人
"""
from . import classic
from . import gas_giant
from . import ice_giant
from . import lava_planet
from . import pulsar
from . import black_hole
from . import alien
from . import comet
from . import mars
from . import venus
from . import saturn
from . import uranus
from . import neutron_star
from . import nebula
from . import grey_alien
from . import reptilian
from . import energy_being
from . import mercury
from . import pluto
from . import white_dwarf
from . import red_giant
from . import wormhole
from . import crystal_alien
from . import octopus_alien
from . import ghost_alien
from . import jellyfish_alien
from . import robot_alien
from . import starship
from . import fighter
from . import corvette
from . import destroyer
from . import interceptor
from . import dreadnought
from . import scout
from . import transporter

SHAPE_MODES = {
    "classic":      {"name": "🌍 经典星球"},
    "gas_giant":    {"name": "🪐 气态巨行星"},
    "ice_giant":    {"name": "🔵 冰巨星"},
    "lava_planet":  {"name": "🌋 熔岩行星"},
    "pulsar":       {"name": "💫 脉冲星"},
    "black_hole":   {"name": "🕳️ 黑洞"},
    "alien":        {"name": "👽 小绿外星人"},
    "comet":        {"name": "☄️ 彗星"},
    "mars":         {"name": "🔴 火星"},
    "venus":        {"name": "🟡 金星"},
    "saturn":       {"name": "🪐 土星"},
    "uranus":       {"name": "🔷 天王星"},
    "neutron_star": {"name": "⭐ 中子星"},
    "nebula":       {"name": "🌌 星云"},
    "grey_alien":   {"name": "👾 灰人"},
    "reptilian":    {"name": "🦎 蜥蜴人"},
    "energy_being": {"name": "✨ 能量体"},
    "mercury":      {"name": "☿️ 水星"},
    "pluto":        {"name": "♇ 冥王星"},
    "white_dwarf":  {"name": "⚪ 白矮星"},
    "red_giant":    {"name": "🔴 红巨星"},
    "wormhole":     {"name": "🌀 虫洞"},
    "crystal_alien":{"name": "💎 水晶生命体"},
    "octopus_alien":{"name": "🐙 章鱼星人"},
    "ghost_alien":      {"name": "👻 幽灵外星人"},
    "jellyfish_alien":  {"name": "🪼 水母外星人"},
    "robot_alien":      {"name": "🤖 机器外星人"},
    "starship":          {"name": "🚀 太空星舰"},
    "fighter":           {"name": "⚔️ 星际战机"},
    "corvette":          {"name": "🛡️ 轻型护卫舰"},
    "destroyer":         {"name": "💥 重型驱逐舰"},
    "interceptor":       {"name": "⚡ 截击机"},
    "dreadnought":       {"name": "🏰 无畏舰"},
    "scout":             {"name": "🔭 侦察舰"},
    "transporter":       {"name": "📦 运输舰"},
}

SHAPE_MODE_LIST = [
    "classic", "gas_giant", "ice_giant", "lava_planet",
    "pulsar", "black_hole", "alien", "comet",
    "mars", "venus", "saturn", "uranus", "neutron_star", "nebula",
    "grey_alien", "reptilian", "energy_being",
    "mercury", "pluto", "white_dwarf", "red_giant", "wormhole",
    "crystal_alien", "octopus_alien", "ghost_alien", "jellyfish_alien",
    "robot_alien", "starship",
    "fighter", "corvette", "destroyer", "interceptor",
    "dreadnought", "scout", "transporter",
]

SHAPE_PLANETS = [
    "classic", "gas_giant", "ice_giant", "lava_planet",
    "pulsar", "black_hole", "comet",
    "mars", "venus", "saturn", "uranus", "neutron_star", "nebula",
    "mercury", "pluto", "white_dwarf", "red_giant", "wormhole",
]

SHAPE_ALIENS = [
    "alien", "grey_alien", "reptilian", "energy_being",
    "crystal_alien", "octopus_alien", "ghost_alien", "jellyfish_alien",
    "robot_alien",
]

SHAPE_STARSHIPS = ["starship", "fighter", "corvette", "destroyer",
                   "interceptor", "dreadnought", "scout", "transporter"]

SHAPE_PAINTERS = {
    "classic":      classic.paint,
    "gas_giant":    gas_giant.paint,
    "ice_giant":    ice_giant.paint,
    "lava_planet":  lava_planet.paint,
    "pulsar":       pulsar.paint,
    "black_hole":   black_hole.paint,
    "alien":        alien.paint,
    "comet":        comet.paint,
    "mars":         mars.paint,
    "venus":        venus.paint,
    "saturn":       saturn.paint,
    "uranus":       uranus.paint,
    "neutron_star": neutron_star.paint,
    "nebula":       nebula.paint,
    "grey_alien":   grey_alien.paint,
    "reptilian":    reptilian.paint,
    "energy_being": energy_being.paint,
    "mercury":      mercury.paint,
    "pluto":        pluto.paint,
    "white_dwarf":  white_dwarf.paint,
    "red_giant":    red_giant.paint,
    "wormhole":     wormhole.paint,
    "crystal_alien":crystal_alien.paint,
    "octopus_alien":octopus_alien.paint,
    "ghost_alien":  ghost_alien.paint,
    "jellyfish_alien": jellyfish_alien.paint,
    "robot_alien":   robot_alien.paint,
    "starship":       starship.paint,
    "fighter":        fighter.paint,
    "corvette":       corvette.paint,
    "destroyer":      destroyer.paint,
    "interceptor":    interceptor.paint,
    "dreadnought":    dreadnought.paint,
    "scout":          scout.paint,
    "transporter":    transporter.paint,
}

```
