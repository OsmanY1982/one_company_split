# `iqra/modules/intelligence/_text_editor_files_mixin.py`

> 路径：`iqra/modules/intelligence/_text_editor_files_mixin.py` | 行数：167


---


```python
# -*- coding: utf-8 -*-
"""TextEditorWidget 文件操作 & 标签管理 mixin。"""
import os

from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QDialog,
)
from PyQt5.QtCore import Qt

from ._text_crypto import (
    NoteTab, PasswordDialog, is_encrypted, decrypt_text, encrypt_text,
    NOTES_DIR,
)


class TextEditorFilesMixin:
    """提供文件操作（_open_filepath ~ _auto_save_all）与标签管理（_new_tab ~ _current_tab）。"""

    # ── 标签管理 ──
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

    def _current_tab(self):
        return self._tabs.currentWidget()

    # ── 文件操作 ──
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

    def _save_tab(self, tab) -> bool:
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

    def _save_as_tab(self, tab, encrypted=False) -> bool:
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
            # 已加密文件直接保存
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

```
