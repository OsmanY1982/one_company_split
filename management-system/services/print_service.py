"""
打印服务
支持小票打印、标签打印、A4文档打印
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime


class PrintService:
    """打印服务"""

    def __init__(self):
        self._printers: List[Dict] = []
        self._default_printer: Optional[str] = None
        self._detect_printers()

    def _detect_printers(self):
        """检测打印机"""
        import platform

        system = platform.system()
        self._printers = []

        try:
            if system == "Windows":
                import win32print
                printers = win32print.EnumPrinters(2)  # PRINTER_ENUM_LOCAL
                for printer in printers:
                    self._printers.append({
                        "name": printer[2],
                        "is_default": printer[2] == win32print.GetDefaultPrinter(),
                    })
            elif system == "Darwin":
                # macOS
                import subprocess
                result = subprocess.run(
                    ["lpstat", "-p"],
                    capture_output=True,
                    text=True,
                )
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split()
                        name = parts[1] if len(parts) > 1 else line
                        self._printers.append({
                            "name": name,
                            "is_default": False,
                        })
        except Exception:
            # 添加虚拟打印机
            self._printers.append({
                "name": "虚拟打印机",
                "is_default": True,
            })

        if self._printers:
            default = next((p for p in self._printers if p["is_default"]), None)
            self._default_printer = default["name"] if default else self._printers[0]["name"]

    def get_printers(self) -> List[Dict]:
        """获取打印机列表"""
        return self._printers

    def set_default_printer(self, printer_name: str):
        """设置默认打印机"""
        self._default_printer = printer_name

    def print_receipt(self,
                      content: str,
                      printer_name: Optional[str] = None,
                      copies: int = 1) -> Dict:
        """打印小票"""
        printer = printer_name or self._default_printer

        if not printer:
            return {"success": False, "message": "未指定打印机"}

        try:
            # 模拟打印
            return {
                "success": True,
                "printer": printer,
                "content_length": len(content),
                "copies": copies,
                "printed_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "message": f"打印失败: {e}"}

    def print_label(self,
                    product_name: str,
                    barcode: str,
                    price: float,
                    printer_name: Optional[str] = None,
                    copies: int = 1) -> Dict:
        """打印标签"""
        content = f"""
产品: {product_name}
条码: {barcode}
价格: ¥{price:.2f}
        """

        return self.print_receipt(content.strip(), printer_name, copies)

    def print_order(self,
                    order_data: Dict,
                    printer_name: Optional[str] = None) -> Dict:
        """打印订单"""
        items_text = "\n".join(
            f"  {item.get('name', '')} x{item.get('quantity', 0)} = ¥{item.get('amount', 0):.2f}"
            for item in order_data.get("items", [])
        )

        content = f"""
┌──────────────────────┐
│      一人公司          │
│    订单小票            │
├──────────────────────┤
订单号: {order_data.get('order_no', '')}
时间: {order_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
客户: {order_data.get('customer_name', '')}
───────────────────────
{items_text}
───────────────────────
合计: ¥{order_data.get('total_amount', 0):.2f}
│
│    谢谢惠顾！
└──────────────────────┘
        """

        return self.print_receipt(content.strip(), printer_name)

    def print_batch_labels(self,
                           products: List[Dict],
                           printer_name: Optional[str] = None) -> Dict:
        """批量打印标签"""
        results = []
        for product in products:
            result = self.print_label(
                product.get("name", ""),
                product.get("barcode", ""),
                product.get("price", 0),
                printer_name,
                1,
            )
            results.append(result)

        return {
            "success": True,
            "total": len(products),
            "results": results,
        }

    def preview_receipt(self, order_data: Dict) -> str:
        """预览小票"""
        items_text = "\n".join(
            f"  {item.get('name', '')} x{item.get('quantity', 0)} = ¥{item.get('amount', 0):.2f}"
            for item in order_data.get("items", [])
        )

        return f"""
┌──────────────────────┐
│      一人公司          │
│    订单小票            │
├──────────────────────┤
订单号: {order_data.get('order_no', '')}
时间: {order_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
客户: {order_data.get('customer_name', '')}
───────────────────────
{items_text}
───────────────────────
合计: ¥{order_data.get('total_amount', 0):.2f}
│
│    谢谢惠顾！
└──────────────────────┘
        """

