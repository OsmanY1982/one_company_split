"""
基础信息 · ENGINEERING DECK
QDialog：公司信息配置表单，金属灰主题
"""
import traceback
import os, json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFormLayout,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(14,16,20,245), stop:1 rgba(20,23,28,245));
        border: 2px solid rgba(130,145,165,50);
        border-radius: 14px;
    }
"""
INPUT_STYLE = """
    QLineEdit {
        background: rgba(16,18,22,230); color: #aabbcc;
        border: 1px solid rgba(130,145,165,35); border-radius: 6px;
        padding: 8px 12px; font-size: 12px; min-width: 280px;
    }
    QLineEdit:focus { border: 1px solid rgba(160,175,195,180); }
    QLineEdit::placeholder { color: #445566; }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(130,145,165,40); color: #ccddee;
        border: 1px solid rgba(150,165,185,60); border-radius: 16px;
        padding: 8px 24px; font-size: 12px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(150,165,185,70); }
"""
GROUP_STYLE = """
    QGroupBox {
        color: #889999; font-weight: 700; font-size: 13px;
        border: 1px solid rgba(130,145,165,35); border-radius: 10px;
        margin-top: 12px; padding-top: 18px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
    QLabel { color: #889999; font-size: 12px; background: transparent; }
"""


class BaseInfoWindow(QDialog):
    """基础信息配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("基础信息 · ENGINEERING DECK")
        self.setMinimumSize(560, 520)
        self.setStyleSheet(QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("基础信息 · ENGINEERING DECK")
        title.setStyleSheet("color: #aabbcc; font-size: 16px; font-weight: 800; letter-spacing: 3px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        grp = QGroupBox("公司信息")
        grp.setStyleSheet(GROUP_STYLE)
        fl = QFormLayout(grp)
        fl.setSpacing(10)
        fl.setContentsMargins(20, 20, 20, 16)

        self.edit_company = QLineEdit()
        self.edit_company.setPlaceholderText("公司名称")
        self.edit_contact = QLineEdit()
        self.edit_contact.setPlaceholderText("联系人")
        self.edit_phone = QLineEdit()
        self.edit_phone.setPlaceholderText("联系电话")
        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("邮箱")
        self.edit_address = QLineEdit()
        self.edit_address.setPlaceholderText("地址")
        self.edit_tax_id = QLineEdit()
        self.edit_tax_id.setPlaceholderText("税号")
        self.edit_bank = QLineEdit()
        self.edit_bank.setPlaceholderText("开户行")
        self.edit_bank_acc = QLineEdit()
        self.edit_bank_acc.setPlaceholderText("银行账号")

        for w in [self.edit_company, self.edit_contact, self.edit_phone,
                   self.edit_email, self.edit_address, self.edit_tax_id,
                   self.edit_bank, self.edit_bank_acc]:
            w.setStyleSheet(INPUT_STYLE)

        fl.addRow("公司名称:", self.edit_company)
        fl.addRow("联系人:", self.edit_contact)
        fl.addRow("联系电话:", self.edit_phone)
        fl.addRow("邮箱:", self.edit_email)
        fl.addRow("地址:", self.edit_address)
        fl.addRow("税号:", self.edit_tax_id)
        fl.addRow("开户行:", self.edit_bank)
        fl.addRow("银行账号:", self.edit_bank_acc)
        layout.addWidget(grp)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save = QPushButton("保存")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)
        layout.addStretch()

    def _load(self):
        info_file = os.path.join(DATA_DIR, "company_info.json")
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                return  # 文件损坏，静默跳过
            self.edit_company.setText(data.get("company_name", ""))
            self.edit_contact.setText(data.get("contact", ""))
            self.edit_phone.setText(data.get("phone", ""))
            self.edit_email.setText(data.get("email", ""))
            self.edit_address.setText(data.get("address", ""))
            self.edit_tax_id.setText(data.get("tax_id", ""))
            self.edit_bank.setText(data.get("bank", ""))
            self.edit_bank_acc.setText(data.get("bank_account", ""))

    def _save(self):
        info_file = os.path.join(DATA_DIR, "company_info.json")
        data = {
            "company_name": self.edit_company.text().strip(),
            "contact": self.edit_contact.text().strip(),
            "phone": self.edit_phone.text().strip(),
            "email": self.edit_email.text().strip(),
            "address": self.edit_address.text().strip(),
            "tax_id": self.edit_tax_id.text().strip(),
            "bank": self.edit_bank.text().strip(),
            "bank_account": self.edit_bank_acc.text().strip(),
        }
        os.makedirs(os.path.dirname(info_file), exist_ok=True)
        tmp_path = info_file + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, info_file)  # 原子替换
        self._log_op("基础信息", "保存", "公司信息已更新")
        QMessageBox.information(self, "提示", "基础信息已保存")

    def _log_op(self, module, action, detail):
        try:
            import sqlite3
            db = os.path.join(DATA_DIR, "system_logs.db")
            conn = sqlite3.connect(db)
            conn.execute("INSERT INTO op_logs(module, action, detail) VALUES(?,?,?)",
                         (module, action, detail))
            conn.commit(); conn.close()
        except Exception:
            traceback.print_exc()
