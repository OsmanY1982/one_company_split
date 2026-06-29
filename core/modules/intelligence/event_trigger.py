# -*- coding: utf-8 -*-
"""
事件触发器
监听业务事件并触发相应动作
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class EventType(Enum):
    """事件类型"""
    NEW_ORDER = "new_order"           # 新订单
    ORDER_CANCELLED = "order_cancelled"  # 订单取消
    STOCK_LOW = "stock_low"           # 库存不足
    MEMBER_EXPIRED = "member_expired" # 会员到期
    PAYMENT_RECEIVED = "payment_received"  # 收款
    LARGE_ORDER = "large_order"       # 大额订单
    RETURN_REQUEST = "return_request" # 退货申请
    SYNC_FAILED = "sync_failed"       # 同步失败


@dataclass
class Event:
    """事件定义"""
    id: str
    event_type: str
    source: str           # 事件来源
    data: Dict            # 事件数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processed: bool = False
    handler_result: Optional[Dict] = None


class EventTrigger:
    """事件触发器"""
    
    def __init__(self):
        self.events: List[Event] = []
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._thread = None
        self._listeners: Dict[str, Callable] = {}
        
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认事件处理器"""
        self._handlers = {
            EventType.NEW_ORDER.value: [self._handle_new_order],
            EventType.ORDER_CANCELLED.value: [self._handle_order_cancelled],
            EventType.STOCK_LOW.value: [self._handle_stock_low],
            EventType.MEMBER_EXPIRED.value: [self._handle_member_expired],
            EventType.PAYMENT_RECEIVED.value: [self._handle_payment_received],
            EventType.LARGE_ORDER.value: [self._handle_large_order],
            EventType.RETURN_REQUEST.value: [self._handle_return_request],
            EventType.SYNC_FAILED.value: [self._handle_sync_failed],
        }
    
    def register_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def emit(self, event_type: str, data: Dict, source: str = "system"):
        """触发事件"""
        import uuid
        event = Event(
            id=str(uuid.uuid4())[:8],
            event_type=event_type,
            source=source,
            data=data
        )
        self.events.append(event)
        
        # 异步处理
        threading.Thread(
            target=self._process_event,
            args=(event,),
            daemon=True
        ).start()
    
    def _process_event(self, event: Event):
        """处理事件"""
        handlers = self._handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                result = handler(event.data)
                event.handler_result = result
            except Exception as e:
                print(f"[EventTrigger] 事件处理失败: {event.event_type}, 错误: {e}")
        
        event.processed = True
    
    def _handle_new_order(self, data: Dict) -> Dict:
        """处理新订单事件"""
        order_id = data.get("order_id")
        amount = data.get("amount", 0)
        customer = data.get("customer_name", "")
        
        print(f"[EventTrigger] 新订单: #{order_id}, 金额: {amount}, 客户: {customer}")
        
        # 大额订单检查
        if amount > 10000:
            self.emit(EventType.LARGE_ORDER.value, data, source="event_trigger")
        
        # 自动分配任务给销售助手
        # TODO: 集成数字员工系统
        
        return {"action": "processed", "order_id": order_id}
    
    def _handle_order_cancelled(self, data: Dict) -> Dict:
        """处理订单取消事件"""
        order_id = data.get("order_id")
        reason = data.get("reason", "")
        
        print(f"[EventTrigger] 订单取消: #{order_id}, 原因: {reason}")
        
        # 恢复库存
        # TODO: 调用库存恢复逻辑
        
        return {"action": "stock_restored", "order_id": order_id}
    
    def _handle_stock_low(self, data: Dict) -> Dict:
        """处理库存不足事件"""
        product_id = data.get("product_id")
        product_name = data.get("product_name", "")
        current_stock = data.get("current_stock", 0)
        threshold = data.get("threshold", 10)
        
        print(f"[EventTrigger] 库存预警: {product_name}, 当前: {current_stock}, 阈值: {threshold}")
        
        # 发送通知给库存管理员
        # TODO: 集成通知系统
        
        return {"action": "alert_sent", "product_id": product_id}
    
    def _handle_member_expired(self, data: Dict) -> Dict:
        """处理会员到期事件"""
        member_id = data.get("member_id")
        member_name = data.get("member_name", "")
        expiry_date = data.get("expiry_date", "")
        
        print(f"[EventTrigger] 会员到期: {member_name}, 到期日: {expiry_date}")
        
        # 发送续费提醒
        # TODO: 集成消息推送
        
        return {"action": "reminder_sent", "member_id": member_id}
    
    def _handle_payment_received(self, data: Dict) -> Dict:
        """处理收款事件"""
        order_id = data.get("order_id")
        amount = data.get("amount", 0)
        payment_method = data.get("payment_method", "")
        
        print(f"[EventTrigger] 收款: #{order_id}, 金额: {amount}, 方式: {payment_method}")
        
        # 自动确认订单
        # TODO: 调用订单确认逻辑
        
        return {"action": "order_confirmed", "order_id": order_id}
    
    def _handle_large_order(self, data: Dict) -> Dict:
        """处理大额订单事件"""
        order_id = data.get("order_id")
        amount = data.get("amount", 0)
        
        print(f"[EventTrigger] 大额订单: #{order_id}, 金额: {amount}")
        
        # 发送给经理审批
        # TODO: 集成审批流程
        
        return {"action": "approval_required", "order_id": order_id}
    
    def _handle_return_request(self, data: Dict) -> Dict:
        """处理退货申请事件"""
        order_id = data.get("order_id")
        product_id = data.get("product_id")
        reason = data.get("reason", "")
        
        print(f"[EventTrigger] 退货申请: #{order_id}, 原因: {reason}")
        
        # 自动审核退货
        # TODO: 集成退货审核逻辑
        
        return {"action": "return_reviewed", "order_id": order_id}
    
    def _handle_sync_failed(self, data: Dict) -> Dict:
        """处理同步失败事件"""
        table_name = data.get("table_name", "")
        error = data.get("error", "")
        
        print(f"[EventTrigger] 同步失败: {table_name}, 错误: {error}")
        
        # 重试同步
        # TODO: 调用重试逻辑
        
        return {"action": "retry_scheduled", "table_name": table_name}
    
    def get_recent_events(self, event_type: str = None, limit: int = 50) -> List[Event]:
        """获取最近事件"""
        events = self.events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]
    
    def get_event_stats(self) -> Dict:
        """获取事件统计"""
        stats = {}
        for event in self.events:
            stats[event.event_type] = stats.get(event.event_type, 0) + 1
        return stats


# 全局触发器实例
_trigger = None

def get_trigger() -> EventTrigger:
    """获取全局触发器实例"""
    global _trigger
    if _trigger is None:
        _trigger = EventTrigger()
    return _trigger
