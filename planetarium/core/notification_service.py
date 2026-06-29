"""
Notification Service - 通知中心服务
支持站内信、邮件、短信三种通知方式
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class NotificationType(Enum):
    SYSTEM = "system"      # 系统通知
    ORDER = "order"        # 订单通知
    CUSTOMER = "customer"  # 客户通知
    FINANCE = "finance"    # 财务通知
    INVENTORY = "inventory" # 库存通知


class NotificationChannel(Enum):
    IN_APP = "in_app"      # 站内信
    EMAIL = "email"        # 邮件
    SMS = "sms"            # 短信


class NotificationService:
    """通知中心服务"""
    
    def __init__(self, db_path: str = "data/notifications.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'in_app',
                recipient_id TEXT,
                recipient_email TEXT,
                recipient_phone TEXT,
                is_read INTEGER DEFAULT 0,
                is_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                sent_at TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON notifications(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipient ON notifications(recipient_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_read ON notifications(is_read)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON notifications(created_at)")
        
        conn.commit()
        conn.close()
    
    def create_notification(
        self,
        title: str,
        content: str,
        notif_type: NotificationType,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        recipient_id: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """创建通知"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO notifications 
            (title, content, type, channel, recipient_id, recipient_email, recipient_phone, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, content, notif_type.value, channel.value,
            recipient_id, recipient_email, recipient_phone,
            json.dumps(metadata) if metadata else None
        ))
        
        notif_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 如果是站内信，标记为已发送
        if channel == NotificationChannel.IN_APP:
            self.mark_as_sent(notif_id)
        
        return notif_id
    
    def get_notifications(
        self,
        recipient_id: Optional[str] = None,
        notif_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """获取通知列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM notifications WHERE 1=1"
        params = []
        
        if recipient_id:
            query += " AND recipient_id = ?"
            params.append(recipient_id)
        
        if notif_type:
            query += " AND type = ?"
            params.append(notif_type.value)
        
        if is_read is not None:
            query += " AND is_read = ?"
            params.append(1 if is_read else 0)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        notifications = []
        for row in rows:
            notif = dict(row)
            if notif.get('metadata'):
                notif['metadata'] = json.loads(notif['metadata'])
            notifications.append(notif)
        
        conn.close()
        return notifications
    
    def get_unread_count(self, recipient_id: Optional[str] = None) -> int:
        """获取未读通知数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM notifications WHERE is_read = 0"
        params = []
        
        if recipient_id:
            query += " AND recipient_id = ?"
            params.append(recipient_id)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def mark_as_read(self, notification_id: int) -> bool:
        """标记通知为已读"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE notifications 
            SET is_read = 1, read_at = ? 
            WHERE id = ?
        """, (datetime.now().isoformat(), notification_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def mark_all_as_read(self, recipient_id: Optional[str] = None) -> int:
        """标记所有通知为已读"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "UPDATE notifications SET is_read = 1, read_at = ? WHERE is_read = 0"
        params = [datetime.now().isoformat()]
        
        if recipient_id:
            query += " AND recipient_id = ?"
            params.append(recipient_id)
        
        cursor.execute(query, params)
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return updated_count
    
    def mark_as_sent(self, notification_id: int) -> bool:
        """标记通知为已发送"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE notifications 
            SET is_sent = 1, sent_at = ? 
            WHERE id = ?
        """, (datetime.now().isoformat(), notification_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def delete_notification(self, notification_id: int) -> bool:
        """删除通知"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_notification_stats(self, recipient_id: Optional[str] = None) -> Dict:
        """获取通知统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                type,
                COUNT(*) as total,
                SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread
            FROM notifications
            WHERE 1=1
        """
        params = []
        
        if recipient_id:
            query += " AND recipient_id = ?"
            params.append(recipient_id)
        
        query += " GROUP BY type"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        stats = {
            "total": 0,
            "unread": 0,
            "by_type": {}
        }
        
        for row in rows:
            notif_type, total, unread = row
            stats["total"] += total
            stats["unread"] += unread
            stats["by_type"][notif_type] = {
                "total": total,
                "unread": unread
            }
        
        conn.close()
        return stats


# 便捷函数
def notify_order_created(order_id: str, customer_name: str, amount: float):
    """订单创建通知"""
    service = NotificationService()
    service.create_notification(
        title="新订单",
        content=f"客户 {customer_name} 创建了订单 #{order_id}，金额 ¥{amount:.2f}",
        notif_type=NotificationType.ORDER,
        metadata={"order_id": order_id, "amount": amount}
    )


def notify_low_stock(product_name: str, current_stock: int, min_stock: int):
    """库存不足通知"""
    service = NotificationService()
    service.create_notification(
        title="库存预警",
        content=f"产品 {product_name} 库存不足，当前 {current_stock}，最低要求 {min_stock}",
        notif_type=NotificationType.INVENTORY,
        metadata={"product_name": product_name, "current_stock": current_stock}
    )


def notify_payment_received(order_id: str, amount: float):
    """收款通知"""
    service = NotificationService()
    service.create_notification(
        title="收款成功",
        content=f"订单 #{order_id} 收到付款 ¥{amount:.2f}",
        notif_type=NotificationType.FINANCE,
        metadata={"order_id": order_id, "amount": amount}
    )
