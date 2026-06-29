# -*- coding: utf-8 -*-
"""
星球/形态绘制引擎 — shapes 调度器
从 core.shapes 导入 28 种形态，paint_shape 统一调度绘制
"""
import math
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QFont, QRadialGradient
)

# ═══════════════════════════════════════════
# shapes 注册表导入
# ═══════════════════════════════════════════

from core.shapes import SHAPE_MODE_LIST, SHAPE_PAINTERS, SHAPE_MODES

# ═══════════════════════════════════════════
# 统一绘制调度
# ═══════════════════════════════════════════

def paint_shape(
    painter: QPainter,
    mode_key: str,
    rect: QRectF,
    t: float,
    hover_scale: float = 1.0,
    click_pulse: float = 1.0,
    morph_progress: float = 1.0,
    style_params: dict = None,
) -> bool:
    """
    统一形状绘制调度函数。

    参数:
        painter: QPainter 实例（需已开启 Antialiasing）
        mode_key: 形态键名（如 "classic", "alien"）
        rect: 绘制矩形区域（从中提取 center 和 radius）
        t: 动画时间（秒）
        hover_scale: 悬停放大系数（1.0 ~ 1.08）
        click_pulse: 点击脉冲强度（0.0 ~ 1.0）
        morph_progress: 形态过渡进度（0.0 ~ 1.0，用于切换动画）
        style_params: 额外样式参数字典

    返回:
        True 如果绘制成功，False 如果形态不存在
    """
    paint_fn = SHAPE_PAINTERS.get(mode_key)
    if paint_fn is None:
        return False

    center = rect.center()
    radius = min(rect.width(), rect.height()) / 2.0

    # 应用悬停缩放
    if hover_scale != 1.0:
        radius *= hover_scale

    # hovered 判定
    hovered = hover_scale > 1.01

    # alpha 通道（形态过渡）
    alpha = min(1.0, morph_progress)

    # 点击脉冲效果：略微调整半径
    if click_pulse < 1.0:
        pulse_extra = (1.0 - click_pulse) * radius * 0.04
        radius += pulse_extra

    # 调用形状模块的 paint 函数
    # 核心 6 参：painter, center, radius, t, hovered, alpha
    # 额外参数仅 classic 族接受（style / label / font_size），外星人族忽略
    try:
        paint_fn(painter, center, radius, t, hovered, alpha,
                 style=style_params)
    except TypeError:
        # 外星人/简单形状忽略 style 参数
        paint_fn(painter, center, radius, t, hovered, alpha)

    return True


# ═══════════════════════════════════════════
# 轨道线 + 能量连接线（保留）
# ═══════════════════════════════════════════

def paint_orbit(p: QPainter, center: QPointF, radius: float):
    """半透明轨道圆环"""
    pen = QPen(QColor(170, 80, 255, 12))
    pen.setWidth(1)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(center, radius, radius)


def paint_energy_line(p: QPainter, from_pos: QPointF, to_pos: QPointF):
    """能量连接线"""
    p.setPen(QPen(QColor(170, 80, 255, 20)))
    p.drawLine(from_pos, to_pos)
