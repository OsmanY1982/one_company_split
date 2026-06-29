# `iqra/modules/auth/upgrade_window.py`

> 路径：`iqra/modules/auth/upgrade_window.py` | 行数：768


---


```python
# -*- coding: utf-8 -*-
from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
import sys
import os
import json
import random
import string
import csv
import hashlib
import subprocess
import uuid
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QWidget,
    QMessageBox, QLineEdit, QApplication, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPixmap, QImage
import ctypes

# 深空金属风主题
from core.dark_tool_theme import (
    DARK_BG, DARK_SURFACE, DARK_TEXT, DARK_TEXT_MUTED,
    DARK_INPUT_STYLE, DARK_BTN_PRIMARY, DANGER_RED,
)

# --------------------------
# 路径配置（彻底修复中文路径问题）
# --------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_abs_path(relative_path):
    """获取绝对路径（全平台兼容，解决中文/特殊字符路径）"""
    try:
        abs_path = os.path.join(BASE_DIR, relative_path)
        abs_path = os.path.normpath(abs_path)
        abs_path = os.path.abspath(abs_path)
        if isinstance(abs_path, bytes):
            abs_path = abs_path.decode('utf-8')
        return abs_path
    except Exception as e:
        print(f"路径处理错误：{e}")
        return relative_path

# 收款码路径
QR_WECHAT_49 = get_abs_path("wechat_49.png")
QR_ALIPAY_49 = get_abs_path("alipay_49.png")
QR_WECHAT_99 = get_abs_path("wechat_99.png")
QR_ALIPAY_99 = get_abs_path("alipay_99.png")

PAY_LOG = get_abs_path("payments.csv")
USER_PRO_FILE = get_abs_path(os.path.join("config", "user_pro.json"))

# --------------------------
# 核心修改：生成固定32位十六进制机器码（Windows专属）
# --------------------------
def get_fixed_machine_code():
    """
    生成基于硬件的固定32位机器码（格式：25E2F3C83577C30C77197CDF857B08B0）
    基于：硬盘序列号 + 主板序列号 + CPU标识 → MD5加密 → 32位大写十六进制
    """
    try:
        hardware_info = []
        
        # 1. 获取硬盘序列号（优先系统盘）
        try:
            # Windows cmd命令获取硬盘序列号
            cmd = 'wmic diskdrive get serialnumber /format:value'
            result = subprocess.check_output(
                cmd, shell=True, encoding='gbk', errors='ignore'
            ).strip()
            for line in result.split('\n'):
                if line.startswith('SerialNumber=') and line.strip() != 'SerialNumber=':
                    hardware_info.append(line.split('=')[1].strip())
                    break
        except Exception as e:
            print(f"获取硬盘序列号失败：{e}")
        
        # 2. 获取主板序列号
        try:
            cmd = 'wmic baseboard get serialnumber /format:value'
            result = subprocess.check_output(
                cmd, shell=True, encoding='gbk', errors='ignore'
            ).strip()
            for line in result.split('\n'):
                if line.startswith('SerialNumber=') and line.strip() != 'SerialNumber=':
                    hardware_info.append(line.split('=')[1].strip())
                    break
        except Exception as e:
            print(f"获取主板序列号失败：{e}")
        
        # 3. 获取CPU标识
        try:
            cmd = 'wmic cpu get processorid /format:value'
            result = subprocess.check_output(
                cmd, shell=True, encoding='gbk', errors='ignore'
            ).strip()
            for line in result.split('\n'):
                if line.startswith('ProcessorId=') and line.strip() != 'ProcessorId=':
                    hardware_info.append(line.split('=')[1].strip())
                    break
        except Exception as e:
            print(f"获取CPU标识失败：{e}")
        
        # 4. 兜底：如果硬件信息获取失败，用网卡MAC地址
        if not hardware_info:
            mac = hex(uuid.getnode()).replace('0x', '').zfill(12)
            hardware_info.append(mac)
        
        # 5. 拼接硬件信息并生成32位MD5（固定格式）
        combined = '|'.join(hardware_info)
        # MD5加密 → 32位十六进制大写字符串（和你要的格式完全一致）
        machine_code = hashlib.md5(combined.encode('utf-8')).hexdigest().upper()
        
        print(f"✅ 生成固定机器码：{machine_code}")
        return machine_code
    
    except Exception as e:
        # 终极兜底：生成固定格式的随机码（仅当硬件查询全失败时）
        print(f"硬件信息获取失败，生成兜底固定码：{e}")
        random_bytes = os.urandom(16)  # 16字节 → 32位十六进制
        machine_code = random_bytes.hex().upper()
        return machine_code

# --------------------------
# 工具函数（原逻辑不变）
# --------------------------
def _generate_random_suffix(length=8):
    """生成随机激活码后缀（8位字母+数字，确保唯一性）"""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choice(chars) for _ in range(length))
    while suffix in _get_all_generated_suffixes():
        suffix = ''.join(random.choice(chars) for _ in range(length))
    return suffix

def _get_all_generated_suffixes():
    """获取已生成的激活码后缀，避免重复"""
    suffixes = []
    if not os.path.exists(PAY_LOG):
        return suffixes
    try:
        with open(PAY_LOG, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "," in line:
                    parts = line.split(",")
                    if len(parts) >=3 and "-" in parts[2]:
                        suffix = parts[2].split("-")[-2] + parts[2].split("-")[-1]
                        suffixes.append(suffix)
    except Exception:
        pass
    return suffixes

def _save_user_pro_status(username, vip_type="PRO"):
    """核心：自动写入会员状态"""
    if not username:
        print("❌ 用户名不能为空")
        return False
        
    try:
        config_dir = os.path.dirname(USER_PRO_FILE)
        os.makedirs(config_dir, exist_ok=True)
        
        data = {}
        if os.path.exists(USER_PRO_FILE):
            try:
                with open(USER_PRO_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                    else:
                        data = {}
            except json.JSONDecodeError:
                print("⚠️ 用户配置文件格式错误，将重建")
                data = {}
            except PermissionError:
                print(f"❌ 无权限读取配置文件：{USER_PRO_FILE}")
                return False
            except Exception as e:
                print(f"读取用户配置失败：{e}")
                data = {}
        
        data[username] = vip_type
        
        temp_file = USER_PRO_FILE + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if os.path.exists(USER_PRO_FILE):
                os.remove(USER_PRO_FILE)
            os.rename(temp_file, USER_PRO_FILE)
        except PermissionError:
            print(f"❌ 无权限写入配置文件：{USER_PRO_FILE}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
        except Exception as e:
            print(f"❌ 写入临时文件失败：{e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
        
        print(f"✅ 已写入会员状态：{username} - {vip_type}")
        return True
    except Exception as e:
        print(f"❌ 写入会员状态失败：{e}")
        return False

def _is_code_used(code):
    """检查激活码是否已使用"""
    if not os.path.exists(USER_PRO_FILE):
        return False
    try:
        with open(USER_PRO_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return False
            data = json.loads(content)
            for user, vip_type in data.items():
                if code in str(user) or code in str(vip_type):
                    return True
        return False
    except Exception:
        return False

# --------------------------
# 核心窗口类（使用固定机器码）
# --------------------------
class UpgradeWindow(QDialog):
    def __init__(self, username="123", parent=None, role="user", membership="trial", expire_at=None):
        super().__init__(parent)
        self.username = username.strip() if username else "default_user"
        self._role = role
        self._membership = membership
        self._expire_at = expire_at
        # 统一使用 license_service 的机器码，与激活系统保持一致
        try:
            from modules.account.license_local import get_machine_code
            self.machine_code = get_machine_code()
        except Exception:
            self.machine_code = get_fixed_machine_code()
        self.setWindowTitle("升级会员")
        self.setModal(True)
        self.setMinimumSize(960, 700)
        self.setStyleSheet(f"""
            * {{ background-color: {DARK_BG}; }}
            QDialog {{ background-color: {DARK_BG}; }}
            QLabel {{ color: {DARK_TEXT}; background: transparent; }}
            QGroupBox {{
                border: 1px solid rgba(80,120,180,40); border-radius: 10px;
                font-family: PingFang SC, Arial; font-size: 14px; font-weight: bold;
                background-color: {DARK_SURFACE}; color: {DARK_TEXT};
                margin-top: 10px; padding: 15px;
            }}
            QGroupBox::title {{ color: {DARK_TEXT}; subcontrol-origin: margin; left: 15px; padding: 0 5px; }}
            QPushButton {{
                background: {DARK_BTN_PRIMARY}; color: white; border: none;
                border-radius: 8px; font-family: PingFang SC, Arial; font-size: 13px; padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #205090; }}
            QPushButton#maxBtn {{ background-color: #48bb78; }}
            QPushButton#maxBtn:hover {{ background-color: #38a169; }}
            QPushButton#activateBtn {{ background-color: #28a745; }}
            QPushButton#activateBtn:hover {{ background-color: #218838; }}
            QPushButton#dangerBtn {{ background-color: {DANGER_RED}; }}
            QPushButton#dangerBtn:hover {{ background-color: #cc2222; }}
            QLineEdit {{ {DARK_INPUT_STYLE} }}
        """)
        self._build_ui()

    def _build_ui(self):
        """构建UI界面（包裹 QScrollArea 适配低分辨率屏幕）"""
        # 滚动容器 — 解决低分辨率屏幕物理装不下窗口的问题
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.max_btn = QPushButton("🖥️ 最大化窗口")
        self.max_btn.setObjectName("maxBtn")
        self.max_btn.clicked.connect(self.showMaximized)
        top_layout.addWidget(self.max_btn)
        
        header = QLabel("⭐ 升级会员 ⭐")
        header.setFont(QFont("PingFang SC", 22, QFont.Bold))
        header.setStyleSheet("color: #2E86AB;")
        top_layout.addWidget(header, alignment=Qt.AlignCenter)
        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        user_label = QLabel(f"当前用户：{self.username}")
        user_label.setFont(QFont("PingFang SC", 14, QFont.Bold))
        user_label.setStyleSheet("color:red; background:#fff; border-radius:8px; padding:10px;")
        user_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(user_label)

        # 会员状态行
        status_text = f"当前会员：{self._membership}"
        if self._expire_at:
            status_text += f"  |  到期：{self._expire_at}"
        status_label = QLabel(status_text)
        status_label.setFont(QFont("PingFang SC", 12))
        status_label.setStyleSheet("color:#495057; background:#e9ecef; border-radius:8px; padding:8px;")
        status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(status_label)

        tip = QLabel(f"⚠️ 付款时请备注用户名【{self.username}】，否则无法生成激活码")
        tip.setStyleSheet("color:#e53e3e; font-size:12px; font-weight:bold;")
        tip.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(tip)

        package_layout = QHBoxLayout()
        package_layout.setSpacing(30)
        
        pro_group = QGroupBox("⭐ VIP会员 — ¥49 / 年")
        pro_layout = QVBoxLayout(pro_group)
        pro_layout.setSpacing(15)
        pro_qr = QHBoxLayout()
        pro_qr.setSpacing(20)
        pro_qr.addWidget(self._create_qr(QR_WECHAT_49, "微信支付（49元）"))
        pro_qr.addWidget(self._create_qr(QR_ALIPAY_49, "支付宝支付（49元）"))
        pro_layout.addLayout(pro_qr)
        pro_layout.addWidget(QLabel("💡 扫码付款后，点击下方按钮获取机器码"))
        package_layout.addWidget(pro_group)

        vip_group = QGroupBox("👑 钻石会员 — ¥99 / 终身")
        vip_layout = QVBoxLayout(vip_group)
        vip_layout.setSpacing(15)
        vip_qr = QHBoxLayout()
        vip_qr.setSpacing(20)
        vip_qr.addWidget(self._create_qr(QR_WECHAT_99, "微信支付（99元）"))
        vip_qr.addWidget(self._create_qr(QR_ALIPAY_99, "支付宝支付（99元）"))
        vip_layout.addLayout(vip_qr)
        vip_layout.addWidget(QLabel("💡 扫码付款后，点击下方按钮获取机器码"))
        package_layout.addWidget(vip_group)
        main_layout.addLayout(package_layout)

        # ── 机器码展示区（紧凑单行，不遮挡收款码）──
        mc_row = QHBoxLayout()
        mc_row.setSpacing(10)

        mc_icon = QLabel("🔑 机器码：")
        mc_icon.setStyleSheet("color:#2b6cb0; font-size:13px; font-weight:bold; background:transparent;")
        mc_row.addWidget(mc_icon)

        self.mc_display = QLineEdit(self.machine_code)
        self.mc_display.setReadOnly(True)
        self.mc_display.setAlignment(Qt.AlignCenter)
        self.mc_display.setFixedHeight(36)
        self.mc_display.setStyleSheet("""
            QLineEdit {
                background: #f7fafc; border: 1px solid #3182ce;
                border-radius: 6px; padding: 4px 8px;
                font-family: Menlo, 'Courier New', monospace;
                font-size: 13px; font-weight: bold; color: #2b6cb0;
                letter-spacing: 1px;
            }
        """)
        mc_row.addWidget(self.mc_display, stretch=1)

        self.copy_btn = QPushButton("📋 一键复制")
        self.copy_btn.setFixedSize(100, 36)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3182ce; color: white; border: none;
                border-radius: 6px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2b6cb0; }
        """)
        self.copy_btn.clicked.connect(self._copy_machine_code)
        mc_row.addWidget(self.copy_btn)

        main_layout.addLayout(mc_row)

        self.code_label = QLabel("")
        self.code_label.setFont(QFont("PingFang SC", 14, QFont.Bold))
        self.code_label.setStyleSheet("""
            color:green; background:white; padding:10px; border-radius:8px;
            border:1px solid #e2e8f0;
        """)
        self.code_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.code_label)

        activate_group = QGroupBox("🔑 已有激活码？立即激活")
        activate_layout = QVBoxLayout(activate_group)
        
        self.activate_input = QLineEdit()
        self.activate_input.setPlaceholderText("请输入激活码（例如：PRO-XXXX-XXXX-XXXX 或 VIP-XXXX-XXXX-XXXX）")
        activate_layout.addWidget(self.activate_input)
        
        activate_btn = QPushButton("🚀 立即激活")
        activate_btn.setObjectName("activateBtn")
        activate_btn.setStyleSheet("font-weight:bold; padding:10px;")
        activate_btn.clicked.connect(self.activate_code)
        activate_layout.addWidget(activate_btn)
        
        main_layout.addWidget(activate_group)

        contact = QLabel("📞 联系管理员（如未自动生成激活码）\n微信：Osman-Y\nQQ：59435234\n邮箱：59435234@qq.com")
        contact.setFont(QFont("PingFang SC", 12))
        contact.setStyleSheet("color:#444; background:white; padding:15px; border-radius:8px;")
        contact.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(contact)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("background-color: #718096;")
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignCenter)

    def _create_qr(self, qr_path, title):
        """收款码加载"""
        w = QWidget()
        w.setFixedSize(180, 210)
        l = QVBoxLayout(w)
        l.setSpacing(10)
        l.setAlignment(Qt.AlignCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("PingFang SC", 12, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        l.addWidget(title_lbl)
        
        img_label = QLabel()
        img_label.setFixedSize(170, 170)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border:1px solid #eee; border-radius:8px;")
        
        # 调试信息
        print("\n===== 二维码加载调试 =====")
        print(f"目标路径：{qr_path}")
        print(f"文件是否存在：{os.path.exists(qr_path)}")
        if os.path.exists(qr_path):
            print(f"文件大小：{os.path.getsize(qr_path)} 字节")
            print(f"文件绝对路径：{os.path.abspath(qr_path)}")
        
        try:
            if not os.path.exists(qr_path):
                raise FileNotFoundError("文件不存在")
            
            with open(qr_path, 'rb') as f:
                img_data = f.read()
            
            if len(img_data) == 0:
                raise ValueError("文件为空/损坏")
            
            image = QImage()
            if not image.loadFromData(img_data):
                raise ValueError("图片格式不支持/解码失败")
            
            scaled_image = image.scaled(
                img_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            pixmap = QPixmap.fromImage(scaled_image)
            img_label.setPixmap(pixmap)
            
        except FileNotFoundError:
            img_label.setText(f"❌ 收款码缺失\n{os.path.basename(qr_path)}\n请确认文件存在")
            img_label.setStyleSheet("color:#ff6b6b; font-size:10px; border:1px solid #eee; border-radius:8px;")
        except PermissionError:
            img_label.setText(f"❌ 无读取权限\n{os.path.basename(qr_path)}\n请以管理员运行")
            img_label.setStyleSheet("color:#ff6b6b; font-size:10px; border:1px solid #eee; border-radius:8px;")
        except ValueError as e:
            img_label.setText(f"❌ 收款码损坏\n{str(e)}\n请更换正常图片")
            img_label.setStyleSheet("color:#ff6b6b; font-size:10px; border:1px solid #eee; border-radius:8px;")
        except Exception as e:
            img_label.setText(f"❌ 加载失败\n{str(e)[:10]}")
            img_label.setStyleSheet("color:#ff6b6b; font-size:10px; border:1px solid #eee; border-radius:8px;")
        
        l.addWidget(img_label)
        return w

    def _copy_machine_code(self):
        """一键复制机器码到剪贴板"""
        clipboard = QApplication.clipboard()
        # 复制：用户名+机器码，方便管理员直接使用
        copy_text = f"用户名：{self.username}\n机器码：{self.machine_code}"
        clipboard.setText(copy_text)
        self.copy_btn.setText("✅ 已复制！")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #48bb78; color: white; border: none;
                border-radius: 8px; font-size: 14px; font-weight: bold;
            }
        """)
        QTimer.singleShot(2000, self._reset_copy_btn)

    def _reset_copy_btn(self):
        """恢复复制按钮状态"""
        self.copy_btn.setText("📋 一键复制")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3182ce; color: white; border: none;
                border-radius: 8px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2b6cb0; }
        """)

    def show_machine_code(self):
        """显示机器码并提供复制功能"""
        self.code_label.setText(
            f"🔑 你的机器码：\n{self.machine_code}\n"
            f"📢 请将此机器码+用户名【{self.username}】发送给管理员！"
        )

        # 弹窗：显示机器码 + 一键复制
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
        dlg = QDialog(self)
        dlg.setWindowTitle("机器码")
        dlg.setFixedSize(420, 200)
        dlg.setStyleSheet("""
            QDialog { background: #1e293b; }
            QLabel { color: #e2e8f0; font-size: 13px; }
            QLineEdit { background: #0f172a; border: 1px solid #334155;
                        border-radius: 6px; padding: 8px; color: #60a5fa;
                        font-size: 14px; font-weight: bold; }
            QPushButton { background: #3b82f6; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-size: 13px; }
            QPushButton:hover { background: #60a5fa; }
            QPushButton#close { background: #334155; }
        """)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"账号：{self.username}"))
        layout.addWidget(QLabel("机器码（发给管理员以获取激活码）："))

        mc_input = QLineEdit(self.machine_code)
        mc_input.setReadOnly(True)
        layout.addWidget(mc_input)

        btn_row = QHBoxLayout()
        btn_copy = QPushButton("📋 一键复制")
        def do_copy():
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.machine_code)
            btn_copy.setText("✅ 已复制！")
            QTimer.singleShot(2000, lambda: btn_copy.setText("📋 一键复制"))
        btn_copy.clicked.connect(do_copy)
        btn_row.addWidget(btn_copy)

        btn_close = QPushButton("关闭")
        btn_close.setObjectName("close")
        btn_close.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        dlg.exec_()
        self._record_machine_code()

    def _record_machine_code(self):
        """记录固定机器码到CSV"""
        try:
            if not os.path.exists(PAY_LOG):
                with open(PAY_LOG, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["# 用户名", "固定机器码", "金额", "激活码", "生成时间"])
            
            with open(PAY_LOG, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                writer.writerow([self.username, self.machine_code, "", "", current_time])
            
            print(f"✅ 已记录固定机器码：{self.username} - {self.machine_code}")
        except Exception as e:
            print(f"记录机器码失败：{e}")
            QMessageBox.warning(self, "提示", f"记录机器码失败：{str(e)[:30]}")

    def query_activation_code(self):
        """备用：查询激活码（原逻辑）"""
        if self.username == "default_user":
            QMessageBox.warning(self, "提示", "用户名无效，请重新登录！")
            self.code_label.setText("❌ 用户名无效，请重新登录！")
            return
            
        if not os.path.exists(PAY_LOG):
            QMessageBox.warning(self, "提示", "暂无支付记录，请联系管理员确认！")
            self.code_label.setText("❌ 暂无支付记录，请联系管理员！")
            return
        
        try:
            matched = False
            activation_code = ""
            
            with open(PAY_LOG, "r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    if not row or (isinstance(row[0], str) and row[0].startswith("#")):
                        continue
                    
                    if len(row) < 2:
                        print(f"第{row_num}行记录格式错误：字段不足")
                        continue
                    
                    user = row[0].strip()
                    amount = row[1].strip()
                    
                    if user == self.username:
                        matched = True
                        suffix = _generate_random_suffix()
                        if amount == "49":
                            activation_code = f"Y49-{suffix[:4]}-{suffix[4:]}"
                            self.code_label.setText(f"🎉 年卡激活码：{activation_code}")
                            _save_user_pro_status(self.username, "PRO")
                        elif amount == "99":
                            activation_code = f"VIP9-{suffix[:4]}-{suffix[4:]}"
                            self.code_label.setText(f"🎉 终身激活码：{activation_code}")
                            _save_user_pro_status(self.username, "VIP")
                        else:
                            self.code_label.setText(f"❌ 支付金额错误（仅支持49/99元），当前金额：{amount}")
                        self._record_activation_code(user, amount, activation_code)
                        break

            if not matched:
                self.code_label.setText("❌ 未查询到你的付款记录，请核对用户名！")
                QMessageBox.warning(self, "提示", "未查询到你的付款记录，请核对用户名或联系管理员！")

        except PermissionError:
            err_msg = "无权限读取支付记录文件，请以管理员身份运行或检查文件权限！"
            QMessageBox.critical(self, "错误", err_msg)
            self.code_label.setText(f"❌ {err_msg}")
        except Exception as e:
            err_msg = f"查询失败：{str(e)}"
            QMessageBox.critical(self, "错误", err_msg)
            self.code_label.setText(f"❌ 查询出错：{str(e)[:50]}")

    def _record_activation_code(self, user, amount, code):
        """记录激活码"""
        try:
            if not os.path.exists(PAY_LOG):
                with open(PAY_LOG, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["# 用户名", "金额", "激活码", "生成时间"])
            
            with open(PAY_LOG, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                writer.writerow([user, amount, code, current_time])
        except Exception as e:
            print(f"记录激活码失败：{e}")
            QMessageBox.warning(self, "提示", f"记录激活码失败：{str(e)[:30]}")

    def activate_code(self):
        """激活码激活逻辑 — 走核心 license_service 统一流程"""
        code = self.activate_input.text().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入激活码！")
            return

        # ── 先尝试正常激活 ──
        try:
            from modules.account.license_local import activate_license, transfer_license
            ok, msg = activate_license(code, self.username)
        except Exception as e:
            QMessageBox.critical(self, "激活异常", f"激活服务出错：{str(e)}")
            return

        # ── 正常激活成功 ──
        if ok:
            self._on_activate_success(code)
            return

        # ── 如果是设备不匹配，提示用户是否迁移 ──
        if "设备不匹配" in msg or "其他设备" in msg or "已绑定其他设备" in msg:
            reply = QMessageBox.question(
                self, "检测到设备变更",
                f"{msg}\n\n"
                f"💡 检测到您的激活码绑定了其他设备。\n"
                f"如果这是您本人的账号，可以迁移到当前设备。\n\n"
                f"⚠️ 迁移后，旧设备上的会员将失效。\n\n"
                f"是否迁移到当前设备？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    ok2, msg2 = transfer_license(code, self.username)
                except Exception as e:
                    QMessageBox.critical(self, "迁移异常", f"迁移服务出错：{str(e)}")
                    return
                if ok2:
                    self._on_activate_success(code, migrated=True)
                else:
                    QMessageBox.warning(self, "迁移失败", msg2)
            return

        # ── 其他错误 ──
        if "已被账号" in msg:
            detail = f"{msg}\n\n💡 每个激活码只能绑定一个账号，请联系管理员获取新激活码"
        elif "格式不正确" in msg or "无效" in msg:
            detail = f"{msg}\n\n💡 支持的格式：\n  PRO-XXXX-XXXX-XXXX（VIP会员）\n  VIP-XXXX-XXXX-XXXX（钻石会员）\n  TRIAL-XXXX-XXXX-XXXX（体验会员）"
        else:
            detail = msg
        QMessageBox.warning(self, "激活失败", detail)

    def _on_activate_success(self, code, migrated=False):
        """激活/迁移成功后的统一处理"""
        # ── 同步更新中央数据库 ──
        try:
            from core.data_sync import DataSync
            from modules.account.license_local import validate_license
            lic = validate_license(self.username)
            DataSync.record_user_login(self.username, "user", lic.get("type"))
            DataSync.record_membership(self.username, lic.get("type"), code)
        except Exception as e:
            print(f"[upgrade] sync failed: {e}")

        # ── 同步到云端 ──
        try:
            from core.supabase_client import CloudActivation, CloudLog
            from modules.account.license_local import _normalize
            CloudActivation.verify(_normalize(code), self.username)
            action = "self_transfer" if migrated else "self_activate"
            username=self.username,
            CloudLog.log(
                username=self.username,
                machine_code=self.machine_code,
                activation_code=code,

                action=action,

                result="SUCCESS",

                detail=f"{'设备迁移' if migrated else '用户自助激活'}，账号：{self.username}"

            )
        except Exception as e:
            print(f"[upgrade] cloud sync failed: {e}")

        # ── 界面反馈 ──
        prefix = "🎉 设备迁移成功！" if migrated else "🎉 激活成功！"
        QMessageBox.information(self, prefix,
            f"用户【{self.username}】\n已{'迁移到当前设备' if migrated else '激活成功'}\n\n请重新登录以刷新会员状态")
        self.activate_input.clear()
        self.code_label.setText(f"✅ 已{'迁移' if migrated else '激活'}：{code}")
        QTimer.singleShot(1000, self.close)

# --------------------------
# 测试入口
# --------------------------
if __name__ == "__main__":
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
    
    app = QApplication(sys.argv)
    font = QFont()
    if sys.platform == "win32":
        font.setFamily("PingFang SC")
    elif sys.platform == "darwin":
        font.setFamily("PingFang SC")
    else:
        font.setFamily("WenQuanYi Micro Hei")
    font.setPointSize(9)
    app.setFont(font)
    
    win = UpgradeWindow("test_user")
    win.show()
    sys.exit(app.exec_())
```
