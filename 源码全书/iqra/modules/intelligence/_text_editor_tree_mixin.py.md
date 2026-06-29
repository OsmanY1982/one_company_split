# `iqra/modules/intelligence/_text_editor_tree_mixin.py`

> 路径：`iqra/modules/intelligence/_text_editor_tree_mixin.py` | 行数：190


---


```python
# -*- coding: utf-8 -*-
"""TextEditorWidget 文件树 & 索引管理 mixin。"""
import os, json
from datetime import datetime

from PyQt5.QtWidgets import (
    QTreeWidgetItem, QInputDialog, QMessageBox, QMenu,
)
from PyQt5.QtCore import Qt

from ._text_crypto import INDEX_FILE, NOTES_DIR


class TextEditorTreeMixin:
    """提供文件树操作（_load_tree ~ _delete_folder）与索引管理（_load_index_data / _save_index / _add_to_index）。"""

    # ── 文件树 ──
    def _load_tree(self):
        self._tree.clear()
        index = self._load_index_data()
        folders = {}
        # 先建文件夹节点
        for folder in index.get('folders', []):
            item = QTreeWidgetItem(self._tree, [f"📁 {folder}"])
            item.setData(0, Qt.UserRole, {'type': 'folder', 'name': folder})
            item.setExpanded(True)
            folders[folder] = item
        # 再建文件节点
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
        # 检查是否已打开
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if tab.filepath == filepath:
                self._tabs.setCurrentIndex(i)
                return
        # 打开文件
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

    # ── 索引管理 ──
    def _load_index_data(self) -> dict:
        if os.path.exists(INDEX_FILE):
            try:
                data = json.load(open(INDEX_FILE, encoding='utf-8'))
                # 兼容旧格式（列表）→ 自动迁移为新格式（字典）
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

    def _add_to_index(self, tab):
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

```
