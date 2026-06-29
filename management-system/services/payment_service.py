"""
支付服务
集成支付宝、微信支付
"""

import json
import hashlib
import time
from typing import Dict, List, Optional
from datetime import datetime


class PaymentService:
    """支付服务"""

    def __init__(self):
        self._payment_methods = {
            "alipay": {"name": "支付宝", "enabled": False, "config": {}},
            "wechat": {"name": "微信支付", "enabled": False, "config": {}},
            "cash": {"name": "现金", "enabled": True, "config": {}},
            "bank_transfer": {"name": "银行转账", "enabled": True, "config": {}},
        }

    def configure(self, method: str, config: Dict) -> Dict:
        """配置支付方式"""
        if method not in self._payment_methods:
            return {"success": False, "message": "不支持的支付方式"}

        self._payment_methods[method]["config"] = config
        self._payment_methods[method]["enabled"] = True

        return {"success": True, "message": f"{self._payment_methods[method]['name']} 配置成功"}

    def create_payment(self,
                       order_no: str,
                       amount: float,
                       method: str,
                       description: str = "") -> Dict:
        """创建支付"""
        if method not in self._payment_methods:
            return {"success": False, "message": "不支持的支付方式"}

        payment_method = self._payment_methods[method]
        if not payment_method["enabled"]:
            return {"success": False, "message": f"{payment_method['name']} 未启用"}

        payment = {
            "payment_id": self._generate_payment_id(),
            "order_no": order_no,
            "amount": amount,
            "method": method,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        # 根据支付方式生成不同的支付参数
        if method == "alipay":
            payment.update(self._create_alipay_payment(order_no, amount, description))
        elif method == "wechat":
            payment.update(self._create_wechat_payment(order_no, amount, description))

        return {"success": True, "payment": payment}

    def _create_alipay_payment(self, order_no: str, amount: float, description: str) -> Dict:
        """创建支付宝支付"""
        # 模拟支付宝统一下单
        return {
            "platform": "alipay",
            "qr_code": f"alipay://qr/{self._generate_payment_id()}",
            "out_trade_no": self._generate_trade_no("ALI"),
        }

    def _create_wechat_payment(self, order_no: str, amount: float, description: str) -> Dict:
        """创建微信支付"""
        # 模拟微信支付统一下单
        return {
            "platform": "wechat",
            "qr_code": f"weixin://wxpay/{self._generate_payment_id()}",
            "prepay_id": self._generate_trade_no("WX"),
        }

    def query_payment(self, payment_id: str) -> Dict:
        """查询支付状态"""
        # 模拟查询
        return {
            "success": True,
            "payment_id": payment_id,
            "status": "success",
            "paid_at": datetime.now().isoformat(),
        }

    def refund(self, payment_id: str, amount: float, reason: str = "") -> Dict:
        """退款"""
        return {
            "success": True,
            "refund_id": self._generate_payment_id(),
            "payment_id": payment_id,
            "amount": amount,
            "reason": reason,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
        }

    def get_payment_methods(self) -> Dict:
        """获取支付方式列表"""
        return self._payment_methods

    def get_enabled_methods(self) -> List[Dict]:
        """获取已启用的支付方式"""
        return [
            {"method": method, "name": info["name"]}
            for method, info in self._payment_methods.items()
            if info["enabled"]
        ]

    def verify_callback(self, method: str, data: Dict) -> Dict:
        """验证支付回调"""
        # 模拟签名验证
        return {
            "success": True,
            "payment_id": data.get("payment_id", ""),
            "verified": True,
        }

    @staticmethod
    def _generate_payment_id() -> str:
        """生成支付ID"""
        return f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()}"

    @staticmethod
    def _generate_trade_no(prefix: str) -> str:
        """生成交易号"""
        return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{hashlib.md5(str(time.time()).encode()).hexdigest()[:6].upper()}"

    def calculate_fee(self, amount: float, method: str) -> Dict:
        """计算手续费"""
        fee_rates = {
            "alipay": 0.006,   # 0.6%
            "wechat": 0.006,   # 0.6%
            "bank_transfer": 0.001,  # 0.1%
            "cash": 0,
        }

        rate = fee_rates.get(method, 0)
        fee = round(amount * rate, 2)

        return {
            "method": method,
            "amount": amount,
            "fee_rate": rate,
            "fee": fee,
            "net_amount": amount - fee,
        }

