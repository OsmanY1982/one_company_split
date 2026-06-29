"""
USB扫码枪支持模块

功能：
- 监听USB扫码枪输入（模拟键盘输入）
- 支持多种条码格式
- 防抖处理（避免重复扫描）
- 事件回调机制
- 与订单系统集成

使用方法：
    scanner = USBScanner()
    scanner.on_scan = lambda code, type: print(f"扫描: {code}")
    scanner.start()
"""

import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum


class BarcodeType(Enum):
    """条码类型"""
    UNKNOWN = "unknown"
    QR_CODE = "qr_code"
    CODE_128 = "code_128"
    CODE_39 = "code_39"
    EAN_13 = "ean_13"
    EAN_8 = "ean_8"
    UPC_A = "upc_a"
    UPC_E = "upc_e"


@dataclass
class ScanEvent:
    """扫描事件"""
    code: str
    barcode_type: BarcodeType
    timestamp: float
    raw_data: Optional[str] = None


class USBScanner:
    """
    USB扫码枪监听器
    
    扫码枪通常模拟键盘输入，以回车键结束。
    本类通过监听键盘输入来捕获扫码内容。
    """
    
    def __init__(self, 
                 debounce_seconds: float = 0.5,
                 buffer_timeout: float = 0.1):
        """
        初始化扫码枪监听器
        
        Args:
            debounce_seconds: 防抖时间，同一内容在此时间内不重复触发
            buffer_timeout: 字符缓冲超时，超过此时间未收到新字符则清空缓冲
        """
        self.debounce_seconds = debounce_seconds
        self.buffer_timeout = buffer_timeout
        
        self._buffer = ""
        self._last_char_time = 0.0
        self._last_scan_time = 0.0
        self._last_code = ""
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.on_scan: Optional[Callable[[ScanEvent], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # 监听钩子（用于GUI集成）
        self._hook_id = None
        
    def start(self):
        """开始监听扫码枪输入"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """停止监听"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            
    def _listen_loop(self):
        """监听循环（在独立线程中运行）"""
        try:
            # 使用keyboard库监听全局键盘事件
            import keyboard
            
            def on_key(event):
                if not self._running:
                    return
                    
                current_time = time.time()
                
                # 检查是否是回车键（扫码结束标记）
                if event.name == 'enter':
                    if self._buffer:
                        self._process_scan(self._buffer)
                        self._buffer = ""
                    return
                    
                # 检查是否是有效字符
                if event.name and len(event.name) == 1:
                    # 检查超时，如果超时则清空缓冲
                    if current_time - self._last_char_time > self.buffer_timeout:
                        self._buffer = ""
                        
                    self._buffer += event.name
                    self._last_char_time = current_time
                    
            # 注册全局键盘钩子
            keyboard.on_press(on_key)
            
            # 保持线程运行
            while self._running:
                time.sleep(0.1)
                
            # 取消键盘钩子
            keyboard.unhook_all()
            
        except ImportError:
            error = ImportError(
                "需要安装keyboard库: pip install keyboard"
            )
            if self.on_error:
                self.on_error(error)
            else:
                raise error
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            else:
                raise
                
    def _process_scan(self, code: str):
        """处理扫描到的条码"""
        current_time = time.time()
        
        # 防抖检查
        if (code == self._last_code and 
            current_time - self._last_scan_time < self.debounce_seconds):
            return
            
        self._last_code = code
        self._last_scan_time = current_time
        
        # 检测条码类型
        barcode_type = self._detect_barcode_type(code)
        
        # 创建事件
        event = ScanEvent(
            code=code,
            barcode_type=barcode_type,
            timestamp=current_time,
            raw_data=code
        )
        
        # 触发回调
        if self.on_scan:
            self.on_scan(event)
            
    def _detect_barcode_type(self, code: str) -> BarcodeType:
        """检测条码类型"""
        if not code:
            return BarcodeType.UNKNOWN
            
        # 二维码通常以特定格式开头或包含特定字符
        if code.startswith('http') or code.startswith('QR:'):
            return BarcodeType.QR_CODE
            
        # EAN-13: 13位数字
        if len(code) == 13 and code.isdigit():
            return BarcodeType.EAN_13
            
        # EAN-8: 8位数字
        if len(code) == 8 and code.isdigit():
            return BarcodeType.EAN_8
            
        # UPC-A: 12位数字
        if len(code) == 12 and code.isdigit():
            return BarcodeType.UPC_A
            
        # Code 128: 通常包含字母和数字
        if code.isalnum() and len(code) > 6:
            return BarcodeType.CODE_128
            
        # Code 39: 通常包含数字、大写字母和特定符号
        if all(c.isdigit() or c.isupper() or c in '-.$/+% ' for c in code):
            return BarcodeType.CODE_39
            
        return BarcodeType.UNKNOWN
        
    def simulate_scan(self, code: str):
        """
        模拟扫描（用于测试）
        
        Args:
            code: 要模拟扫描的条码内容
        """
        self._process_scan(code)


class ScanBuffer:
    """
    扫码缓冲器
    
    用于集成到现有GUI框架中，通过接收按键事件来组装扫码内容。
    """
    
    def __init__(self, 
                 on_scan: Callable[[ScanEvent], None],
                 debounce_seconds: float = 0.5):
        """
        初始化缓冲器
        
        Args:
            on_scan: 扫描完成回调
            debounce_seconds: 防抖时间
        """
        self.on_scan = on_scan
        self.debounce_seconds = debounce_seconds
        
        self._buffer = ""
        self._last_char_time = 0.0
        self._last_scan_time = 0.0
        self._last_code = ""
        
    def on_key_press(self, key: str):
        """
        接收按键事件
        
        在GUI的keyPressEvent中调用此方法
        
        Args:
            key: 按下的键值
        """
        current_time = time.time()
        
        # 检查是否是回车键
        if key in ('\r', '\n', 'Return', 'Enter'):
            if self._buffer:
                self._finish_scan()
            return
            
        # 检查超时
        if current_time - self._last_char_time > 0.1:
            self._buffer = ""
            
        # 添加字符到缓冲
        if len(key) == 1:
            self._buffer += key
            self._last_char_time = current_time
            
    def _finish_scan(self):
        """完成扫描"""
        code = self._buffer
        self._buffer = ""
        
        current_time = time.time()
        
        # 防抖
        if (code == self._last_code and 
            current_time - self._last_scan_time < self.debounce_seconds):
            return
            
        self._last_code = code
        self._last_scan_time = current_time
        
        # 创建事件并回调
        event = ScanEvent(
            code=code,
            barcode_type=BarcodeType.UNKNOWN,
            timestamp=current_time,
            raw_data=code
        )
        
        self.on_scan(event)
        
    def clear(self):
        """清空缓冲"""
        self._buffer = ""
        self._last_char_time = 0.0


# 便捷函数
def create_scanner(on_scan: Callable[[ScanEvent], None]) -> USBScanner:
    """
    快速创建扫码枪监听器
    
    Args:
        on_scan: 扫描回调函数
        
    Returns:
        USBScanner实例
    """
    scanner = USBScanner()
    scanner.on_scan = on_scan
    return scanner
