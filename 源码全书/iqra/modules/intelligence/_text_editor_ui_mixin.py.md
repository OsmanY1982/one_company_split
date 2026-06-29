# `iqra/modules/intelligence/_text_editor_ui_mixin.py`

> 路径：`iqra/modules/intelligence/_text_editor_ui_mixin.py` | 行数：229


---


```python
# -*- coding: utf-8 -*-
"""TextEditorWidget UI 构建 mixin：工具栏、格式栏、状态栏。"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QFontComboBox, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TextEditorUiMixin:
    """提供 _build_ui / _build_toolbar / _build_format_bar / _update_status。"""

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 顶部工具栏 ──
        self._build_toolbar(main_layout)

        # ── 格式工具栏 ──
        self._build_format_bar(main_layout)

        # ── 主体：左侧树 + 右侧编辑区 ──
        splitter = QSplitter(Qt.Horizontal)

        # 左侧文件树
        left = QWidget()
        left.setFixedWidth(210)
        left.setStyleSheet("background: white;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        tree_header = QWidget()
        tree_header.setStyleSheet("background: #f7fafc; border-bottom: 1px solid #e2e8f0;")
        th_layout = QHBoxLayout(tree_header)
        th_layout.setContentsMargins(8, 6, 6, 6)
        th_lbl = QLabel("📁 我的笔记")
        th_lbl.setStyleSheet("color: #4a5568; font-weight: bold; font-size: 13px;")
        th_layout.addWidget(th_lbl)
        th_layout.addStretch()
        btn_new_folder = QPushButton("＋")
        btn_new_folder.setFixedSize(24, 24)
        btn_new_folder.setToolTip("新建文件夹")
        btn_new_folder.setStyleSheet("background: #e2e8f0; color: #4a5568; border-radius: 4px; font-size: 14px; padding: 0;")
        btn_new_folder.clicked.connect(self._new_folder)
        th_layout.addWidget(btn_new_folder)
        left_layout.addWidget(tree_header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.itemDoubleClicked.connect(self._tree_open)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._tree_context_menu)
        left_layout.addWidget(self._tree)
        splitter.addWidget(left)

        # 右侧标签编辑区
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        splitter.addWidget(self._tabs)
        splitter.setSizes([210, 890])
        main_layout.addWidget(splitter)

        # 状态栏
        status_bar = QWidget()
        status_bar.setStyleSheet("background: #f7fafc; border-top: 1px solid #e2e8f0;")
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(12, 4, 12, 4)
        self._status_lbl = QLabel("字数: 0 | 行数: 0")
        self._status_lbl.setStyleSheet("color: #a0aec0; font-size: 11px;")
        sb_layout.addWidget(self._status_lbl)
        sb_layout.addStretch()
        self._enc_lbl = QLabel("")
        self._enc_lbl.setStyleSheet("color: #38a169; font-size: 11px;")
        sb_layout.addWidget(self._enc_lbl)
        main_layout.addWidget(status_bar)

    def _build_toolbar(self, layout):
        tb = QWidget()
        tb.setStyleSheet("background: #2d3748; padding: 4px 8px;")
        tb_layout = QHBoxLayout(tb)
        tb_layout.setContentsMargins(6, 3, 6, 3)
        tb_layout.setSpacing(4)

        for text, obj, slot in [
            ("📄 新建",   "greenBtn", lambda: self._new_tab()),
            ("📂 打开",   "",         self._open_file),
            ("💾 保存",   "",         self._save_current),
            ("🔐 加密保存","",        self._save_encrypted),
            ("💾 另存为", "grayBtn",  self._save_as),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setFixedHeight(30)
            btn.clicked.connect(slot)
            tb_layout.addWidget(btn)

        tb_layout.addSpacing(8)

        # 字体
        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentFont(QFont("微软雅黑"))
        self._font_combo.setFixedWidth(150)
        self._font_combo.setFixedHeight(30)
        self._font_combo.setStyleSheet("background:white; border-radius:4px; padding:2px 6px; color:#2d3748;")
        self._font_combo.currentFontChanged.connect(self._change_font)
        tb_layout.addWidget(self._font_combo)

        self._size_combo = QComboBox()
        self._size_combo.addItems(["10","11","12","13","14","16","18","20","24","28","32","36","48"])
        self._size_combo.setCurrentText("13")
        self._size_combo.setFixedWidth(58)
        self._size_combo.setFixedHeight(30)
        self._size_combo.setStyleSheet("background:white; border-radius:4px; padding:2px 4px; color:#2d3748;")
        self._size_combo.currentTextChanged.connect(self._change_size)
        tb_layout.addWidget(self._size_combo)

        tb_layout.addStretch()
        self._word_count = QLabel("字数: 0")
        self._word_count.setStyleSheet("color: #a0aec0; font-size: 12px;")
        tb_layout.addWidget(self._word_count)

        layout.addWidget(tb)

    def _build_format_bar(self, layout):
        fb = QWidget()
        fb.setStyleSheet("background: #1a202c; padding: 2px 8px;")
        fb_layout = QHBoxLayout(fb)
        fb_layout.setContentsMargins(6, 2, 6, 2)
        fb_layout.setSpacing(2)

        def _fmt_btn(text, tip, slot, checkable=False):
            btn = QPushButton(text)
            btn.setToolTip(tip)
            btn.setFixedSize(30, 26)
            btn.setCheckable(checkable)
            btn.clicked.connect(slot)
            return btn

        self._btn_bold   = _fmt_btn("B",  "加粗 Ctrl+B",   self._toggle_bold,   True)
        self._btn_italic = _fmt_btn("I",  "斜体 Ctrl+I",   self._toggle_italic, True)
        self._btn_under  = _fmt_btn("U",  "下划线 Ctrl+U", self._toggle_under,  True)
        self._btn_bold.setStyleSheet(self._btn_bold.styleSheet() + "QPushButton { font-weight: bold; }")
        self._btn_italic.setStyleSheet(self._btn_italic.styleSheet() + "QPushButton { font-style: italic; }")

        fb_layout.addWidget(self._btn_bold)
        fb_layout.addWidget(self._btn_italic)
        fb_layout.addWidget(self._btn_under)

        # 分隔
        sep = QLabel("|")
        sep.setStyleSheet("color: #4a5568; margin: 0 4px;")
        fb_layout.addWidget(sep)

        # 对齐
        for icon, tip, align in [
            ("≡", "左对齐",  Qt.AlignLeft),
            ("≡", "居中",    Qt.AlignCenter),
            ("≡", "右对齐",  Qt.AlignRight),
        ]:
            btn = _fmt_btn(icon, tip, lambda _, a=align: self._set_align(a))
            fb_layout.addWidget(btn)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #4a5568; margin: 0 4px;")
        fb_layout.addWidget(sep2)

        # 颜色
        btn_color = QPushButton("A")
        btn_color.setToolTip("文字颜色")
        btn_color.setFixedSize(30, 26)
        btn_color.setStyleSheet("QPushButton { background: transparent; color: #f6ad55; border: none; border-radius: 4px; font-size: 14px; font-weight: bold; } QPushButton:hover { background: #4a5568; }")
        btn_color.clicked.connect(self._pick_color)
        fb_layout.addWidget(btn_color)

        btn_bg = QPushButton("▣")
        btn_bg.setToolTip("背景色高亮")
        btn_bg.setFixedSize(30, 26)
        btn_bg.setStyleSheet("QPushButton { background: transparent; color: #68d391; border: none; border-radius: 4px; font-size: 14px; } QPushButton:hover { background: #4a5568; }")
        btn_bg.clicked.connect(self._pick_bg_color)
        fb_layout.addWidget(btn_bg)

        sep3 = QLabel("|")
        sep3.setStyleSheet("color: #4a5568; margin: 0 4px;")
        fb_layout.addWidget(sep3)

        # 插入图片
        btn_img = QPushButton("🖼 插图")
        btn_img.setToolTip("插入图片")
        btn_img.setFixedHeight(26)
        btn_img.setStyleSheet("QPushButton { background: transparent; color: #90cdf4; border: none; border-radius: 4px; font-size: 12px; padding: 0 8px; } QPushButton:hover { background: #4a5568; }")
        btn_img.clicked.connect(self._insert_image)
        fb_layout.addWidget(btn_img)

        # 清除格式
        btn_clear = QPushButton("✕ 清格式")
        btn_clear.setToolTip("清除所有格式")
        btn_clear.setFixedHeight(26)
        btn_clear.setStyleSheet("QPushButton { background: transparent; color: #fc8181; border: none; border-radius: 4px; font-size: 12px; padding: 0 8px; } QPushButton:hover { background: #4a5568; }")
        btn_clear.clicked.connect(self._clear_format)
        fb_layout.addWidget(btn_clear)

        fb_layout.addStretch()
        layout.addWidget(fb)

    def _update_status(self):
        tab = self._current_tab()
        if not tab:
            return
        text  = tab.editor.toPlainText()
        words = len(text)
        lines = text.count('\n') + 1 if text else 0
        self._status_lbl.setText(f"字数: {words} | 行数: {lines}")
        self._word_count.setText(f"字数: {words}")
        idx   = self._tabs.indexOf(tab)
        title = ("🔐 " if tab.encrypted else "📄 ") + tab.title
        if tab.modified:
            self._tabs.setTabText(idx, "* " + title)
        else:
            self._tabs.setTabText(idx, title)

```
