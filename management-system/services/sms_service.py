"""
短信服务
集成阿里云/腾讯云短信接口
"""

import json
import hashlib
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SMSService:
    """短信服务"""

    def __init__(self):
        self._providers = {
            "aliyun": {"name": "阿里云短信", "enabled": False, "config": {}},
            "tencent": {"name": "腾讯云短信", "enabled": False, "config": {}},
        }
        self._templates: Dict[str, Dict] = {}
        self._send_history: List[Dict] = []
        self._rate_limit: Dict[str, datetime] = {}  # 发送频率限制

    def configure(self, provider: str, config: Dict) -> Dict:
        """配置短信服务商"""
        if provider not in self._providers:
            return {"success": False, "message": "不支持的短信服务商"}

        self._providers[provider]["config"] = config
        self._providers[provider]["enabled"] = True

        return {"success": True, "message": f"{self._providers[provider]['name']} 配置成功"}

    def register_template(self, template_id: str, content: str, description: str = ""):
        """注册短信模板"""
        self._templates[template_id] = {
            "content": content,
            "description": description,
        }

    def send(self,
             phone: str,
             message: str,
             provider: str = "aliyun") -> Dict:
        """发送短信"""
        # 频率限制检查
        if phone in self._rate_limit:
            elapsed = datetime.now() - self._rate_limit[phone]
            if elapsed < timedelta(seconds=60):
                return {"success": False, "message": "发送频率过快，请稍后再试"}

        if provider not in self._providers:
            return {"success": False, "message": "不支持的短信服务商"}

        prov = self._providers[provider]
        if not prov["enabled"]:
            return {"success": False, "message": f"{prov['name']} 未配置"}

        try:
            # 模拟发送
            send_id = hashlib.md5(f"{phone}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
            self._rate_limit[phone] = datetime.now()

            result = {
                "success": True,
                "send_id": send_id,
                "phone": phone,
                "message": message,
                "provider": provider,
                "sent_at": datetime.now().isoformat(),
            }

            self._send_history.append(result)
            return result

        except Exception as e:
            return {"success": False, "message": str(e)}

    def send_by_template(self,
                         phone: str,
                         template_id: str,
                         params: Optional[Dict] = None,
                         provider: str = "aliyun") -> Dict:
        """通过模板发送"""
        template = self._templates.get(template_id)
        if not template:
            return {"success": False, "message": "模板不存在"}

        content = template["content"]
        if params:
            for key, value in params.items():
                content = content.replace(f"{{{key}}}", str(value))

        return self.send(phone, content, provider)

    def send_verification_code(self, phone: str) -> Dict:
        """发送验证码"""
        code = str(random.randint(100000, 999999))

        result = self.send(
            phone,
            f"【一人公司】您的验证码是 {code}，5 分钟内有效。",
        )

        if result.get("success"):
            result["code"] = code  # 实际应用中应存储到缓存

        return result

    def send_order_notification(self, phone: str, order_no: str, amount: float) -> Dict:
        """发送订单通知"""
        return self.send(
            phone,
            f"【一人公司】订单 {order_no} 已创建，金额 ¥{amount:.2f}，我们将尽快处理。",
        )

    def send_payment_reminder(self, phone: str, customer_name: str, amount: float) -> Dict:
        """发送付款提醒"""
        return self.send(
            phone,
            f"【一人公司】{customer_name}，您有 ¥{amount:.2f} 待付款，请及时处理。",
        )

    def batch_send(self, phones: List[str], message: str, provider: str = "aliyun") -> Dict:
        """批量发送"""
        results = []
        for phone in phones:
            result = self.send(phone, message, provider)
            results.append(result)

        success = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        return {
            "success": True,
            "total": len(phones),
            "success_count": len(success),
            "failed_count": len(failed),
            "results": results,
        }

    def get_send_history(self, limit: int = 50) -> List[Dict]:
        """获取发送历史"""
        return self._send_history[-limit:]

    def get_provider_status(self) -> Dict:
        """获取服务商状态"""
        return {
            provider: {
                "name": info["name"],
                "enabled": info["enabled"],
            }
            for provider, info in self._providers.items()
        }

    def get_statistics(self) -> Dict:
        """获取统计"""
        today = datetime.now().date()
        today_count = sum(
            1 for h in self._send_history
            if datetime.fromisoformat(h["sent_at"]).date() == today
        )

        return {
            "total_sent": len(self._send_history),
            "today_sent": today_count,
        }

