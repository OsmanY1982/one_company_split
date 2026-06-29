# `planetarium/core/modules/intelligence/text_editor/_core.py`

> 路径：`planetarium/core/modules/intelligence/text_editor/_core.py` | 行数：683


---


```python
# -*- coding: utf-8 -*-
from core.paths import DATA_DIR

import os, json, base64
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTextEdit, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QMessageBox, QInputDialog, QComboBox,
    QMenu, QFontComboBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (
    QFont, QTextCharFormat, QColor, QTextImageFormat, QPixmap
)

from ._crypto import (
    NOTES_DIR, INDEX_FILE,
    encrypt_text, decrypt_text, is_encrypted,
)
from ._note_tab import NoteTab, PasswordDialog


class TextEditorWidget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 文本编辑器")
        self.setMinimumSize(1100, 720)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save_all)
        self._auto_save_timer.start(60 * 1000)
        self._build_ui()
        self._load_tree()
        if self._tabs.count() == 0:
            self._new_tab()

    # ══════════════════════════════════════════════
    #  UI 构建
    # ══════════════════════════════════════════════
    def _build_ui(self):
        self.setStyleSheet

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_toolbar(main_layout)
        self._build_format_bar(main_layout)

        splitter = QSplitter(Qt.Horizontal)

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

        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        splitter.addWidget(self._tabs)
        splitter.setSizes([210, 890])
        main_layout.addWidget(splitter)

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
            btn.setStyleSheet
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

        sep = QLabel("|")
        sep.setStyleSheet("color: #4a5568; margin: 0 4px;")
        fb_layout.addWidget(sep)

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

        btn_img = QPushButton("🖼 插图")
        btn_img.setToolTip("插入图片")
        btn_img.setFixedHeight(26)
        btn_img.setStyleSheet("QPushButton { background: transparent; color: #90cdf4; border: none; border-radius: 4px; font-size: 12px; padding: 0 8px; } QPushButton:hover { background: #4a5568; }")
        btn_img.clicked.connect(self._insert_image)
        fb_layout.addWidget(btn_img)

        btn_clear = QPushButton("✕ 清格式")
        btn_clear.setToolTip("清除所有格式")
        btn_clear.setFixedHeight(26)
        btn_clear.setStyleSheet("QPushButton { background: transparent; color: #fc8181; border: none; border-radius: 4px; font-size: 12px; padding: 0 8px; } QPushButton:hover { background: #4a5568; }")
        btn_clear.clicked.connect(self._clear_format)
        fb_layout.addWidget(btn_clear)

        fb_layout.addStretch()
        layout.addWidget(fb)

    # ══════════════════════════════════════════════
    #  文件树
    # ══════════════════════════════════════════════
    def _load_tree(self):
        self._tree.clear()
        index = self._load_index_data()
        folders = {}
        for folder in index.get('folders', []):
            item = QTreeWidgetItem(self._tree, [f"📁 {folder}"])
            item.setData(0, Qt.UserRole, {'type': 'folder', 'name': folder})
            item.setExpanded(True)
            folders[folder] = item
        for note in index.get('notes', []):
            folder = note.get('folder', '')
            enc    = note.get('encrypted', False)
            icon   = "🔐" if enc else "📄"
            label  = f"{icon} {note['title']}"
            parent = folders.get(folder, self._tree.invisibleRootItem())
            item   = QTreeWidgetItem(parent, [label])
            item.setData(0, Qt.UserRole, {'type': 'note', **note})

    def _new_folder(self):
        name, ok = QInputDialog.getText(self, "新建文件夹", "文件夹名称：")
        if not ok or not name.strip():
            return
        name = name.strip()
        index = self._load_index_data()
        if name not in index.get('folders', []):
            index.setdefault('folders', []).append(name)
            self._save_index(index)
            self._load_tree()

    def _tree_open(self, item):
        data = item.data(0, Qt.UserRole)
        if not data or data.get('type') != 'note':
            return
        filepath = data.get('filepath')
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "文件不存在", f"文件已被移动或删除：\n{filepath}")
            return
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if tab.filepath == filepath:
                self._tabs.setCurrentIndex(i)
                return
        self._open_filepath(filepath)

    def _tree_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        if data and data.get('type') == 'note':
            menu.addAction("📂 打开", lambda: self._tree_open(item))
            menu.addAction("✏️ 重命名", lambda: self._rename_note(item))
            menu.addSeparator()
            menu.addAction("🗑️ 删除", lambda: self._delete_note(item))
        elif data and data.get('type') == 'folder':
            menu.addAction("📄 在此新建笔记", lambda: self._new_tab_in_folder(data['name']))
            menu.addAction("✏️ 重命名文件夹", lambda: self._rename_folder(item))
            menu.addSeparator()
            menu.addAction("🗑️ 删除文件夹", lambda: self._delete_folder(item))
        menu.exec_(self._tree.viewport().mapToGlobal(pos))

    def _rename_note(self, item):
        data = item.data(0, Qt.UserRole)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称：", text=data.get('title', ''))
        if ok and new_name.strip():
            index = self._load_index_data()
            for note in index.get('notes', []):
                if note.get('filepath') == data.get('filepath'):
                    note['title'] = new_name.strip()
                    break
            self._save_index(index)
            self._load_tree()

    def _delete_note(self, item):
        data = item.data(0, Qt.UserRole)
        if QMessageBox.Yes != QMessageBox.question(
                self, "确认", f"从列表移除「{data.get('title')}」？\n（不会删除实际文件）"):
            return
        index = self._load_index_data()
        index['notes'] = [n for n in index.get('notes', [])
                          if n.get('filepath') != data.get('filepath')]
        self._save_index(index)
        self._load_tree()

    def _rename_folder(self, item):
        data = item.data(0, Qt.UserRole)
        old  = data['name']
        new_name, ok = QInputDialog.getText(self, "重命名文件夹", "新名称：", text=old)
        if ok and new_name.strip():
            index = self._load_index_data()
            if old in index.get('folders', []):
                idx = index['folders'].index(old)
                index['folders'][idx] = new_name.strip()
            for note in index.get('notes', []):
                if note.get('folder') == old:
                    note['folder'] = new_name.strip()
            self._save_index(index)
            self._load_tree()

    def _delete_folder(self, item):
        data = item.data(0, Qt.UserRole)
        name = data['name']
        if QMessageBox.Yes != QMessageBox.question(
                self, "确认", f"删除文件夹「{name}」？\n（文件夹内的笔记会移到根目录）"):
            return
        index = self._load_index_data()
        index['folders'] = [f for f in index.get('folders', []) if f != name]
        for note in index.get('notes', []):
            if note.get('folder') == name:
                note['folder'] = ''
        self._save_index(index)
        self._load_tree()

    def _new_tab_in_folder(self, folder):
        tab = self._new_tab()
        tab._target_folder = folder

    # ══════════════════════════════════════════════
    #  标签管理
    # ══════════════════════════════════════════════
    def _new_tab(self, title="新文档", content="", filepath=None, encrypted=False, password=None):
        if isinstance(title, bool):
            title = "新文档"
        tab = NoteTab(title, content, filepath, encrypted, password)
        tab.editor.textChanged.connect(self._update_status)
        tab.editor.cursorPositionChanged.connect(self._update_format_buttons)
        tab._target_folder = getattr(tab, '_target_folder', '')
        idx = self._tabs.addTab(tab, ("🔐 " if encrypted else "📄 ") + title)
        self._tabs.setCurrentIndex(idx)
        tab.editor.setFocus()
        return tab

    def _close_tab(self, idx):
        tab = self._tabs.widget(idx)
        if tab.modified:
            r = QMessageBox.question(self, "未保存",
                f"「{tab.title}」有未保存的修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if r == QMessageBox.Cancel:
                return
            if r == QMessageBox.Save:
                self._save_tab(tab)
        self._tabs.removeTab(idx)
        if self._tabs.count() == 0:
            self._new_tab()

    def _on_tab_changed(self, idx):
        self._update_status()
        self._update_format_buttons()
        tab = self._tabs.widget(idx)
        if tab:
            self._enc_lbl.setText("🔐 加密文件" if tab.encrypted else "")

    def _current_tab(self) -> NoteTab:
        return self._tabs.currentWidget()

    # ══════════════════════════════════════════════
    #  文件操作
    # ══════════════════════════════════════════════
    def _open_filepath(self, filepath: str):
        try:
            if is_encrypted(filepath):
                dlg = PasswordDialog(self, "输入密码解锁文件")
                if dlg.exec_() != QDialog.Accepted:
                    return
                pwd = dlg.password()
                try:
                    raw     = open(filepath, 'rb').read()
                    content = decrypt_text(raw, pwd)
                except Exception:
                    QMessageBox.warning(self, "密码错误", "密码不正确，无法解密文件")
                    return
                title = os.path.basename(filepath)
                tab   = self._new_tab(title, content, filepath, encrypted=True, password=pwd)
            else:
                content = open(filepath, encoding='utf-8', errors='replace').read()
                title   = os.path.basename(filepath)
                tab     = self._new_tab(title, content, filepath)
            tab.modified = False
            self._tabs.setTabText(self._tabs.currentIndex(),
                                  ("🔐 " if tab.encrypted else "📄 ") + tab.title)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", NOTES_DIR,
            "所有支持格式 (*.txt *.md *.html *.opc);;文本文件 (*.txt);;Markdown (*.md);;加密文件 (*.opc);;所有文件 (*)")
        if path:
            self._open_filepath(path)

    def _save_tab(self, tab: NoteTab) -> bool:
        if not tab.filepath:
            return self._save_as_tab(tab)
        try:
            content = tab.get_content()
            if tab.encrypted and tab.password:
                data = encrypt_text(content, tab.password)
                with open(tab.filepath, 'wb') as f:
                    f.write(data)
            else:
                with open(tab.filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            tab.modified = False
            idx = self._tabs.indexOf(tab)
            self._tabs.setTabText(idx, ("🔐 " if tab.encrypted else "📄 ") + tab.title)
            return True
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
            return False

    def _save_as_tab(self, tab: NoteTab, encrypted=False) -> bool:
        default_name = tab.title + (".opc" if encrypted else ".txt")
        path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", os.path.join(NOTES_DIR, default_name),
            "文本文件 (*.txt);;Markdown (*.md);;加密文件 (*.opc);;所有文件 (*)")
        if not path:
            return False
        if encrypted and not tab.password:
            dlg = PasswordDialog(self, "设置加密密码", confirm=True)
            if dlg.exec_() != QDialog.Accepted:
                return False
            tab.password  = dlg.password()
            tab.encrypted = True
        try:
            content = tab.get_content()
            if tab.encrypted and tab.password:
                data = encrypt_text(content, tab.password)
                with open(path, 'wb') as f:
                    f.write(data)
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            tab.filepath = path
            tab.title    = os.path.splitext(os.path.basename(path))[0]
            tab.modified = False
            idx = self._tabs.indexOf(tab)
            self._tabs.setTabText(idx, ("🔐 " if tab.encrypted else "📄 ") + tab.title)
            self._add_to_index(tab)
            self._load_tree()
            return True
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
            return False

    def _save_current(self):
        tab = self._current_tab()
        if tab:
            self._save_tab(tab)

    def _save_encrypted(self):
        tab = self._current_tab()
        if not tab:
            return
        if tab.encrypted and tab.filepath:
            self._save_tab(tab)
        else:
            self._save_as_tab(tab, encrypted=True)

    def _save_as(self):
        tab = self._current_tab()
        if tab:
            self._save_as_tab(tab)

    def _auto_save_all(self):
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if tab and tab.modified and tab.filepath:
                self._save_tab(tab)

    # ══════════════════════════════════════════════
    #  索引管理
    # ══════════════════════════════════════════════
    def _load_index_data(self) -> dict:
        if os.path.exists(INDEX_FILE):
            try:
                data = json.load(open(INDEX_FILE, encoding='utf-8'))
                if isinstance(data, list):
                    migrated = {
                        'folders': [],
                        'notes': [
                            {
                                'title':     item.get('title', ''),
                                'filepath':  item.get('filepath', ''),
                                'folder':    '',
                                'encrypted': False,
                                'updated':   item.get('updated', ''),
                            }
                            for item in data if isinstance(item, dict)
                        ]
                    }
                    self._save_index(migrated)
                    return migrated
                return data
            except Exception:
                pass
        return {'folders': [], 'notes': []}

    def _save_index(self, index: dict):
        os.makedirs(NOTES_DIR, exist_ok=True)
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _add_to_index(self, tab: NoteTab):
        index  = self._load_index_data()
        folder = getattr(tab, '_target_folder', '')
        entry  = {
            'title':     tab.title,
            'filepath':  tab.filepath,
            'folder':    folder,
            'encrypted': tab.encrypted,
            'updated':   datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        notes = index.get('notes', [])
        for n in notes:
            if n.get('filepath') == tab.filepath:
                n.update(entry)
                self._save_index(index)
                return
        notes.append(entry)
        index['notes'] = notes
        self._save_index(index)

    # ══════════════════════════════════════════════
    #  富文本格式
    # ══════════════════════════════════════════════
    def _current_editor(self):
        tab = self._current_tab()
        return tab.editor if tab else None

    def _toggle_bold(self):
        e = self._current_editor()
        if e:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Normal if e.fontWeight() == QFont.Bold else QFont.Bold)
            e.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self):
        e = self._current_editor()
        if e:
            fmt = QTextCharFormat()
            fmt.setFontItalic(not e.fontItalic())
            e.mergeCurrentCharFormat(fmt)

    def _toggle_under(self):
        e = self._current_editor()
        if e:
            fmt = QTextCharFormat()
            fmt.setFontUnderline(not e.fontUnderline())
            e.mergeCurrentCharFormat(fmt)

    def _set_align(self, align):
        e = self._current_editor()
        if e:
            e.setAlignment(align)

    def _pick_color(self):
        e = self._current_editor()
        if not e:
            return
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(e.textColor(), self, "选择文字颜色")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            e.mergeCurrentCharFormat(fmt)

    def _pick_bg_color(self):
        e = self._current_editor()
        if not e:
            return
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(Qt.yellow, self, "选择高亮颜色")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            e.mergeCurrentCharFormat(fmt)

    def _insert_image(self):
        e = self._current_editor()
        if not e:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp)")
        if not path:
            return
        with open(path, 'rb') as f:
            img_data = f.read()
        ext      = os.path.splitext(path)[1].lower().strip('.')
        mime     = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png',
                    'gif': 'gif', 'bmp': 'bmp', 'webp': 'webp'}.get(ext, 'png')
        b64      = base64.b64encode(img_data).decode()
        data_url = f"data:image/{mime};base64,{b64}"
        cursor   = e.textCursor()
        img_fmt  = QTextImageFormat()
        img_fmt.setName(data_url)
        img_fmt.setWidth(min(600, e.width() - 60))
        cursor.insertImage(img_fmt)

    def _clear_format(self):
        e = self._current_editor()
        if e:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Normal)
            fmt.setFontItalic(False)
            fmt.setFontUnderline(False)
            fmt.setForeground(QColor("#2d3748"))
            fmt.setBackground(QColor(Qt.transparent))
            e.mergeCurrentCharFormat(fmt)

    def _update_format_buttons(self):
        e = self._current_editor()
        if not e:
            return
        self._btn_bold.setChecked(e.fontWeight() == QFont.Bold)
        self._btn_italic.setChecked(e.fontItalic())
        self._btn_under.setChecked(e.fontUnderline())

    def _change_font(self, font):
        e = self._current_editor()
        if e:
            fmt = QTextCharFormat()
            fmt.setFontFamily(font.family())
            e.mergeCurrentCharFormat(fmt)

    def _change_size(self, size_str):
        e = self._current_editor()
        if e and size_str.isdigit():
            fmt = QTextCharFormat()
            fmt.setFontPointSize(int(size_str))
            e.mergeCurrentCharFormat(fmt)

    # ══════════════════════════════════════════════
    #  状态栏
    # ══════════════════════════════════════════════
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
