"""
系统通知服务
Windows/macOS 原生通知
"""

import platform
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class NotificationService:
    """系统通知服务"""

    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.notification_file = os.path.join(config_dir, "notifications.json")
        self._notifications: List[Dict] = []
        self._enabled = True
        self._load_notifications()

    def _load_notifications(self):
        """加载通知记录"""
        if os.path.exists(self.notification_file):
            try:
                with open(self.notification_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._notifications = data.get("items", [])
            except Exception:
                pass

    def _save_notifications(self):
        """保存通知记录"""
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.notification_file, "w", encoding="utf-8") as f:
            json.dump({"items": self._notifications}, f, ensure_ascii=False, indent=2)

    def send(self, title: str, message: str, level: str = "info") -> Dict:
        """发送通知"""
        system = platform.system()

        try:
            if system == "Windows":
                self._send_windows_notification(title, message)
            elif system == "Darwin":
                self._send_macos_notification(title, message)
            else:
                self._send_linux_notification(title, message)

            # 记录通知
            notification = {
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "read": False,
            }
            self._notifications.append(notification)
            self._save_notifications()

            return {"success": True, "message": "通知已发送"}

        except Exception as e:
            return {"success": False, "message": f"通知发送失败: {e}"}

    def _send_windows_notification(self, title: str, message: str):
        """Windows通知"""
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="一人公司",
            timeout=5,
        )

    def _send_macos_notification(self, title: str, message: str):
        """macOS通知"""
        import subprocess
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], capture_output=True)

    def _send_linux_notification(self, title: str, message: str):
        """Linux通知"""
        import subprocess
        subprocess.run(["notify-send", title, message], capture_output=True)

    def send_order_notification(self, order_no: str, amount: float):
        """发送订单通知"""
        return self.send(
            title="新订单",
            message=f"订单 {order_no}，金额 ¥{amount:,.2f}",
            level="info",
        )

    def send_stock_alert(self, product_name: str, current_stock: int):
        """发送库存预警"""
        return self.send(
            title="库存预警",
            message=f"{product_name} 库存不足，当前库存: {current_stock}",
            level="warning",
        )

    def send_payment_reminder(self, customer_name: str, amount: float, due_date: str):
        """发送付款提醒"""
        return self.send(
            title="付款提醒",
            message=f"{customer_name} 应付 ¥{amount:,.2f}，到期日: {due_date}",
            level="warning",
        )

    def get_notifications(self, limit: int = 20, unread_only: bool = False) -> List[Dict]:
        """获取通知列表"""
        notifications = self._notifications

        if unread_only:
            notifications = [n for n in notifications if not n.get("read")]

        return notifications[-limit:]

    def mark_as_read(self, timestamp: str):
        """标记为已读"""
        for notification in self._notifications:
            if notification.get("timestamp") == timestamp:
                notification["read"] = True
        self._save_notifications()

    def mark_all_read(self):
        """全部标记为已读"""
        for notification in self._notifications:
            notification["read"] = True
        self._save_notifications()

    def clear_all(self):
        """清空通知"""
        self._notifications = []
        self._save_notifications()

    def get_unread_count(self) -> int:
        """获取未读数量"""
        return sum(1 for n in self._notifications if not n.get("read"))

    def set_enabled(self, enabled: bool):
        """启用/禁用通知"""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

