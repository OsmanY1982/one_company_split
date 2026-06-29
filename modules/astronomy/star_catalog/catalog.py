# -*- coding: utf-8 -*-
"""
星谱目录窗口 · STAR CATALOG（全屏版）
搜索/筛选 306 颗太阳系天体，点击打开详情。ESC 关闭。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter

from core.cosmic import CosmicBackground
from core.planet_painter import PLANET_STYLES, paint_planet
from modules.astronomy.star_catalog.encyclopedia import get_all_entries, get_statistics


# ═══════════════════════════════════════════════════════
# 样式常量（全屏加大版）
# ═══════════════════════════════════════════════════════
TAB_STYLE = """
    QPushButton {{
        color: #8899bb; background: transparent; border: none;
        font-size: 16px; padding: 10px 24px;
        font-family: 'PingFang SC';
    }}
    QPushButton:hover {{ color: #aaccee; }}
    QPushButton:checked {{ color: #00ccff; border-bottom: 3px solid #00ccff; }}
"""

LIST_ITEM_STYLE = """
    QListWidget {{
        background: rgba(8, 12, 28, 0.85);
        border: 1px solid rgba(80, 120, 200, 0.15);
        border-radius: 8px; color: #99aacc;
        font-size: 16px; font-family: 'PingFang SC';
        padding: 6px;
    }}
    QListWidget::item {{
        background: rgba(10, 18, 40, 0.6); border-radius: 6px;
        padding: 14px 20px; margin: 3px 6px;
        border: 1px solid transparent;
    }}
    QListWidget::item:hover {{
        background: rgba(30, 50, 90, 0.7);
        border: 1px solid rgba(80, 140, 220, 0.3);
    }}
    QListWidget::item:selected {{
        background: rgba(40, 70, 130, 0.8);
        border: 1px solid rgba(0, 200, 255, 0.5);
    }}
"""

SEARCH_STYLE = """
    QLineEdit {{
        background: rgba(10, 18, 40, 0.8); border: 1px solid rgba(80, 140, 200, 0.25);
        border-radius: 10px; padding: 14px 20px; color: #aaccee;
        font-size: 18px; font-family: 'PingFang SC';
    }}
    QLineEdit:focus {{ border-color: rgba(0, 200, 255, 0.5); }}
"""

# ═══════════════════════════════════════════════════════
# StarCatalogWindow
# ═══════════════════════════════════════════════════════

class StarCatalogWindow(QWidget):
    """太阳系星谱目录 — 搜索/筛选/跳转"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("太阳系星谱 · STAR CATALOG")
        self.setMinimumSize(800, 600)

        self._all_entries = []
        self._filtered = []
        self._active_tab = "all"
        self._search_text = ""

        self._build_ui()
        self._load_data()
        self.showMaximized()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def _build_ui(self):
        """构建界面"""
        self._bg = CosmicBackground(self)
        self._bg.setGeometry(0, 0, self.width(), self.height())

        # 主布局
        self._content = QWidget(self)
        self._content.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(48, 32, 48, 24)
        layout.setSpacing(16)

        # 标题行
        title = QLabel("太阳系星谱")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 32px; font-weight: 800;"
            " letter-spacing: 10px; background: transparent;"
            " font-family: 'PingFang SC';"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 搜索框
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索天体名称... (支持中文/英文)")
        self._search.setStyleSheet(SEARCH_STYLE)
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # 分类 Tab
        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)

        tabs = [
            ("all", "全部"),
            ("star", "恒星"),
            ("planet", "行星"),
            ("dwarf_planet", "矮行星"),
            ("moon", "卫星"),
        ]
        self._tab_btns = {}
        for tab_id, tab_label in tabs:
            btn = QPushButton(f"{tab_label}")
            btn.setCheckable(True)
            btn.setStyleSheet(TAB_STYLE)
            btn.clicked.connect(lambda checked, tid=tab_id: self._on_tab(tid))
            tab_row.addWidget(btn)
            self._tab_btns[tab_id] = btn
        tab_row.addStretch()
        layout.addLayout(tab_row)

        # 列表
        self._list = QListWidget()
        self._list.setStyleSheet(LIST_ITEM_STYLE)
        self._list.setSpacing(3)
        self._list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list, 1)

        # 底部状态栏
        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        self._count_label = QLabel("")
        self._count_label.setStyleSheet(
            "color: #7766aa; background: transparent; font-size: 14px;"
            " font-family: 'PingFang SC';"
        )
        bottom.addWidget(self._count_label)
        bottom.addStretch()

        hint = QLabel("点击天体查看详情 · ESC 关闭")
        hint.setStyleSheet(
            "color: #554477; background: transparent; font-size: 12px;"
            " font-family: 'PingFang SC';"
        )
        bottom.addWidget(hint)
        layout.addLayout(bottom)

        self._content.setGeometry(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_bg'):
            self._bg.setGeometry(0, 0, w, h)
        if hasattr(self, '_content'):
            self._content.setGeometry(0, 0, w, h)

    def _load_data(self):
        """加载天体数据"""
        self._all_entries = get_all_entries()
        self._all_entries.sort(key=lambda e: (
            {"star": 0, "planet": 1, "dwarf_planet": 2, "moon": 3}.get(e.get("type"), 9),
            e.get("name_cn", ""),
        ))
        self._apply_filters()

    def _apply_filters(self):
        """应用筛选 + 搜索"""
        self._filtered = []
        stats = get_statistics()

        for entry in self._all_entries:
            etype = entry.get("type", "")
            ecn = entry.get("name_cn", "")
            een = entry.get("name", "")

            if self._active_tab != "all" and etype != self._active_tab:
                continue

            if self._search_text:
                txt = self._search_text.lower()
                if txt not in ecn.lower() and txt not in een.lower():
                    continue

            self._filtered.append(entry)

        self._refresh_list(stats)

    def _refresh_list(self, stats):
        """刷新列表"""
        self._list.clear()
        for entry in self._filtered:
            item = self._build_item(entry)
            self._list.addItem(item)

        tab_counts = {
            "all": stats["total"],
            "star": stats["stars"],
            "planet": stats["planets"],
            "dwarf_planet": stats["dwarfs"],
            "moon": stats["moons"],
        }
        for tab_id, btn in self._tab_btns.items():
            if tab_id == "all":
                btn.setText(f"全部({tab_counts['all']})")
            else:
                btn.setText(f"{_tab_label(tab_id)}({tab_counts.get(tab_id, 0)})")

        self._count_label.setText(
            f"太阳系星谱 · 已收录 {stats['total']} 个已命名天体"
            + (f" | 显示 {len(self._filtered)}" if self._search_text or self._active_tab != "all" else "")
        )
        for tid, btn in self._tab_btns.items():
            btn.setChecked(tid == self._active_tab)

    def _build_item(self, entry):
        """构建列表项（含 40x40 星球缩略图）"""
        etype = entry.get("type", "")
        ecn = entry.get("name_cn", "")
        parent = entry.get("parent", "")
        type_label = _type_label(etype)

        text = f"{ecn}"
        if etype == "moon" and parent:
            text += f"       ↳ {_type_label('moon')} | 绕 {parent}"
        else:
            text += f"       [{type_label}]"

        # ── 渲染 60x60 星球缩略图（大气光晕/光环不裁剪）──
        pix = QPixmap(60, 60)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        style_name = entry.get("style", "neptune")
        style = PLANET_STYLES.get(style_name, PLANET_STYLES["neptune"])
        paint_planet(p, QPointF(30, 30), 16, style,
                     hovered=False, label="", font_size=9,
                     anim_t=0.0)
        p.end()

        item = QListWidgetItem(QIcon(pix), text)
        item.setData(Qt.UserRole, entry)
        item.setSizeHint(QSize(0, 64))
        item.setFont(QFont("PingFang SC", 16))
        return item

    def _on_tab(self, tab_id):
        self._active_tab = tab_id
        self._apply_filters()

    def _on_search(self, text):
        self._search_text = text.strip()
        self._apply_filters()

    def _on_item_clicked(self, item):
        entry = item.data(Qt.UserRole)
        if entry:
            from modules.astronomy.star_catalog.detail import BodyDetailWindow
            self._detail_win = BodyDetailWindow(entry, parent_window=self)
            self._detail_win.show()
            self.hide()


def _type_label(t):
    from modules.astronomy.star_catalog import BODY_TYPE_LABELS
    return BODY_TYPE_LABELS.get(t, t)


def _tab_label(t):
    from modules.astronomy.star_catalog import BODY_TYPE_LABELS
    return BODY_TYPE_LABELS.get(t, t)
