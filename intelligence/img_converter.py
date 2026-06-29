# -*- coding: utf-8 -*-
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor
from PIL import Image

# --------------------------
# 转换线程（新增ICO支持）
# --------------------------
class ConvertThread(QThread):
    progress = pyqtSignal(str)  # 进度信号
    finish = pyqtSignal(bool)   # 完成信号

    def __init__(self, file_list, target_format, output_dir):
        super().__init__()
        self.file_list = file_list
        self.target_format = target_format.lower()
        self.output_dir = output_dir

    def run(self):
        success_count = 0
        for file_path in self.file_list:
            try:
                # 打开图片
                img = Image.open(file_path)
                # 处理透明通道（PNG/JPG转ICO专用）
                if self.target_format == "ico":
                    # ICO需要正方形，先裁剪为正方形
                    width, height = img.size
                    min_size = min(width, height)
                    left = (width - min_size) // 2
                    top = (height - min_size) // 2
                    right = left + min_size
                    bottom = top + min_size
                    img = img.crop((left, top, right, bottom))
                    # 调整ICO标准尺寸（支持多尺寸）
                    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128)]
                    img = img.resize((128,128), Image.Resampling.LANCZOS)
                elif self.target_format in ["jpg", "jpeg"] and img.mode == "RGBA":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg

                # 生成输出文件名
                file_name = os.path.basename(file_path)
                name, _ = os.path.splitext(file_name)
                # 适配收款码命名（自动替换特殊字符）
                name = name.replace("-pay", "").replace("pay-", "").replace("支付", "")
                output_path = os.path.join(
                    self.output_dir,
                    f"{name}.{self.target_format}"
                )

                # 保存图片（ICO专用逻辑）
                if self.target_format == "ico":
                    img.save(output_path, format="ICO", sizes=sizes)
                else:
                    img.save(output_path, self.target_format.upper())
                
                self.progress.emit(f"✅ 转换成功：{file_name} → {name}.{self.target_format}")
                success_count += 1
            except Exception as e:
                self.progress.emit(f"❌ 转换失败：{os.path.basename(file_path)} → {str(e)[:20]}")
        self.finish.emit(success_count == len(self.file_list))

# --------------------------
# 主窗口（新增ICO选项）
# --------------------------
class ImageConverter(QMainWindow):
    def __init__(self, app=None):
        super().__init__()
        from PyQt5.QtWidgets import QApplication
        self.app = app or QApplication.instance()
        self.setWindowTitle("一人公司 - 图片格式转换工具（支持ICO）")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f2f5; }
            QPushButton {
                background-color: #3182ce; color: white; border: none;
                border-radius: 8px; padding: 8px 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #2b6cb0; }
            QPushButton#convertBtn { background-color: #28a745; }
            QPushButton#convertBtn:hover { background-color: #218838; }
            QLabel { font-size: 12px; }
            QComboBox { padding: 6px; border-radius: 6px; border: 1px solid #ddd; }
            QListWidget { border-radius: 8px; border: 1px solid #ddd; padding: 8px; }
        """)

        # 初始化变量
        self.file_list = []
        self.output_dir = os.path.join(os.path.dirname(__file__), "转换结果")
        os.makedirs(self.output_dir, exist_ok=True)

        # 构建UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("📸 图片格式转换工具（支持ICO/收款码适配）")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 选择文件
        file_layout = QHBoxLayout()
        self.file_btn = QPushButton("📁 选择图片文件")
        self.file_btn.clicked.connect(self.select_files)
        file_layout.addWidget(self.file_btn)
        self.file_count = QLabel("已选择：0 个文件")
        file_layout.addWidget(self.file_count, alignment=Qt.AlignRight)
        layout.addLayout(file_layout)

        # 已选文件列表
        self.file_list_widget = QListWidget()
        self.placeholder_item = QListWidgetItem("已选择的图片文件会显示在这里...")
        self.placeholder_item.setForeground(QColor("#999999"))
        self.file_list_widget.addItem(self.placeholder_item)
        layout.addWidget(self.file_list_widget)

        # 格式选择（新增ICO选项）
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("🎯 目标格式："))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "JPEG", "BMP", "GIF", "ICO"])  # 新增ICO
        self.format_combo.setCurrentText("PNG")
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)

        # 输出路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("📂 输出路径："))
        self.path_label = QLabel(self.output_dir)
        self.path_label.setStyleSheet("color: #666; font-size: 11px;")
        path_layout.addWidget(self.path_label)
        self.path_btn = QPushButton("🔄 更换路径")
        self.path_btn.clicked.connect(self.select_output_dir)
        path_layout.addStretch()
        layout.addLayout(path_layout)

        # 转换按钮
        self.convert_btn = QPushButton("🚀 开始转换")
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.clicked.connect(self.start_convert)
        layout.addWidget(self.convert_btn, alignment=Qt.AlignCenter)

        # 进度提示
        self.progress_label = QLabel("✅ 准备就绪（支持ICO格式转换）")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #28a745; font-weight: bold;")
        layout.addWidget(self.progress_label)

    def select_files(self):
        """选择图片文件（支持更多格式）"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.ico);;所有文件 (*.*)"
        )
        if files:
            if self.file_list_widget.findItems("已选择的图片文件会显示在这里...", Qt.MatchExactly):
                self.file_list_widget.takeItem(self.file_list_widget.row(self.placeholder_item))
            
            self.file_list.extend(files)
            self.file_list_widget.addItems([os.path.basename(f) for f in files])
            self.file_count.setText(f"已选择：{len(self.file_list)} 个文件")
            self.progress_label.setText(f"📝 已选择 {len(self.file_list)} 个文件，等待转换...")

    def select_output_dir(self):
        """选择输出路径"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if dir_path:
            self.output_dir = dir_path
            self.path_label.setText(self.output_dir)
            self.progress_label.setText(f"📂 输出路径已更换：{self.output_dir}")

    def start_convert(self):
        """开始转换"""
        if not self.file_list:
            QMessageBox.warning(self, "提示", "请先选择要转换的图片文件！")
            return

        self.convert_btn.setEnabled(False)
        self.progress_label.setText("⚡ 正在转换中...")

        self.thread = ConvertThread(
            self.file_list,
            self.format_combo.currentText(),
            self.output_dir
        )
        self.thread.progress.connect(self.update_progress)
        self.thread.finish.connect(self.convert_finish)
        self.thread.start()

    def update_progress(self, msg):
        """更新进度"""
        self.progress_label.setText(msg)
        self.file_list_widget.addItem(msg)
        self.file_list_widget.scrollToBottom()

    def convert_finish(self, is_success):
        self.progress_label.setText("转换完成！" if is_success else "转换失败")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("\u25b6 \u5f00\u59cb\u8f6c\u6362")
        if is_success:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "\u6210\u529f", f"\u8f6c\u6362\u5b8c\u6210\uff0c\u6587\u4ef6\u5df2\u4fdd\u5b58\u81f3\uff1a{self.output_dir}")
def main():
    app = QApplication(sys.argv)
    font = QFont("PingFang SC")
    app.setFont(font)
    Image.MAX_IMAGE_PIXELS = None
    window = ImageConverter(app)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
