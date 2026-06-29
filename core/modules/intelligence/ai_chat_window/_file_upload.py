# ── 文件上传 Mixin ──
import os

from PyQt5.QtWidgets import QFileDialog, QPushButton
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from ._model_selector import FILE_PILL_STYLE


class _FileUploadMixin:
    """文件上传 / 附件标签 / 拖拽支持"""

    def _on_upload_clicked(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "所有文件 (*.*);;图片 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;文档 (*.pdf *.txt *.md *.py *.json *.csv *.xlsx *.docx)"
        )
        if paths:
            for p in paths:
                self._add_file_pill(p)

    def _add_file_pill(self, filepath):
        basename = os.path.basename(filepath)
        if any(fp == filepath for fp, _ in self._attached_files):
            return
        self._attached_files.append((filepath, basename))

        pill = QPushButton(f" {basename} ×")
        pill.setToolTip(filepath)
        pill.setStyleSheet(FILE_PILL_STYLE)
        pill.clicked.connect(lambda checked, fp=filepath: self._remove_file_pill(fp))
        self._pills_layout.insertWidget(self._pills_layout.count() - 1, pill)
        self._file_pills.append(pill)
        self._pills_container.setVisible(True)

    def _remove_file_pill(self, filepath):
        for i, (fp, _) in enumerate(self._attached_files):
            if fp == filepath:
                self._attached_files.pop(i)
                pill = self._file_pills.pop(i)
                pill.deleteLater()
                break
        if not self._attached_files:
            self._pills_container.setVisible(False)

    def _clear_file_pills(self):
        for pill in self._file_pills:
            pill.deleteLater()
        self._file_pills.clear()
        self._attached_files.clear()
        self._pills_container.setVisible(False)

    def _drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.ai_chat.setStyleSheet("""
                QTextBrowser {
                    background: rgba(20,10,40,230); color: #bb99dd;
                    border: 2px dashed rgba(255,170,80,180); border-radius: 10px;
                    padding: 12px; font-size: 12px; line-height: 1.6;
                }
            """)

    def _drop_event(self, event: QDropEvent):
        self.ai_chat.setStyleSheet("""
            QTextBrowser {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and os.path.isfile(filepath):
                self._add_file_pill(filepath)
        event.acceptProposedAction()
