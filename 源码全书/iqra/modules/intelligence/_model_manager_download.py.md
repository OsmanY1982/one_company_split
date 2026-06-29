# `iqra/modules/intelligence/_model_manager_download.py`

> 路径：`iqra/modules/intelligence/_model_manager_download.py` | 行数：576


---


```python
# -*- coding: utf-8 -*-
"""
模型下载对话框 — DownloadModelDialog + DownloadWorker
从 _model_manager.py 拆分，独立为 _model_manager_download.py
"""

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox,
    QGroupBox, QProgressBar, QPlainTextEdit,
    QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from modules.intelligence._model_manager_ollama import OllamaManager
from modules.intelligence._ai_shared import ButtonAnimationHelper, RECOMMENDED_MODELS


class DownloadModelDialog(QDialog):
    """下载模型对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⬇️ 下载本地模型")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        self._installed_models = self._get_installed()
        self._model_buttons = {}
        self._delete_buttons = {}
        self._is_downloading = False
        self._build_ui()

    @staticmethod
    def _get_installed():
        """获取已安装模型名称列表"""
        try:
            models = OllamaManager.list_models()
            return set(m.get("name", "") for m in models)
        except Exception:
            return set()

    def showEvent(self, event):
        super().showEvent(event)
        self._installed_models = self._get_installed()
        self._refresh_buttons()

    def closeEvent(self, event):
        if self._is_downloading:
            reply = QMessageBox.question(
                self, "下载进行中",
                "模型正在下载中，关闭对话框下载会中断。\n确定要取消吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if hasattr(self, 'worker') and self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait(1000)
                self._is_downloading = False
                self.progress.setVisible(False)
                parent = self.parent()
                if parent and hasattr(parent, '_check_ollama_status'):
                    parent._check_ollama_status()
                event.accept()
            else:
                event.ignore()
        else:
            parent = self.parent()
            if parent and hasattr(parent, '_check_ollama_status'):
                parent._check_ollama_status()
            event.accept()

    def _refresh_buttons(self):
        for model_id, btn in self._model_buttons.items():
            if model_id in self._installed_models:
                self._mark_installed(btn, model_id)
            else:
                self._mark_download(btn, model_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("⬇️ 下载本地模型")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("选择模型下载到本地，下载后即可离线使用。建议先下载小模型测试。")
        desc.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(12)

        self._installed_section = self._create_installed_section()
        layout.addWidget(self._installed_section)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        small_group = self._create_model_group(
            "🚀 超小模型（推荐测试用）",
            "400MB-2.3GB，下载快，适合测试功能",
            RECOMMENDED_MODELS[:4]
        )
        scroll_layout.addWidget(small_group)

        medium_group = self._create_model_group(
            "⚡ 中等模型（日常使用）",
            "1-2GB，性能与速度平衡",
            RECOMMENDED_MODELS[4:7]
        )
        scroll_layout.addWidget(medium_group)

        large_group = self._create_model_group(
            "🧠 大模型（高性能）",
            "4-9GB，需要较好硬件",
            RECOMMENDED_MODELS[7:11]
        )
        scroll_layout.addWidget(large_group)

        super_large_group = self._create_model_group(
            "🦾 超大型模型（企业级性能）",
            "9-60GB+，需高配硬件与大显存",
            RECOMMENDED_MODELS[11:]
        )
        scroll_layout.addWidget(super_large_group)

        custom_group = QGroupBox("🔧 自定义模型")
        custom_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                color: #2c3e50;
                border: 2px solid #e0e4ea;
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px;
            }
        """)
        custom_layout = QHBoxLayout(custom_group)
        custom_layout.setSpacing(12)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("输入模型名称，如: llama3:8b")
        self.custom_input.setMinimumHeight(36)
        self.custom_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e4ea;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
        """)
        custom_layout.addWidget(self.custom_input)

        custom_btn = QPushButton("⬇️ 下载")
        custom_btn.setMinimumHeight(36)
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #553c9a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #44337a; }
            QPushButton:pressed { padding-top: 7px; padding-bottom: 5px; }
        """)
        custom_btn.clicked.connect(self._download_custom)
        ButtonAnimationHelper.apply_scale_animation(custom_btn, 1.03)
        custom_layout.addWidget(custom_btn)

        scroll_layout.addWidget(custom_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMinimumHeight(24)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e4ea;
                border-radius: 4px;
                text-align: center;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #2b6cb0;
            }
        """)
        layout.addWidget(self.progress)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setPlaceholderText("下载日志将显示在这里...")
        self.log_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 12px;
                padding: 8px;
                color: #2d3748;
            }
        """)
        layout.addWidget(self.log_output)

        close_btn = QPushButton("✅ 完成")
        close_btn.setMinimumHeight(40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2f855a; }
            QPushButton:pressed { background-color: #276749; padding-top: 9px; padding-bottom: 7px; }
        """)
        close_btn.clicked.connect(self.accept)
        ButtonAnimationHelper.apply_scale_animation(close_btn, 1.03)
        layout.addWidget(close_btn)

    def _create_model_group(self, title: str, subtitle: str, models: list) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2b6cb0;
            }
        """)

        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        sub = QLabel(subtitle)
        sub.setStyleSheet("color: #718096; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(sub)

        for model_id, model_name, size in models:
            row = QHBoxLayout()
            row.setSpacing(16)

            info_frame = QFrame()
            info_frame.setStyleSheet("""
                QFrame {
                    background-color: #f7fafc;
                    border-radius: 8px;
                    padding: 4px;
                }
            """)
            info_layout = QHBoxLayout(info_frame)
            info_layout.setContentsMargins(12, 8, 12, 8)

            name_label = QLabel(f"<b>{model_name}</b>")
            name_label.setStyleSheet("font-size: 13px; color: #1a202c;")
            info_layout.addWidget(name_label)

            info_layout.addStretch()

            size_label = QLabel(f"📦 {size}")
            size_label.setStyleSheet("font-size: 12px; color: #718096;")
            info_layout.addWidget(size_label)

            row.addWidget(info_frame, stretch=1)

            btn = QPushButton("⬇️ 下载")
            btn.setProperty("model_id", model_id)
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(80)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b6cb0;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #2c5282; }
                QPushButton:pressed { padding-top: 7px; padding-bottom: 5px; }
                QPushButton:disabled { background-color: #cbd5e0; }
            """)
            self._model_buttons[model_id] = btn
            btn.clicked.connect(lambda checked, m=model_id, b=btn: self._download_model(m, b))
            ButtonAnimationHelper.apply_scale_animation(btn, 1.05)
            row.addWidget(btn)

            del_btn = QPushButton("🗑️ 删除")
            del_btn.setProperty("model_id", model_id)
            del_btn.setMinimumHeight(36)
            del_btn.setMinimumWidth(80)
            del_btn.setVisible(False)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #c53030; }
                QPushButton:pressed { padding-top: 7px; padding-bottom: 5px; }
            """)
            self._delete_buttons[model_id] = del_btn
            del_btn.clicked.connect(lambda checked, m=model_id: self._delete_model(m))
            ButtonAnimationHelper.apply_scale_animation(del_btn, 1.05)
            row.addWidget(del_btn)

            layout.addLayout(row)

        return group

    def _create_installed_section(self):
        group = QGroupBox("📦 已安装的模型")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2b6cb0;
            }
        """)
        group._model_layout = QVBoxLayout(group)
        group._model_layout.setSpacing(8)
        group._model_layout.setContentsMargins(8, 8, 8, 8)
        self._refresh_installed_section(group)
        return group

    def _refresh_installed_section(self, group=None):
        if group is None:
            group = self._installed_section
        layout = group._model_layout

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        models = OllamaManager.list_models()
        if not models:
            empty = QLabel("暂无已安装的模型\n可从下方推荐列表下载")
            empty.setStyleSheet("color: #7f8c8d; font-size: 13px; padding: 12px;")
            layout.addWidget(empty)
            return

        for m in models:
            name = m.get("name", "")
            size = m.get("size", 0)
            size_str = f"{size / 1024 / 1024 / 1024:.1f} GB" if size else ""

            row = QHBoxLayout()
            row.setSpacing(12)

            name_lbl = QLabel(f"<b>{name}</b>")
            name_lbl.setStyleSheet("font-size: 13px; color: #2c3e50;")
            row.addWidget(name_lbl)

            if size_str:
                size_lbl = QLabel(f"📦 {size_str}")
                size_lbl.setStyleSheet("font-size: 12px; color: #7f8c8d;")
                row.addWidget(size_lbl)

            row.addStretch()

            del_btn = QPushButton("🗑️ 删除")
            del_btn.setMinimumHeight(32)
            del_btn.setMinimumWidth(70)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #c53030; }
            """)
            del_btn.clicked.connect(lambda checked, n=name: self._delete_model(n))
            row.addWidget(del_btn)

            layout.addLayout(row)

    def _mark_installed(self, btn, model_id=None):
        btn.setText("✅ 已下载")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:disabled { background-color: #c6f6d5; color: #276749; }
        """)
        btn.setEnabled(False)
        if model_id is None:
            model_id = btn.property("model_id")
        if model_id and model_id in self._delete_buttons:
            self._delete_buttons[model_id].setVisible(True)
            self._delete_buttons[model_id].setText("🗑️ 删除")
            self._delete_buttons[model_id].setEnabled(True)

    def _mark_download(self, btn, model_id=None):
        btn.setText("⬇️ 下载")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:disabled { background-color: #cbd5e0; }
        """)
        btn.setEnabled(True)
        if model_id is None:
            model_id = btn.property("model_id")
        if model_id and model_id in self._delete_buttons:
            self._delete_buttons[model_id].setVisible(False)

    def _download_model(self, model_id: str, btn: QPushButton):
        if self._is_downloading:
            QMessageBox.warning(self, "提示", "已有模型正在下载中")
            return

        self._is_downloading = True
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        btn.setEnabled(False)
        btn.setText("下载中...")

        self.log_output.appendPlainText(f"开始下载模型: {model_id}")

        self.worker = DownloadWorker(model_id)
        self.worker.progress.connect(self._on_download_progress)
        self.worker.finished.connect(lambda success, msg: self._on_download_finished(success, msg, model_id, btn))
        self.worker.start()

    def _on_download_progress(self, data: dict):
        status = data.get("status", "")
        completed = data.get("completed", 0)
        total = data.get("total", 0)

        if status == "pulling":
            self.log_output.appendPlainText(f"下载中... {completed}/{total}")
        elif status == "downloading":
            if total > 0:
                percent = int(completed / total * 100)
                self.progress.setRange(0, 100)
                self.progress.setValue(percent)

        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_download_finished(self, success: bool, msg: str, model_id: str, btn: QPushButton):
        self._is_downloading = False
        self.progress.setVisible(False)

        if success:
            self.log_output.appendPlainText(f"✅ {msg}")
            self._mark_installed(btn, model_id)
            self._installed_models.add(model_id)
            self._refresh_installed_section()
            QMessageBox.information(self, "完成", f"模型 {model_id} 下载成功！")
        else:
            self.log_output.appendPlainText(f"❌ {msg}")
            self._mark_download(btn, model_id)
            QMessageBox.warning(self, "失败", f"模型 {model_id} 下载失败:\n{msg}")

        parent = self.parent()
        if parent and hasattr(parent, '_check_ollama_status'):
            parent._check_ollama_status()

    def _download_custom(self):
        model_id = self.custom_input.text().strip()
        if not model_id:
            QMessageBox.warning(self, "提示", "请输入模型名称")
            return

        temp_btn = QPushButton()
        temp_btn.setProperty("model_id", model_id)
        self._download_model(model_id, temp_btn)

    def _delete_model(self, model_id: str):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模型 {model_id} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if OllamaManager.delete_model(model_id):
                QMessageBox.information(self, "成功", f"模型 {model_id} 已删除")
                self._installed_models.discard(model_id)
                if model_id in self._model_buttons:
                    self._mark_download(self._model_buttons[model_id], model_id)
                self._refresh_installed_section()
                parent = self.parent()
                if parent and hasattr(parent, '_check_ollama_status'):
                    parent._check_ollama_status()
            else:
                QMessageBox.warning(self, "失败", f"删除模型 {model_id} 失败")


class DownloadWorker(QThread):
    """后台下载线程"""
    progress = pyqtSignal(dict)
    finished = pyqtSignal(bool, str)

    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name

    def run(self):
        try:
            def on_progress(data):
                self.progress.emit(data)

            success = OllamaManager.pull_model(self.model_name, on_progress)
            if success:
                self.finished.emit(True, f"模型 {self.model_name} 下载完成")
            else:
                self.finished.emit(False, "下载失败")
        except Exception as e:
            self.finished.emit(False, str(e))

```
