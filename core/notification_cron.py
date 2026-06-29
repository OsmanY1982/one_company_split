# -*- coding: utf-8 -*-
"""
消息通知系统 - 会员到期提醒、订单提醒
被cron定时调用，每小时检查一次
"""
import sys
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox, QApplication
from core.database import get_conn, close_conn

# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")


def check_member_expiry():
    """检查即将到期的会员"""
    alerts = []
    try:
        # 检查VIP会员（7天内到期）
        conn = get_conn("member.db")
        cursor = conn.cursor()
        today = datetime.now()
        week_later = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT name, phone, vip_expire, level FROM member 
            WHERE vip_expire <= ? AND vip_expire != '' AND status = '正常'
        """, (week_later,))
        rows = cursor.fetchall()
        close_conn("member.db")
        
        for name, phone, expire, level in rows:
            if expire:
                expire_date = datetime.strptime(expire, "%Y-%m-%d")
                days_left = (expire_date - today).days
                if 0 <= days_left <= 7:
                    alerts.append(f"  {name} ({phone}) - {level}会员将在{days_left}天后到期 ({expire})")
                elif days_left < 0:
                    alerts.append(f"  {name} ({phone}) - {level}会员已过期{abs(days_left)}天 ({expire})")
    except Exception as e:
        print(f"检查会员到期失败: {e}")
    
    return alerts


def check_pending_orders():
    """检查待处理订单"""
    alerts = []
    try:
        conn = get_conn("order.db")
        cursor = conn.cursor()
        
        # 待付款订单
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = '待付款'")
        pending_pay = cursor.fetchone()[0]
        if pending_pay > 0:
            alerts.append(f"  有 {pending_pay} 个订单待付款")
        
        # 已付款待发货
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = '已付款'")
        pending_ship = cursor.fetchone()[0]
        if pending_ship > 0:
            alerts.append(f"  有 {pending_ship} 个订单已付款待发货")
        
        # 今日新订单
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (f"{today}%",))
        today_orders = cursor.fetchone()[0]
        if today_orders > 0:
            alerts.append(f"  今日新增 {today_orders} 个订单")
        
        close_conn("order.db")
    except Exception as e:
        print(f"检查订单失败: {e}")
    
    return alerts


def show_notification(alerts):
    """显示通知弹窗"""
    if not alerts:
        return
    
    # 创建临时QApplication用于弹窗
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    message = "\n".join(alerts)
    QMessageBox.information(None, "系统提醒", message)


def check_anomaly_alerts():
    """检查业务异常"""
    alerts = []
    try:
        from modules.intelligence.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector(data_dir=DATA_DIR)
        new_alerts = detector.run_full_scan()
        
        for alert in new_alerts:
            if alert.severity in ["high", "critical"]:
                alerts.append(f"  [{alert.severity.upper()}] {alert.title}: {alert.description}")
    except Exception as e:
        print(f"检查异常失败: {e}")
    
    return alerts


def check_low_stock():
    """检查低库存"""
    alerts = []
    try:
        conn = get_conn("orders.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, stock, price FROM products WHERE stock <= 10 ORDER BY stock ASC LIMIT 5")
        rows = cursor.fetchall()
        close_conn("orders.db")
        
        for name, stock, price in rows:
            alerts.append(f"  {name}：库存仅剩 {stock} 件")
    except Exception as e:
        print(f"检查库存失败: {e}")
    
    return alerts


def main():
    """主检查函数"""
    print(f"[{datetime.now()}] 执行消息通知检查...")
    
    all_alerts = []
    
    # 检查会员到期
    member_alerts = check_member_expiry()
    if member_alerts:
        all_alerts.append("【会员到期提醒】")
        all_alerts.extend(member_alerts)
    
    # 检查订单
    order_alerts = check_pending_orders()
    if order_alerts:
        if all_alerts:
            all_alerts.append("")
        all_alerts.append("【订单提醒】")
        all_alerts.extend(order_alerts)
    
    # 检查业务异常
    anomaly_alerts = check_anomaly_alerts()
    if anomaly_alerts:
        if all_alerts:
            all_alerts.append("")
        all_alerts.append("【业务异常预警】")
        all_alerts.extend(anomaly_alerts)
    
    # 检查低库存
    stock_alerts = check_low_stock()
    if stock_alerts:
        if all_alerts:
            all_alerts.append("")
        all_alerts.append("【库存预警】")
        all_alerts.extend(stock_alerts)
    
    # 显示通知
    if all_alerts:
        show_notification(all_alerts)
        print(f"发现 {len(all_alerts)} 条提醒")
    else:
        print("暂无提醒")
    
    return len(all_alerts)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count == 0 else 1)
