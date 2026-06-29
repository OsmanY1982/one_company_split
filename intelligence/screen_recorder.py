# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import tempfile
import webbrowser
from PIL import Image
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class ScreenRecorder(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GIF 录屏工具")
        self.setFixedSize(450, 350)
        self.setStyleSheet("""
            QDialog { background-color: #f0f2f5; }
            QPushButton {
                background-color: #3182ce; color: white; border: none;
                border-radius: 8px; padding: 10px 20px; font-size: 12px;
            }
            QPushButton:hover { background-color: #2b6cb0; }
            QPushButton#startBtn { background-color: #28a745; }
            QPushButton#stopBtn { background-color: #e53e3e; }
            QPushButton#openBtn { background-color: #48bb78; }
            QLabel { font-size: 12px; }
        """)

        self.is_recording = False
        self.frames = []
        self.record_time = 0
        self.fps = 8
        self.save_path = os.path.join(os.path.dirname(__file__), "录屏")
        os.makedirs(self.save_path, exist_ok=True)
        self._tmpdir = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        title = QLabel("GIF 录屏（macOS 原生截图）")
        title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.status_label = QLabel("准备就绪 | 点击开始录制，再次点击停止")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.time_label = QLabel("录制时长：00:00")
        self.time_label.setFont(QFont("PingFang SC", 14, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        btn_layout1 = QHBoxLayout()
        btn_layout1.setSpacing(15)
        self.start_btn = QPushButton("开始录制")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_recording)
        btn_layout1.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止录制")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        btn_layout1.addWidget(self.stop_btn)
        layout.addLayout(btn_layout1)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("保存路径："))
        self.path_label = QLabel(self.save_path)
        self.path_label.setStyleSheet("color: #666; font-size: 11px;")
        path_layout.addWidget(self.path_label)

        self.path_btn = QPushButton("选择路径")
        self.path_btn.clicked.connect(self.select_save_path)
        path_layout.addWidget(self.path_btn)
        layout.addLayout(path_layout)

        btn_layout2 = QHBoxLayout()
        btn_layout2.setSpacing(15)
        self.open_btn = QPushButton("打开保存文件夹")
        self.open_btn.setObjectName("openBtn")
        self.open_btn.clicked.connect(self.open_save_folder)
        btn_layout2.addWidget(self.open_btn)

        self.clear_btn = QPushButton("清空录制缓存")
        self.clear_btn.clicked.connect(self.clear_cache)
        btn_layout2.addWidget(self.clear_btn)
        layout.addLayout(btn_layout2)

        tip_label = QLabel("提示：GIF 适合短时间演示（建议 30 秒以内）")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: #4299e1; font-size: 11px;")
        layout.addWidget(tip_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.capture_frame)
        self.capture_timer.setInterval(int(1000 / self.fps))

    def update_time(self):
        self.record_time += 1
        minutes = self.record_time // 60
        seconds = self.record_time % 60
        self.time_label.setText(f"录制时长：{minutes:02d}:{seconds:02d}")

    def capture_frame(self):
        if not self.is_recording:
            return
        try:
            fname = os.path.join(self._tmpdir, f"frame_{len(self.frames):06d}.png")
            subprocess.run(
                ["screencapture", "-x", "-C", "-t", "png", fname],
                check=True, timeout=3, capture_output=True
            )
            img = Image.open(fname)
            self.frames.append(img)
        except Exception:
            pass

    def select_save_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存文件夹", self.save_path)
        if dir_path:
            self.save_path = dir_path
            self.path_label.setText(dir_path)
            os.makedirs(dir_path, exist_ok=True)

    def open_save_folder(self):
        if os.path.exists(self.save_path):
            webbrowser.open(self.save_path)
        else:
            os.makedirs(self.save_path)
            webbrowser.open(self.save_path)

    def clear_cache(self):
        self.frames = []
        self.record_time = 0
        self.time_label.setText("录制时长：00:00")
        self.status_label.setText("缓存已清空 | 点击开始录制")
        QMessageBox.information(self, "提示", "录制缓存已清空！")

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.record_time = 0
        self._tmpdir = tempfile.mkdtemp(prefix="gif_rec_")

        self.showMinimized()
        QApplication.processEvents()

        self.timer.start(1000)
        self.capture_timer.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("正在录制...（点击停止按钮结束）")
        self.status_label.setStyleSheet("color: #e53e3e; font-weight: bold;")

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.timer.stop()
        self.capture_timer.stop()

        self.showNormal()
        self.activateWindow()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("正在保存 GIF...")
        self.status_label.setStyleSheet("color: #ed8936; font-weight: bold;")

        if self.frames:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                gif_path = os.path.join(self.save_path, f"录屏_{timestamp}.gif")

                self.frames[0].save(
                    gif_path,
                    save_all=True,
                    append_images=self.frames[1:],
                    duration=int(1000 / self.fps),
                    loop=0,
                    optimize=True
                )

                self.status_label.setText("录制完成！GIF 已保存")
                self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
                reply = QMessageBox.information(
                    self, "录制成功",
                    f"GIF 文件已保存：\n{gif_path}\n\n是否打开保存文件夹？",
                    QMessageBox.Ok | QMessageBox.Cancel
                )
                if reply == QMessageBox.Ok:
                    self.open_save_folder()

            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"GIF 保存出错：{str(e)}")
                self.status_label.setText("保存失败！")
                self.status_label.setStyleSheet("color: #e53e3e; font-weight: bold;")
        else:
            QMessageBox.warning(self, "录制失败", "未捕获到任何画面，请重试！")
            self.status_label.setText("准备就绪 | 点击开始录制")

        self.time_label.setText("录制时长：00:00")
        self.record_time = 0
        self.frames = []

        # 清理临时文件
        if self._tmpdir and os.path.exists(self._tmpdir):
            import shutil
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None


# 测试入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("PingFang SC")
    app.setFont(font)
    window = ScreenRecorder()
    window.show()
    sys.exit(app.exec_())
