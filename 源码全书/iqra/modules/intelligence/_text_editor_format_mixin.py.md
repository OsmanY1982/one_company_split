# `iqra/modules/intelligence/_text_editor_format_mixin.py`

> 路径：`iqra/modules/intelligence/_text_editor_format_mixin.py` | 行数：119


---


```python
# -*- coding: utf-8 -*-
"""TextEditorWidget 富文本格式 mixin。"""
import os, base64

from PyQt5.QtWidgets import QFileDialog, QColorDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QFont, QTextCharFormat, QColor, QTextImageFormat,
)


class TextEditorFormatMixin:
    """提供富文本格式操作：_current_editor ~ _change_size。"""

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
        color = QColorDialog.getColor(e.textColor(), self, "选择文字颜色")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            e.mergeCurrentCharFormat(fmt)

    def _pick_bg_color(self):
        e = self._current_editor()
        if not e:
            return
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
        # 将图片转为 base64 嵌入 HTML（这样加密保存时图片也一起加密）
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
        # 限制最大宽度
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

```
