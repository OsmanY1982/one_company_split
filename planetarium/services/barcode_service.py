"""
条码服务
支持多种条码类型生成和识别
"""

import os
from typing import Dict, List, Optional
from io import BytesIO


class BarcodeService:
    """条码服务"""

    def __init__(self):
        self._output_dir = "barcodes"
        os.makedirs(self._output_dir, exist_ok=True)

    def generate_barcode(self,
                         data: str,
                         barcode_type: str = "code128",
                         output_path: Optional[str] = None) -> Dict:
        """生成条形码"""
        try:
            import barcode
            from barcode.writer import ImageWriter

            barcode_class = barcode.get_barcode_class(barcode_type)

            if not output_path:
                output_path = os.path.join(self._output_dir, f"{data}_{barcode_type}")

            barcode_obj = barcode_class(data, writer=ImageWriter())
            barcode_obj.save(output_path)

            return {
                "success": True,
                "file_path": f"{output_path}.png",
                "barcode_type": barcode_type,
                "data": data,
            }
        except ImportError:
            return {"success": False, "message": "请安装 python-barcode 库"}
        except Exception as e:
            return {"success": False, "message": f"生成条码失败: {e}"}

    def generate_qrcode(self,
                        data: str,
                        output_path: Optional[str] = None,
                        size: int = 10) -> Dict:
        """生成二维码"""
        try:
            import qrcode

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=size,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            if not output_path:
                output_path = os.path.join(self._output_dir, f"qr_{hash(data)}.png")

            img.save(output_path)

            return {
                "success": True,
                "file_path": output_path,
                "data": data,
            }
        except ImportError:
            return {"success": False, "message": "请安装 qrcode 库"}
        except Exception as e:
            return {"success": False, "message": f"生成二维码失败: {e}"}

    def generate_batch(self,
                       items: List[Dict],
                       barcode_type: str = "code128") -> Dict:
        """批量生成条码"""
        results = {}
        for item in items:
            data = item.get("data", "")
            label = item.get("label", "")
            result = self.generate_barcode(data, barcode_type)
            results[label or data] = result
        return {"success": True, "results": results}

