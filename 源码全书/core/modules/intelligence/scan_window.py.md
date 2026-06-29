# `core/modules/intelligence/scan_window.py`

> 路径：`core/modules/intelligence/scan_window.py` | 行数：221


---


```python
"""
扫码工具 · NEURAL — 独立子窗口
二维码生成（输入文本 → 显示QR码 + 保存） + 解析（手动输入 / 图片解析 + 历史记录）
"""
import os
from io import BytesIO
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QTextEdit, QLineEdit,
    QWidget, QFrame, QMessageBox, QFileDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from core.theme import CYBER_PURPLE
# 懒安装
from deps.install_deps import ensure
ensure("qrcode")
import qrcode


class QRLabel(QLabel):
    """支持动态缩放的 QLabel，用于二维码显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._qimage: QImage | None = None
        self._pixmap: QPixmap | None = None

    def set_qimage(self, image: QImage) -> None:
        self._qimage = image
        self._update_pixmap()

    def set_qpixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._qimage = None
        self._update_pixmap()

    def _update_pixmap(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        if self._qimage:
            scaled = self._qimage.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(QPixmap.fromImage(scaled))
        elif self._pixmap:
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_pixmap()


class ScanWindow(QDialog):
    """扫码工具 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫码工具 · NEURAL")
        self.setMinimumSize(650, 620)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._qr_pixmap = None
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        info = QLabel("二维码工具 — 生成 / 解析")
        info.setStyleSheet("color: #776699; font-size: 12px; background: transparent;")
        l.addWidget(info)

        # ── 生成区 ──
        gen_frame = QFrame()
        gen_frame.setStyleSheet("background: rgba(12,6,22,200); border: 1px solid rgba(170,80,255,25); border-radius: 10px; padding: 12px;")
        gen_l = QVBoxLayout(gen_frame)
        gen_l.setSpacing(8)
        gen_title = QLabel("生成二维码")
        gen_title.setStyleSheet("color: #aa88dd; font-size: 13px; font-weight: 700; background:transparent;")
        gen_l.addWidget(gen_title)

        gen_row = QHBoxLayout()
        self._qr_input = QLineEdit()
        self._qr_input.setPlaceholderText("输入文本 / 链接，回车生成...")
        self._qr_input.setStyleSheet(CYBER_PURPLE.INPUT_STYLE)
        self._qr_input.returnPressed.connect(self._qr_generate)
        gen_row.addWidget(self._qr_input, 1)
        btn_gen = QPushButton("生成")
        btn_gen.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        btn_gen.clicked.connect(self._qr_generate)
        gen_row.addWidget(btn_gen)
        btn_save = QPushButton("保存图片")
        btn_save.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        btn_save.clicked.connect(self._qr_save)
        gen_row.addWidget(btn_save)
        gen_l.addLayout(gen_row)

        self._qr_display = QRLabel()
        self._qr_display.setMinimumSize(220, 220)
        self._qr_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._qr_display.setStyleSheet("border: 1px dashed rgba(170,80,255,40); border-radius: 8px; background: white;")
        gen_l.addWidget(self._qr_display, alignment=Qt.AlignCenter)
        l.addWidget(gen_frame)

        # ── 解析区 ──
        parse_frame = QFrame()
        parse_frame.setStyleSheet("background: rgba(12,6,22,200); border: 1px solid rgba(170,80,255,25); border-radius: 10px; padding: 12px;")
        parse_l = QVBoxLayout(parse_frame)
        parse_l.setSpacing(8)
        parse_title = QLabel("解析二维码")
        parse_title.setStyleSheet("color: #aa88dd; font-size: 13px; font-weight: 700; background:transparent;")
        parse_l.addWidget(parse_title)

        pr = QHBoxLayout()
        self._qr_decode_input = QLineEdit()
        self._qr_decode_input.setPlaceholderText("扫码枪输入或粘贴条码 → 回车解析")
        self._qr_decode_input.setStyleSheet(CYBER_PURPLE.INPUT_STYLE)
        self._qr_decode_input.returnPressed.connect(self._qr_decode_text)
        pr.addWidget(self._qr_decode_input, 1)
        btn_file = QPushButton("打开图片")
        btn_file.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        btn_file.clicked.connect(self._qr_decode_image)
        pr.addWidget(btn_file)
        parse_l.addLayout(pr)

        self._qr_result = QTextEdit()
        self._qr_result.setReadOnly(True)
        self._qr_result.setMaximumHeight(80)
        self._qr_result.setStyleSheet(CYBER_PURPLE.INPUT_STYLE)
        parse_l.addWidget(self._qr_result)

        hist_label = QLabel("解析历史")
        hist_label.setStyleSheet("color: #776699; font-size: 11px; background:transparent;")
        parse_l.addWidget(hist_label)
        self._qr_history = QTableWidget()
        self._qr_history.setColumnCount(3)
        self._qr_history.setHorizontalHeaderLabels(["时间", "内容", "来源"])
        self._qr_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._qr_history.setStyleSheet(CYBER_PURPLE.TABLE_STYLE)
        self._qr_history.setMaximumHeight(160)
        self._qr_history.setEditTriggers(QTableWidget.NoEditTriggers)
        parse_l.addWidget(self._qr_history)

        clr_row = QHBoxLayout()
        clear = QPushButton("清空历史")
        clear.setStyleSheet(CYBER_PURPLE.BTN_DANGER)
        clear.clicked.connect(lambda: self._qr_history.setRowCount(0))
        clr_row.addStretch()
        clr_row.addWidget(clear)
        parse_l.addLayout(clr_row)

        l.addWidget(parse_frame)

    def _qr_generate(self):
        text = self._qr_input.text().strip()
        if not text:
            return
        try:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#aa55ff", back_color="white")
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            self._qr_pixmap = pixmap
            self._qr_display.set_qpixmap(pixmap)
        except Exception as e:
            QMessageBox.warning(self, "生成失败", str(e))

    def _qr_save(self):
        if self._qr_pixmap is None:
            QMessageBox.information(self, "提示", "请先生成二维码")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存二维码", "qrcode.png", "PNG 图片 (*.png)")
        if path:
            self._qr_pixmap.save(path, 'PNG')

    def _qr_decode_text(self):
        text = self._qr_decode_input.text().strip()
        if not text:
            return
        self._qr_result.setText(f"[手动输入] {text}")
        self._qr_add_history(text, "手动输入")
        self._qr_decode_input.clear()

    def _qr_decode_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择二维码图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)")
        if not path:
            return
        try:
            from PIL import Image
            from pyzbar.pyzbar import decode as zb_decode
            img = Image.open(path)
            results = zb_decode(img)
            if results:
                data = results[0].data.decode('utf-8', errors='replace')
                self._qr_result.setText(f"[图片解析] {data}")
                self._qr_add_history(data, os.path.basename(path))
            else:
                self._qr_result.setText("[图片解析] 未检测到二维码")
        except ImportError:
            self._qr_result.setText("[图片解析] 需要安装 pyzbar 和 Pillow 库：pip install pyzbar Pillow")
        except Exception as e:
            self._qr_result.setText(f"[图片解析] 错误: {e}")

    def _qr_add_history(self, content, source):
        row = self._qr_history.rowCount()
        self._qr_history.insertRow(0)
        self._qr_history.setItem(0, 0, QTableWidgetItem(datetime.now().strftime('%H:%M:%S')))
        self._qr_history.setItem(0, 1, QTableWidgetItem(content[:80]))
        self._qr_history.setItem(0, 2, QTableWidgetItem(source))
```
