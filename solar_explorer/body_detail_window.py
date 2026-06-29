# -*- coding: utf-8 -*-
"""
天体详情窗口 · BODY DETAIL（全屏版）
paint_planet() 渲染 + 科普卡片 + 语音朗读。ESC 关闭。
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QTextBrowser, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QFont, QColor

from core.cosmic import CosmicBackground
from core.planet_painter import PLANET_STYLES, paint_planet
from solar_explorer.voice_reader import VoiceReader


# ═══════════════════════════════════════════════════════
# 样式常量（全屏加大版）
# ═══════════════════════════════════════════════════════
SECTION_TITLE_STYLE = (
    "color: #00ccff; font-size: 20px; font-weight: 700;"
    " background: transparent; font-family: 'PingFang SC';"
    " border-bottom: 2px solid rgba(0,200,255,0.2); padding-bottom: 6px; margin-top: 20px;"
)
BODY_TEXT_STYLE = (
    "color: #8899bb; font-size: 16px; background: transparent;"
    " font-family: 'PingFang SC'; line-height: 1.9;"
    " padding: 8px 0;"
)
FACT_STYLE = (
    "color: #7799bb; font-size: 15px; background: transparent;"
    " font-family: 'PingFang SC'; line-height: 1.8;"
)
CARD_STYLE = (
    "background: rgba(8, 14, 32, 0.75);"
    " border: 1px solid rgba(60, 120, 200, 0.2);"
    " border-radius: 10px; padding: 16px 20px;"
)

FILE_LIST_STYLE = (
    "QListWidget {"
    " background: rgba(8, 14, 32, 0.75);"
    " border: 1px solid rgba(60, 120, 200, 0.2);"
    " border-radius: 8px; padding: 4px;"
    " font-family: 'PingFang SC'; font-size: 15px; color: #8899bb;"
    " outline: none;"
    "}"
    "QListWidget::item {"
    " padding: 10px 14px;"
    " border-bottom: 1px solid rgba(60, 120, 200, 0.1);"
    "}"
    "QListWidget::item:selected {"
    " background: rgba(30, 60, 120, 0.6); color: #aaccee;"
    " border-left: 3px solid #3399ff;"
    "}"
    "QListWidget::item:hover {"
    " background: rgba(20, 40, 80, 0.5);"
    "}"
)


# ═══════════════════════════════════════════════════════
# 天体渲染画布（加大版 220px）
# ═══════════════════════════════════════════════════════

class BodyRenderer(QWidget):
    """使用 paint_planet 引擎渲染天体球体"""

    def __init__(self, style_name, size=220, parent=None):
        super().__init__(parent)
        self.setFixedSize(size + 50, size + 50)
        self._style_name = style_name
        self._size = size
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

    def _tick(self):
        self._angle = (self._angle + 0.3) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        style = PLANET_STYLES.get(self._style_name, PLANET_STYLES["neptune"])
        cx, cy = self.width() / 2, self.height() / 2
        from PyQt5.QtCore import QPointF
        paint_planet(p, QPointF(cx, cy), self._size, style,
                     hovered=False, label="", font_size=9,
                     anim_t=self._angle)
        p.end()


# ═══════════════════════════════════════════════════════
# BodyDetailWindow
# ═══════════════════════════════════════════════════════

class BodyDetailWindow(QWidget):
    """天体详情窗口 — 渲染 + 科普 + 语音"""

    def __init__(self, body_data, parent_window=None):
        super().__init__(parent_window)
        self.setWindowFlags(Qt.Window)
        self._body = body_data
        self._parent_win = parent_window
        self._voice = VoiceReader()

        self.setWindowTitle(f"{body_data.get('name_cn', '')} · 天体详情")
        self.setMinimumSize(800, 600)

        self._build_ui()
        self.showMaximized()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._voice.stop()
            if self._parent_win:
                self._parent_win.show()
                self._parent_win._load_data()
            self.close()
        else:
            super().keyPressEvent(event)

    def _build_ui(self):
        """构建界面"""
        self._bg = CosmicBackground(self)
        self._bg.setGeometry(0, 0, self.width(), self.height())

        # 外层 ScrollArea
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            " QScrollBar:vertical { background: rgba(0,0,0,0.3); width: 8px; margin: 2px; }"
            " QScrollBar::handle:vertical {"
            "  background: rgba(100,150,220,0.35); border-radius: 4px; min-height: 40px;"
            " }"
        )

        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(14)

        # ── 上半部分：渲染 + 信息卡片 ──
        top_row = QHBoxLayout()
        top_row.setSpacing(28)

        # 左侧：星球渲染（加大 220px）
        style_name = self._body.get("style", "neptune")
        self._renderer = BodyRenderer(style_name, 220, container)
        render_wrapper = QFrame(container)
        render_wrapper.setMinimumSize(320, 340)
        render_wrapper.setStyleSheet(CARD_STYLE)
        rl = QVBoxLayout(render_wrapper)
        rl.addWidget(self._renderer, 0, Qt.AlignCenter)
        top_row.addWidget(render_wrapper)

        # 右侧：信息卡片
        info_card = QFrame(container)
        info_card.setStyleSheet(CARD_STYLE)
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)

        ecn = self._body.get("name_cn", "未知")
        etype = self._body.get("type", "")
        parent = self._body.get("parent", "")

        name_label = QLabel(f"{ecn}")
        name_label.setStyleSheet(
            "color: #ffffff; font-size: 32px; font-weight: 800;"
            " background: transparent; font-family: 'PingFang SC';"
        )
        info_layout.addWidget(name_label)

        type_label = QLabel(
            f"{_type_name(etype)}"
            + (f" · 绕 {parent}" if etype == "moon" and parent else "")
        )
        type_label.setStyleSheet(
            "color: #7799cc; font-size: 14px; background: transparent;"
            " font-family: 'PingFang SC';"
        )
        info_layout.addWidget(type_label)

        # 物理参数网格
        params = [
            ("直径", f"{self._format_number(self._body.get('diameter_km', 0))} km"),
            ("质量", f"{self._body.get('mass_kg', '—')} kg"),
            ("表面温度", f"{self._body.get('temp_surface_c', '—')}°C"),
            ("与太阳距离", f"{self._body.get('distance_au', '—')} AU"),
            ("公转周期", f"{self._format_orbital(self._body.get('orbit_period_days', 0))}"),
            ("自转周期", f"{self._format_orbital_hours(self._body.get('rotation_period_hours', 0))}"),
            ("发现", f"{self._body.get('discovered_year', '—')}"),
            ("发现者", f"{self._body.get('discovered_by', '—')}"),
        ]
        grid = QVBoxLayout()
        grid.setSpacing(6)
        for label, value in params:
            row = QHBoxLayout()
            row.setSpacing(12)
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                "color: #6688aa; font-size: 14px; background: transparent;"
                " font-family: 'PingFang SC';"
            )
            lbl.setFixedWidth(80)
            row.addWidget(lbl)
            val = QLabel(value)
            val.setStyleSheet(
                "color: #aaccee; font-size: 16px; font-weight: 600;"
                " background: transparent; font-family: 'PingFang SC';"
            )
            row.addWidget(val, 1)
            grid.addLayout(row)
        info_layout.addLayout(grid)
        info_layout.addStretch()

        top_row.addWidget(info_card, 1)
        layout.addLayout(top_row)

        # ── 下半部分：详细介绍（树状导航，点击展开各自 .md 内容）──
        knowledge_files = self._body.get("knowledge_files", [])
        if knowledge_files:
            sec_title = QLabel("详细介绍")
            sec_title.setStyleSheet(SECTION_TITLE_STYLE)
            layout.addWidget(sec_title)

            split_row = QHBoxLayout()
            split_row.setSpacing(12)

            # 左侧：文件列表
            self._file_list = QListWidget()
            self._file_list.setFixedWidth(230)
            self._file_list.setStyleSheet(FILE_LIST_STYLE)
            for kf in knowledge_files:
                item = QListWidgetItem(kf["title"])
                item.setData(Qt.UserRole, kf["content"])
                self._file_list.addItem(item)
            self._file_list.currentRowChanged.connect(self._on_select_knowledge)
            split_row.addWidget(self._file_list)

            # 右侧：内容查看器
            self._content_view = QTextBrowser()
            self._content_view.setOpenExternalLinks(True)
            self._content_view.setStyleSheet(
                "QTextBrowser {"
                " color: #8899bb; font-size: 16px; background: rgba(8,14,32,0.6);"
                " border: 1px solid rgba(60,120,200,0.15); border-radius: 8px;"
                " padding: 12px 16px; font-family: 'PingFang SC';"
                "}"
                "QTextBrowser:focus { border-color: rgba(0,200,255,0.3); }"
            )
            self._content_view.document().setDefaultStyleSheet(
                "body { color: #8899bb; background: rgba(8,14,32,0.6); }"
                " a { color: #66ccff; }"
                " p { color: #8899bb; line-height: 1.8; }"
            )
            self._content_view.setMinimumHeight(120)
            self._content_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            split_row.addWidget(self._content_view, 1)
            layout.addLayout(split_row)

            # 默认选中第一个文件
            if self._file_list.count() > 0:
                self._file_list.setCurrentRow(0)

        else:
            # 无知识文件时回退：显示 summary + physics + exploration 合并文本
            merged_content = self._body.get("summary", "")
            phys = self._body.get("physics", "")
            expl = self._body.get("exploration", "")
            if phys and phys not in merged_content:
                merged_content = merged_content + "\n\n---\n\n" + phys if merged_content else phys
            if expl and expl not in merged_content:
                merged_content = merged_content + "\n\n---\n\n" + expl if merged_content else expl

            if merged_content:
                sec_title = QLabel("详细介绍")
                sec_title.setStyleSheet(SECTION_TITLE_STYLE)
                layout.addWidget(sec_title)
                sec_body = QTextBrowser()
                sec_body.setOpenExternalLinks(True)
                sec_body.setStyleSheet(
                    "QTextBrowser {"
                    " color: #8899bb; font-size: 16px; background: rgba(8,14,32,0.6);"
                    " border: 1px solid rgba(60,120,200,0.15); border-radius: 8px;"
                    " padding: 12px 16px; font-family: 'PingFang SC';"
                    "}"
                    "QTextBrowser:focus { border-color: rgba(0,200,255,0.3); }"
                )
                sec_body.document().setDefaultStyleSheet(
                    "body { color: #8899bb; background: rgba(8,14,32,0.6); }"
                    " a { color: #66ccff; }"
                    " p { color: #8899bb; line-height: 1.8; }"
                )
                sec_body.setHtml(_md_to_html(merged_content))
                sec_body.setMinimumHeight(120)
                sec_body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                layout.addWidget(sec_body)

        # 趣味事实
        facts = self._body.get("facts", [])
        if facts:
            ftitle = QLabel("趣味事实")
            ftitle.setStyleSheet(SECTION_TITLE_STYLE)
            layout.addWidget(ftitle)
            for i, fact in enumerate(facts):
                fl = QLabel(f"{i + 1}. {fact}")
                fl.setStyleSheet(FACT_STYLE)
                fl.setWordWrap(True)
                layout.addWidget(fl)

        layout.addStretch()

        scroll.setWidget(container)

        # ── 底部操作栏 ──
        self._bottom_bar = QWidget(self)
        self._bottom_bar.setStyleSheet(
            "background: rgba(8, 12, 28, 0.9);"
            " border-top: 1px solid rgba(60, 120, 200, 0.2);"
        )
        self._bottom_bar.setFixedHeight(64)
        bl = QHBoxLayout(self._bottom_bar)
        bl.setContentsMargins(28, 10, 28, 10)
        bl.setSpacing(16)

        self._voice_btn = QPushButton("🔊 语音朗读")
        self._voice_btn.setStyleSheet(_btn_style())
        self._voice_btn.clicked.connect(self._on_voice)
        bl.addWidget(self._voice_btn)

        bl.addStretch()

        back_btn = QPushButton("← 返回星谱")
        back_btn.setStyleSheet(_btn_style())
        back_btn.clicked.connect(self._on_back)
        bl.addWidget(back_btn)

        esc_hint = QLabel("ESC 关闭")
        esc_hint.setStyleSheet(
            "color: #554477; background: transparent; font-size: 12px;"
            " font-family: 'PingFang SC';"
        )
        bl.addWidget(esc_hint)

        self._scroll = scroll

        # 初始 geometry：避免 showMaximized() 异步 resize 前首帧内容不可见
        w0, h0 = self.width(), self.height()
        if w0 > 0 and h0 > 0:
            self._scroll.setGeometry(0, 0, w0, h0 - 64)
            self._bottom_bar.setGeometry(0, h0 - 64, w0, 64)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_bg'):
            self._bg.setGeometry(0, 0, w, h)
        if hasattr(self, '_scroll'):
            self._scroll.setGeometry(0, 0, w, h - 64)
        if hasattr(self, '_bottom_bar'):
            self._bottom_bar.setGeometry(0, h - 64, w, 64)

    def _on_voice(self):
        """语音朗读"""
        if self._voice.is_speaking:
            self._voice.stop()
            self._voice_btn.setText("🔊 语音朗读")
            return

        parts = [self._body.get("name_cn", ""),
                 self._body.get("summary", ""),
                 self._body.get("physics", ""),
                 self._body.get("exploration", "")]
        text = "。".join(p for p in parts if p)
        if not text:
            return

        self._voice_btn.setText("⏹ 停止朗读")
        self._voice.speak(text)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_voice)
        self._poll_timer.start(500)

    def _poll_voice(self):
        if self._voice.state == "done":
            self._voice_btn.setText("🔊 语音朗读")
            if hasattr(self, '_poll_timer'):
                self._poll_timer.stop()

    def _on_back(self):
        self._voice.stop()
        if self._parent_win:
            self._parent_win.show()
            self._parent_win._load_data()
        self.close()

    def _on_select_knowledge(self, index):
        """点击左侧文件列表项时，渲染对应 .md 内容到右侧 QTextBrowser"""
        if index < 0:
            return
        item = self._file_list.item(index)
        content = item.data(Qt.UserRole) or ""
        self._content_view.setHtml(_md_to_html(content))

    def closeEvent(self, event):
        self._voice.stop()
        super().closeEvent(event)

    @staticmethod
    def _format_number(n):
        if not n or n == 0:
            return "—"
        if n >= 1000000:
            return f"{n / 1000000:.1f} 万"
        if n >= 1000:
            return f"{n:,}"
        return str(int(n))

    @staticmethod
    def _format_orbital(days):
        if not days or days == 0:
            return "—"
        if days > 365:
            return f"{days / 365.25:.1f} 年"
        if days < 1:
            return f"{days * 24:.1f} 小时"
        return f"{days:.1f} 天"

    @staticmethod
    def _format_orbital_hours(hours):
        if not hours or hours == 0:
            return "—"
        if hours > 24:
            return f"{hours / 24:.1f} 天"
        return f"{hours:.1f} 小时"


def _type_name(t):
    return {"star": "恒星", "planet": "行星", "dwarf_planet": "矮行星", "moon": "卫星"}.get(t, t)


def _btn_style():
    return (
        "QPushButton {"
        " background: rgba(30, 50, 90, 0.7); color: #aaccee;"
        " border: 1px solid rgba(80, 140, 200, 0.3); border-radius: 8px;"
        " padding: 10px 24px; font-size: 15px; font-family: 'PingFang SC';"
        "}"
        "QPushButton:hover {"
        " background: rgba(50, 80, 140, 0.8); color: #00ccff;"
        " border-color: rgba(0, 200, 255, 0.5);"
        "}"
    )


# ═══════════════════════════════════════════════════════
# Markdown → HTML 简易转换
# ═══════════════════════════════════════════════════════

import re as _re


def _md_to_html(text: str) -> str:
    """将知识库 Markdown 转为 HTML 片段（用于 QTextBrowser）"""
    if not text:
        return "<p></p>"
    lines = text.split("\n")
    out = []
    in_code = False
    buf = []

    def _flush_para():
        nonlocal buf
        if buf:
            p = " ".join(buf).strip()
            buf.clear()
            p = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", p)
            p = _re.sub(r"\*(.+?)\*", r"<i>\1</i>", p)
            p = _re.sub(r"`([^`]+)`", r"<code>\1</code>", p)
            p = _re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                         r'<a href="\2" style="color:#66ccff;">\1</a>', p)
            out.append(f"<p>{p}</p>")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            _flush_para()
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                out.append('<pre style="color:#7799aa; background:rgba(0,0,0,0.3); '
                            'padding:10px; border-radius:6px;">')
                in_code = True
            continue

        if in_code:
            out.append(line)
            continue

        if not stripped:
            _flush_para()
            continue

        if stripped.startswith("# "):
            _flush_para()
            h = stripped[2:]
            out.append(f'<h2 style="color:#ccddff; font-size:18px; margin:12px 0 4px;">{h}</h2>')
        elif stripped.startswith("## "):
            _flush_para()
            h = stripped[3:]
            out.append(f'<h3 style="color:#aaccff; font-size:16px; margin:10px 0 2px;">{h}</h3>')
        elif stripped.startswith("### "):
            _flush_para()
            h = stripped[4:]
            out.append(f'<h4 style="color:#99bbee; font-size:15px; margin:8px 0 2px;">{h}</h4>')
        elif stripped == "---" or stripped == "***":
            _flush_para()
            out.append('<hr style="border:none; border-top:1px solid rgba(60,120,200,0.2); margin:8px 0;">')
        elif _re.match(r"^[-*]\s+", stripped):
            _flush_para()
            item = _re.sub(r"^[-*]\s+", "", stripped)
            item = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", item)
            item = _re.sub(r"\*(.+?)\*", r"<i>\1</i>", item)
            out.append(f'<li style="color:#8899bb; margin-left:16px;">{item}</li>')
        elif _re.match(r"^\d+[\.、]\s+", stripped):
            _flush_para()
            item = _re.sub(r"^\d+[\.、]\s+", "", stripped)
            item = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", item)
            item = _re.sub(r"\*(.+?)\*", r"<i>\1</i>", item)
            out.append(f'<li style="color:#8899bb; margin-left:16px;">{item}</li>')
        else:
            buf.append(stripped)

    _flush_para()
    if in_code:
        out.append("</pre>")

    return "".join(out)
