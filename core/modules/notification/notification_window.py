"""
Notification Window - 桌面端通知中心窗口
PyQt5 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton,
    QComboBox, QMessageBox, QMenu, QAction, QSystemTrayIcon,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from notification_service import (
    NotificationService, NotificationType, NotificationChannel
)


class NotificationWindow(QMainWindow):
    """通知中心窗口"""
    
    notification_clicked = pyqtSignal(int)  # 通知ID
    
    def __init__(self):
        super().__init__()
        self.service = NotificationService()
        self.init_ui()
        self.load_notifications()
        
        # 定时刷新
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_notifications)
        self.timer.start(30000)  # 30秒刷新
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("通知中心")
        self.setGeometry(100, 100, 600, 500)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        # 类型筛选
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部类型", None)
        for notif_type in NotificationType:
            self.type_filter.addItem(
                self.get_type_name(notif_type), 
                notif_type.value
            )
        self.type_filter.currentIndexChanged.connect(self.on_filter_changed)
        toolbar.addWidget(QLabel("筛选:"))
        toolbar.addWidget(self.type_filter)
        
        toolbar.addStretch()
        
        # 未读数量
        self.unread_label = QLabel("未读: 0")
        toolbar.addWidget(self.unread_label)
        
        # 全部已读按钮
        self.read_all_btn = QPushButton("全部已读")
        self.read_all_btn.clicked.connect(self.mark_all_read)
        toolbar.addWidget(self.read_all_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_notifications)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # 通知列表
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def load_notifications(self):
        """加载通知列表"""
        self.list_widget.clear()
        
        # 获取筛选条件
        notif_type = None
        type_data = self.type_filter.currentData()
        if type_data:
            notif_type = NotificationType(type_data)
        
        # 获取通知
        notifications = self.service.get_notifications(
            notif_type=notif_type,
            limit=100
        )
        
        # 获取统计
        stats = self.service.get_notification_stats()
        unread_count = stats.get('unread', 0)
        self.unread_label.setText(f"未读: {unread_count}")
        
        # 添加到列表
        for notif in notifications:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, notif['id'])
            
            # 设置显示文本
            type_name = self.get_type_name(NotificationType(notif['type']))
            title = notif['title']
            content = notif['content']
            is_read = notif['is_read']
            
            display_text = f"[{type_name}] {title}\n{content[:50]}..."
            item.setText(display_text)
            
            # 未读通知加粗
            if not is_read:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setBackground(QColor(230, 245, 255))
            
            self.list_widget.addItem(item)
        
        self.statusBar().showMessage(f"共 {len(notifications)} 条通知")
    
    def on_filter_changed(self):
        """筛选条件改变"""
        self.load_notifications()
    
    def on_item_clicked(self, item):
        """点击通知项"""
        notif_id = item.data(Qt.UserRole)
        self.notification_clicked.emit(notif_id)
        
        # 标记为已读
        self.service.mark_as_read(notif_id)
        
        # 刷新显示
        self.load_notifications()
    
    def mark_all_read(self):
        """标记全部已读"""
        count = self.service.mark_all_as_read()
        QMessageBox.information(self, "提示", f"已标记 {count} 条通知为已读")
        self.load_notifications()
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.list_widget.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        # 标记已读
        read_action = QAction("标记已读", self)
        read_action.triggered.connect(lambda: self.mark_item_read(item))
        menu.addAction(read_action)
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_item(item))
        menu.addAction(delete_action)
        
        menu.exec_(self.list_widget.viewport().mapToGlobal(position))
    
    def mark_item_read(self, item):
        """标记单项已读"""
        notif_id = item.data(Qt.UserRole)
        self.service.mark_as_read(notif_id)
        self.load_notifications()
    
    def delete_item(self, item):
        """删除通知"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除这条通知吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            notif_id = item.data(Qt.UserRole)
            self.service.delete_notification(notif_id)
            self.load_notifications()
    
    def get_type_name(self, notif_type: NotificationType) -> str:
        """获取类型名称"""
        type_names = {
            NotificationType.SYSTEM: "系统",
            NotificationType.ORDER: "订单",
            NotificationType.CUSTOMER: "客户",
            NotificationType.FINANCE: "财务",
            NotificationType.INVENTORY: "库存",
        }
        return type_names.get(notif_type, "未知")


class NotificationTrayIcon(QSystemTrayIcon):
    """系统托盘通知图标"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = NotificationService()
        self.init_ui()
        
        # 定时检查新通知
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_new_notifications)
        self.timer.start(30000)  # 30秒
    
    def init_ui(self):
        """初始化托盘图标"""
        self.setIcon(QIcon("icons/notification.png"))
        self.setToolTip("通知中心")
        
        # 右键菜单
        menu = QMenu()
        
        show_action = QAction("打开通知中心", self)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        self.activated.connect(self.on_activated)
    
    def on_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """显示通知窗口"""
        self.window = NotificationWindow()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
    
    def check_new_notifications(self):
        """检查新通知"""
        unread_count = self.service.get_unread_count()
        
        if unread_count > 0:
            self.showMessage(
                "新通知",
                f"您有 {unread_count} 条未读通知",
                QSystemTrayIcon.Information,
                3000
            )


# 便捷函数
def show_notification_window():
    """显示通知窗口"""
    app = QApplication.instance() or QApplication([])
    window = NotificationWindow()
    window.show()
    return window


def create_tray_icon():
    """创建托盘图标"""
    app = QApplication.instance() or QApplication([])
    tray = NotificationTrayIcon()
    tray.show()
    return tray
