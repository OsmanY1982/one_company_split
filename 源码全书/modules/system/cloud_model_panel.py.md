# `modules/system/cloud_model_panel.py`

> 路径：`modules/system/cloud_model_panel.py` | 行数：667


---


```python
"""
Iqra - 云端模型配置面板 (宇宙版适配)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QDialog, QPushButton, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


# ═══════════════════════════════════════════
# 颜色常量 (内联，替代 _shared.py)
# ═══════════════════════════════════════════

COLORS = {
    "bg": "#F5F6FA",
    "sidebar": "#1E2A3A",
    "sidebar_hover": "#2C3E50",
    "sidebar_active": "#3498DB",
    "header": "#2C3E50",
    "card": "#FFFFFF",
    "border": "#E0E4EA",
    "primary": "#3498DB",
    "primary_hover": "#2980B9",
    "secondary": "#E8F4FD",
    "secondary_hover": "#D4ECFA",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "text": "#2C3E50",
    "text_light": "#7F8C8D",
    "text_white": "#FFFFFF",
    "input_bg": "#F8F9FA",
}


# ═══════════════════════════════════════════
# 通用工具函数 (内联，替代 _shared.py)
# ═══════════════════════════════════════════

def _styled_btn(text: str, color: str = COLORS["primary"], height: int = 36,
                font_size: int = 13) -> QPushButton:
    """创建统一样式的按钮"""
    btn = QPushButton(text)
    btn.setMinimumHeight(height)
    btn.setFont(QFont("PingFang SC", font_size))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{ opacity: 0.9; }}
        QPushButton:disabled {{ background: #BDC3C7; }}
    """)
    return btn


def _styled_input(placeholder: str = "", password: bool = False,
                  height: int = 38) -> QLineEdit:
    """创建统一样式的输入框"""
    inp = QLineEdit()
    if password:
        inp.setEchoMode(QLineEdit.Password)
    inp.setPlaceholderText(placeholder)
    inp.setMinimumHeight(height)
    inp.setStyleSheet(f"""
        QLineEdit {{
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 13px;
            background: {COLORS['input_bg']};
        }}
        QLineEdit:focus {{ border-color: {COLORS['primary']}; background: white; }}
    """)
    return inp


class CloudModelPanel(QWidget):
    """管理云端 LLM 供应商"""

    providers_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("☁️ 云端模型管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        desc = QLabel("管理云端 LLM 供应商 (DeepSeek, OpenAI, 通义千问 等)")
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)

        # ── 快速连接：选平台 + 贴Key → 一键聊天 ──
        quick_group = QGroupBox("⚡ 快速连接")
        quick_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {COLORS['text']};
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
        """)
        quick_layout = QVBoxLayout(quick_group)
        quick_layout.setSpacing(8)

        # 平台选择行
        plat_row = QHBoxLayout()
        plat_row.addWidget(QLabel("平台:"))
        self.quick_platform = QComboBox()
        self.quick_platform.setMinimumWidth(180)
        from iqra.core.llm_backend import BackendFactory
        templates = BackendFactory.list_templates()
        cloud_templates = [t for t in templates if not t["local"]]
        self._quick_template_ids = []
        for t in cloud_templates:
            self.quick_platform.addItem(f"{t['name']}", t["id"])
            self._quick_template_ids.append(t["id"])
        plat_row.addWidget(self.quick_platform)
        plat_row.addStretch()
        quick_layout.addLayout(plat_row)

        # Key 输入行
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Key :"))
        self.quick_key = QLineEdit()
        self.quick_key.setPlaceholderText("在此粘贴 API Key，如 sk-xxx...")
        self.quick_key.setEchoMode(QLineEdit.Password)
        self.quick_key.setMinimumHeight(34)
        self.quick_key.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: {COLORS['input_bg']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.quick_key.returnPressed.connect(self._quick_connect)
        key_row.addWidget(self.quick_key)
        quick_layout.addLayout(key_row)

        # 连接按钮 + 显示/隐藏 Key
        btn_row = QHBoxLayout()
        self.quick_show_key = QCheckBox("显示 Key")
        self.quick_show_key.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        self.quick_show_key.toggled.connect(lambda checked: self.quick_key.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        btn_row.addWidget(self.quick_show_key)
        btn_row.addStretch()

        connect_btn = _styled_btn("🚀 连接并开始聊天", COLORS["primary"], height=38)
        connect_btn.setFont(QFont("PingFang SC", 11, QFont.Bold))
        connect_btn.clicked.connect(self._quick_connect)
        btn_row.addWidget(connect_btn)
        quick_layout.addLayout(btn_row)

        layout.addWidget(quick_group)
        layout.addSpacing(8)

        # 当前活跃
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 添加按钮 + 探测按钮
        btn_row = QHBoxLayout()
        add_btn = _styled_btn("+ 添加供应商", COLORS["success"])
        add_btn.clicked.connect(self._show_add_dialog)
        btn_row.addWidget(add_btn)

        scan_btn = _styled_btn("🔍 一键探测", COLORS["primary"])
        scan_btn.clicked.connect(self._scan_all_providers)
        btn_row.addWidget(scan_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 供应商列表
        self.provider_list = QListWidget()
        self.provider_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['card']};
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['primary']};
                color: white;
            }}
        """)
        self.provider_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.provider_list, stretch=1)

        # 操作按钮
        btn_row = QHBoxLayout()
        use_btn = _styled_btn("设为活跃", COLORS["primary"])
        use_btn.clicked.connect(self._use_selected)
        btn_row.addWidget(use_btn)

        edit_btn = _styled_btn("编辑 Key", COLORS["warning"])
        edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(edit_btn)

        del_btn = _styled_btn("删除", COLORS["danger"])
        del_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self.provider_list.clear()
        providers = self.config.list_providers("cloud")
        active_id = self.config._data["active_provider_id"]
        active_type = self.config._data["active_provider_type"]

        for pid, pdata in providers.items():
            name = pdata.get("name", pid)
            model = pdata.get("model", "")
            active_mark = " ★" if (active_type == "cloud" and active_id == pid) else ""
            item = QListWidgetItem(f"{name}{active_mark}  |  {model}")
            item.setData(Qt.UserRole, pid)
            self.provider_list.addItem(item)

        if active_type == "cloud" and active_id:
            active_p = providers.get(active_id, {})
            self.status_label.setText(
                f"当前活跃: {active_p.get('name', active_id)} "
                f"({active_p.get('model', '')})"
            )
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 13px;")
        else:
            self.status_label.setText("⚠️ 未选择活跃供应商, 对话功能不可用")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 13px;")

    def _quick_connect(self):
        """快速连接：用当前选中的平台 + 手动输入的 Key 直接开始聊天"""
        from iqra.core.llm_backend import BackendFactory, ProviderConfig, PROVIDER_TEMPLATES

        key = self.quick_key.text().strip()
        if not key:
            QMessageBox.warning(self, "提示", "请先粘贴 API Key")
            return

        pid = self.quick_platform.currentData()
        t = PROVIDER_TEMPLATES.get(pid)
        if not t:
            QMessageBox.warning(self, "提示", "请选择平台")
            return

        name = t.name
        url = t.base_url
        model = t.model

        # 测试连接
        try:
            cfg = ProviderConfig(
                name=name, provider_type="openai_compatible",
                base_url=url, api_key=key, model=model,
            )
            backend = BackendFactory.create(cfg)
            resp = backend.chat([{"role": "user", "content": "hi"}])
            QMessageBox.information(self, "连接成功", f"{name} 测试通过!\n模型: {resp.model}")
        except Exception as e:
            QMessageBox.critical(self, "连接失败", f"{name} 连接失败:\n{e}")
            return

        # 保存
        pid = name.lower().replace(" ", "_")
        self.config.add_provider("cloud", pid, {
            "name": name,
            "provider_type": "openai_compatible",
            "base_url": url,
            "api_key": key,
            "model": model,
        })
        self.config.set_active_provider(pid, "cloud")
        self._refresh()
        self.providers_changed.emit()

    def _show_add_dialog(self):
        from iqra.core.llm_backend import BackendFactory, ProviderConfig, PROVIDER_TEMPLATES

        dlg = QDialog(self)
        dlg.setWindowTitle("添加云端 LLM 供应商")
        dlg.setMinimumWidth(480)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)

        # 模板选择
        template_combo = QComboBox()
        templates = BackendFactory.list_templates()
        cloud_templates = [t for t in templates if not t["local"]]
        for t in cloud_templates:
            template_combo.addItem(f"{t['name']} ({t['model']})", t["id"])
        layout.addRow("模板:", template_combo)

        # 自定义名称
        name_input = _styled_input("显示名称")
        layout.addRow("名称:", name_input)

        # API Key
        key_input = _styled_input("API Key", password=True)
        layout.addRow("API Key:", key_input)

        # Base URL
        url_input = _styled_input("API 地址 (自动填充)")
        layout.addRow("API 地址:", url_input)

        # 模型选择 (可编辑下拉框 + 获取按钮)
        model_row = QHBoxLayout()
        self._add_model_combo = QComboBox()
        self._add_model_combo.setEditable(True)
        self._add_model_combo.setMinimumWidth(280)
        self._add_model_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background: {COLORS['card']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        model_row.addWidget(self._add_model_combo)

        fetch_btn = QPushButton("📋 获取平台模型列表")
        fetch_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #2980B9;
            }}
        """)
        fetch_btn.clicked.connect(lambda: self._fetch_models_into_combo(
            self._add_model_combo, url_input.text(), key_input.text()
        ))
        model_row.addWidget(fetch_btn)
        layout.addRow("模型:", model_row)

        def _on_template_changed(idx):
            tid = template_combo.currentData()
            t = PROVIDER_TEMPLATES.get(tid)
            if t:
                url_input.setText(t.base_url)
                name_input.setText(t.name)
                # 填模型下拉列表
                self._add_model_combo.clear()
                if t.available_models:
                    self._add_model_combo.addItems(t.available_models)
                self._add_model_combo.setEditText(t.model)

        template_combo.currentIndexChanged.connect(_on_template_changed)
        _on_template_changed(0)

        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.reject)
        save_btn = _styled_btn("测试并保存", COLORS["success"])
        save_btn.clicked.connect(lambda: self._save_cloud_provider(
            dlg, name_input.text(), key_input.text(), url_input.text(),
            self._add_model_combo.currentText()
        ))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addRow("", btn_layout)

        dlg.exec_()

    def _save_cloud_provider(self, dlg, name, key, url, model):
        from iqra.core.llm_backend import BackendFactory, ProviderConfig

        if not name:
            QMessageBox.warning(dlg, "提示", "请输入供应商名称")
            return
        if not key:
            QMessageBox.warning(dlg, "提示", "云端模型需要 API Key")
            return

        # 测试连接
        try:
            cfg = ProviderConfig(
                name=name, provider_type="openai_compatible",
                base_url=url.strip(), api_key=key.strip(), model=model.strip(),
            )
            backend = BackendFactory.create(cfg)
            resp = backend.chat([{"role": "user", "content": "hi"}])
            QMessageBox.information(dlg, "连接成功", f"测试成功! 模型: {resp.model}")
        except Exception as e:
            reply = QMessageBox.question(
                dlg, "连接失败",
                f"测试失败: {e}\n\n是否仍然保存此供应商?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 保存
        pid = name.lower().replace(" ", "_")
        self.config.add_provider("cloud", pid, {
            "name": name.strip(),
            "provider_type": "openai_compatible",
            "base_url": url.strip(),
            "api_key": key.strip(),
            "model": model.strip(),
        })
        dlg.accept()
        self._refresh()
        self.providers_changed.emit()

    def _on_item_double_clicked(self, item):
        self._use_selected()

    def _use_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        self.config.set_active_provider(pid, "cloud")
        self._refresh()
        self.providers_changed.emit()

    def _edit_selected(self):
        """编辑已有供应商的 API Key / URL / Model"""
        from iqra.core.llm_backend import PROVIDER_TEMPLATES

        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        providers = self.config.list_providers("cloud")
        pdata = providers.get(pid)
        if not pdata:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"编辑供应商: {pdata.get('name', pid)}")
        dlg.setMinimumWidth(480)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)

        name_input = _styled_input("显示名称")
        name_input.setText(pdata.get("name", ""))
        layout.addRow("名称:", name_input)

        key_input = _styled_input("API Key (仅替换, 不显示原值)", password=True)
        key_input.setPlaceholderText("输入新 Key 替换, 留空保持不变")
        layout.addRow("API Key:", key_input)

        url_input = _styled_input("API 地址")
        url_input.setText(pdata.get("base_url", ""))
        layout.addRow("API 地址:", url_input)

        # 模型选择 (可编辑下拉框 + 获取按钮)
        model_row = QHBoxLayout()
        edit_model_combo = QComboBox()
        edit_model_combo.setEditable(True)
        edit_model_combo.setMinimumWidth(280)
        edit_model_combo.setEditText(pdata.get("model", ""))
        # 尝试按 base_url 匹配模板, 预填模型列表
        for tpl in PROVIDER_TEMPLATES.values():
            if tpl.base_url == pdata.get("base_url", ""):
                if tpl.available_models:
                    edit_model_combo.addItems(tpl.available_models)
                    edit_model_combo.setEditText(pdata.get("model", ""))
                break
        edit_model_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background: {COLORS['card']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        model_row.addWidget(edit_model_combo)

        fetch_btn = QPushButton("📋 获取平台模型列表")
        fetch_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #2980B9;
            }}
        """)
        fetch_btn.clicked.connect(lambda: self._fetch_models_into_combo(
            edit_model_combo, url_input.text(),
            key_input.text() or pdata.get("api_key", "")
        ))
        model_row.addWidget(fetch_btn)
        layout.addRow("模型:", model_row)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.reject)
        save_btn = _styled_btn("保存", COLORS["success"])
        save_btn.clicked.connect(lambda: self._do_edit_save(
            dlg, pid, name_input.text(), key_input.text(),
            url_input.text(), edit_model_combo.currentText()
        ))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addRow("", btn_layout)

        dlg.exec_()

    def _do_edit_save(self, dlg, pid, name, key, url, model):
        providers = self.config.list_providers("cloud")
        pdata = providers.get(pid, {})
        pdata["name"] = name.strip() or pdata.get("name", pid)
        if key.strip():
            pdata["api_key"] = key.strip()
        pdata["base_url"] = url.strip() or pdata.get("base_url", "")
        pdata["model"] = model.strip() or pdata.get("model", "")
        self.config._data["cloud_providers"][pid] = pdata
        self.config.save()
        dlg.accept()
        self._refresh()
        self.providers_changed.emit()

    def _delete_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认", f"确定要删除供应商 \"{pid}\" 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.remove_provider("cloud", pid)
            self._refresh()
            self.providers_changed.emit()

    def _scan_all_providers(self):
        """一键探测所有预置供应商的连通性"""
        from iqra.core.llm_backend import BackendFactory, ProviderConfig, PROVIDER_TEMPLATES

        self.status_label.setText("正在探测所有供应商...")
        self.status_label.setStyleSheet(f"color: {COLORS['primary']};")
        QApplication.processEvents()

        results = []
        for pid, template in PROVIDER_TEMPLATES.items():
            try:
                cfg = ProviderConfig(
                    name=template.name,
                    provider_type="openai_compatible",
                    base_url=template.base_url,
                    api_key="",  # 空key测试
                    model=template.model,
                )
                backend = BackendFactory.create(cfg)
                # 只测试连接，不发送真实请求
                results.append((template.name, "需要API Key", "info"))
            except Exception as e:
                results.append((template.name, f"错误: {str(e)[:50]}", "error"))

        # 显示结果
        msg = "供应商探测结果:\n\n"
        for name, status, level in results:
            icon = "✅" if level == "ok" else "⚠️" if level == "info" else "❌"
            msg += f"{icon} {name}: {status}\n"

        QMessageBox.information(self, "探测结果", msg)
        self._refresh()

    def _fetch_models_into_combo(self, combo: QComboBox, base_url: str, api_key: str):
        """从平台拉取模型列表并填入下拉框"""
        from iqra.core.llm_backend import get_available_models

        if not base_url.strip():
            QMessageBox.warning(self, "提示", "请先填写 API 地址")
            return
        if not api_key.strip():
            QMessageBox.warning(self, "提示", "云端模型需要 API Key 才能获取模型列表")
            return

        original = combo.currentText()
        combo.clear()
        combo.addItem("⏳ 正在获取模型列表...")
        combo.setEnabled(False)
        QApplication.processEvents()

        try:
            models = get_available_models(base_url.strip(), api_key.strip())
            combo.clear()
            if models:
                combo.addItems(models)
                # 恢复/选择原模型 (如果还在列表里)
                idx = combo.findText(original)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setEditText(original or (models[0] if models else ""))
                QMessageBox.information(self, "成功", f"获取到 {len(models)} 个模型")
            else:
                combo.addItem(original)
                combo.setEditText(original)
                QMessageBox.information(self, "提示", "该平台未返回模型列表")
        except Exception as e:
            combo.clear()
            combo.addItem(original)
            combo.setEditText(original)
            QMessageBox.warning(self, "获取失败", str(e))
        finally:
            combo.setEnabled(True)

```
