# -*- coding: utf-8 -*-
"""
系统通知弹窗组件
右下角浮窗通知
"""
from typing import Optional
from PyQt5.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt, QPoint
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QApplication
from PyQt5.QtGui import QIcon, QPixmap


class NotificationToast(QFrame):
    """通知弹窗"""
    
    _active_toasts: list = []
    
    def __init__(self, title: str = "", message: str = "",
                 icon: str = "info", duration: int = 3000,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.icon_type = icon
        self.duration = duration
        self._animation = None
        self._opacity_animation = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setFixedSize(320, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                           Qt.Tool | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        self._setup_shadow()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #333;
            border: none; background: transparent;
        """)
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("""
            font-size: 12px; color: #666; border: none; background: transparent;
        """)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
    
    def _setup_shadow(self):
        """设置阴影效果"""
        try:
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            from PyQt5.QtGui import QColor
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 60))
            self.setGraphicsEffect(shadow)
        except Exception:
            pass
    
    def show_toast(self):
        """显示通知"""
        self._position_toast()
        self.show()
        self._fade_in()
        NotificationToast._active_toasts.append(self)
        if self.duration > 0:
            QTimer.singleShot(self.duration, self.close_toast)
    
    def _position_toast(self):
        """定位到屏幕右下角"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.right() - self.width() - 20
            y_offset = 20
            for toast in NotificationToast._active_toasts:
                if toast.isVisible():
                    y_offset += toast.height() + 10
            y = screen_geometry.bottom() - y_offset - self.height()
            self.move(x, y)
    
    def _fade_in(self):
        """淡入动画"""
        self._opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_animation.setDuration(300)
        self._opacity_animation.setStartValue(0.0)
        self._opacity_animation.setEndValue(1.0)
        self._opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_animation.start()
    
    def close_toast(self):
        """关闭通知（带淡出）"""
        self._opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_animation.setDuration(200)
        self._opacity_animation.setStartValue(1.0)
        self._opacity_animation.setEndValue(0.0)
        self._opacity_animation.finished.connect(self._on_fade_out_finished)
        self._opacity_animation.start()
    
    def _on_fade_out_finished(self):
        """淡出完成"""
        self.hide()
        self.deleteLater()
        if self in NotificationToast._active_toasts:
            NotificationToast._active_toasts.remove(self)


def show_notification(title: str, message: str, icon: str = "info",
                     duration: int = 3000, parent: Optional[QWidget] = None):
    """快速显示通知的便捷函数"""
    toast = NotificationToast(title, message, icon, duration, parent)
    toast.show_toast()
    return toast


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    btn = QWidget()
    btn.setWindowTitle("通知测试")
    btn.resize(400, 200)
    btn.show()
    QTimer.singleShot(500, lambda: show_notification("系统消息", "数据同步完成", duration=5000))
    QTimer.singleShot(1500, lambda: show_notification("新订单", "客户'测试公司'下了新订单 ¥1,200.00", duration=4000))
    sys.exit(app.exec_())
