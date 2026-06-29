# `core/modules/auth/connect_window.py`

> 路径：`core/modules/auth/connect_window.py` | 行数：529


---


```python
"""AI Agent 连接窗口 — 引擎舱 · 燃料加注

选择模型 = 选择燃料 | API Key = 注入密钥 | 测试 = 点火
"""
from __future__ import annotations
from typing import Any

import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QGroupBox,
    QProgressBar, QApplication, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QThread, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont, QConicalGradient
)
from core.cosmic import CosmicBackground, SPACE_VOID
from core.llm_client import ModelConfig, LLMClient, PROVIDERS
from core.dark_theme import apply_dark_theme
# ═══════════ 颜色 ═══════════
CYAN     = QColor(0, 220, 255)
ORANGE   = QColor(255, 160, 30)
GREEN    = QColor(0, 240, 100)
RED      = QColor(255, 50, 70)
PURPLE   = QColor(160, 80, 255)
GOLD     = QColor(255, 200, 60)
WHITE    = QColor(220, 235, 255)
DIM_BLUE = QColor(40, 70, 120)
CARD_BG      = "rgba(10, 16, 32, 230)"
CARD_BORDER  = "rgba(60, 110, 180, 50)"
CARD_SELECTED = "rgba(16, 28, 50, 250)"
GLOW_BORDER  = "rgba(0, 200, 255, 160)"
INPUT_STYLE = """
    QLineEdit {
        background: rgba(6, 12, 24, 230);
        color: #b0c8e0;
        border: 1px solid rgba(70, 130, 200, 45);
        border-radius: 16px;
        padding: 9px 15px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid rgba(0, 200, 255, 160);
        background: rgba(8, 16, 32, 245);
    }
    QLineEdit::placeholder {
        color: #334466;
    }
"""
COMBO_STYLE = """
    QComboBox {
        background: rgba(6, 12, 24, 230);
        color: #b0c8e0;
        border: 1px solid rgba(70, 130, 200, 45);
        border-radius: 16px;
        padding: 9px 15px;
        font-size: 13px;
        min-width: 180px;
    }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background: rgba(10, 18, 38, 245);
        color: #b0c8e0;
        border: 1px solid rgba(70, 140, 220, 60);
        selection-background-color: rgba(0, 140, 240, 35);
    }
"""
# 燃料类型 → 视觉映射
FUEL_TYPES = {
    "ollama":   {"name": "反物质核心", "icon_color": "#00cc88", "desc": "本地部署 · 数据永不离船"},
    "openai":   {"name": "恒星聚变舱", "icon_color": "#44aaff", "desc": "GPT-4o · 最强火力"},
    "deepseek": {"name": "量子谐振器", "icon_color": "#6688ff", "desc": "DeepSeek · 高性价比"},
    "claude":   {"name": "暗物质引擎", "icon_color": "#cc88ff", "desc": "Claude · 深度推理"},
    "qwen":     {"name": "引力波核心", "icon_color": "#ff8844", "desc": "通义千问 · 中文专精"},
    "custom":   {"name": "未知能源舱", "icon_color": "#889999", "desc": "兼容 OpenAI · 自由扩展"},
}
class ConnectionTestThread(QThread):
    result_ready = pyqtSignal(dict)
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
    def run(self) -> None:
        client = LLMClient(self.config)
        result = client.test_connection()
        self.result_ready.emit(result)
class EngineGlow(QWidget):
    """引擎舱背景 — 中心反应堆辉光动画"""
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._angle = 0
        self._glow_intensity = 0.3
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(40)
    def _tick(self) -> None:
        self._angle += 0.8
        self.update()
    def set_glow(self, v: float) -> None:
        self._glow_intensity = v
        self.update()
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            painter.end()
            return
        cx, cy = w // 2, h // 2
        # 外圈旋转光轮
        for i in range(3):
            r = 140 + i * 30
            alpha = int(20 + self._glow_intensity * 60) - i * 8
            g = QConicalGradient(QPointF(cx, cy), self._angle + i * 40)
            g.setColorAt(0.0, QColor(0, 200, 255, 0))
            g.setColorAt(0.3, QColor(0, 180, 255, alpha))
            g.setColorAt(0.5, QColor(0, 140, 240, alpha // 2))
            g.setColorAt(0.7, QColor(0, 180, 255, alpha))
            g.setColorAt(1.0, QColor(0, 200, 255, 0))
            pen = QPen(QBrush(g), 2.5 - i * 0.5)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r)
        # 中心反应堆辉光
        core_r = 50 + self._glow_intensity * 30
        for layer in range(5, 0, -1):
            lr = core_r + layer * 16
            alpha = int((30 + self._glow_intensity * 60) * (1 - layer * 0.15))
            g = QRadialGradient(QPointF(cx, cy), lr)
            c = QColor(0, 140 + int(self._glow_intensity * 100), 255)
            g.setColorAt(0, QColor(c.red(), c.green(), c.blue(), alpha))
            g.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), alpha // 3))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(cx, cy), lr, lr)
        painter.end()
class ConnectWindow(QMainWindow):
    """引擎舱 · 燃料加注"""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("一人公司 — 引擎舱 · 燃料加注")
        self.setMinimumSize(920, 680)
        apply_dark_theme(self)
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)
        # 引擎光效层
        self._engine = EngineGlow(self._cosmic)
        self._engine.setGeometry(0, 0, 920, 680)
        # HUD 覆盖层 — 必须是窗口直接子控件，不是 _cosmic 子控件
        # 否则 _cosmic 的 WA_TransparentForMouseEvents 会在 macOS 26.x 拦截所有鼠标事件
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 920, 680)
        self._selected_provider = "ollama"
        self._test_thread = None
        self._connected = False
        self._build_ui()
        self._select_provider("ollama")
        # 确保 HUD 在星空背景之上
        self._hud.raise_()
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._engine.setGeometry(0, 0, self.width(), self.height())
        self._hud.setGeometry(0, 0, self.width(), self.height())
    def _build_ui(self) -> None:
        self._hud.paintEvent = self._paint_hud
        root = QWidget(self._hud)
        root.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(root)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        # ── 标题 ──
        title = QLabel("引擎舱 · 燃料加注")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #ddeeff; font-size: 22px; font-weight: 900; letter-spacing: 6px; background: transparent;"
        )
        layout.addWidget(title)
        sub = QLabel("选择燃料类型并注入密钥，为 Agent 引擎提供动力")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #556677; font-size: 11px; letter-spacing: 2px; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(10)
        # ── 燃料选择卡片 ──
        card_row = QHBoxLayout()
        card_row.setSpacing(10)
        card_row.setAlignment(Qt.AlignCenter)
        self._fuel_cards = {}
        fuel_ids = ["ollama", "openai", "deepseek", "claude", "qwen", "custom"]
        for fid in fuel_ids:
            info = FUEL_TYPES[fid]
            card = QPushButton()
            card.setFixedSize(130, 80)
            card.setCursor(Qt.PointingHandCursor)
            card.clicked.connect(lambda checked, p=fid: self._select_provider(p))
            card.setText(f"{info['name']}\n{info['desc']}")
            self._fuel_cards[fid] = {"btn": card, "color": info["icon_color"]}
            card_row.addWidget(card)
        layout.addLayout(card_row)
        layout.addSpacing(8)
        # ── 配置表单 ──
        form = QWidget()
        form.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(10)
        # API Key
        self._key_widget = QWidget()
        self._key_widget.setStyleSheet("background: transparent;")
        key_row = QHBoxLayout(self._key_widget)
        key_row.setContentsMargins(0, 0, 0, 0)
        kl = QLabel("密钥")
        kl.setStyleSheet("color: #8899bb; font-size: 12px; background: transparent; min-width: 50px;")
        key_row.addWidget(kl)
        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("sk-...   (本地引擎无需密钥)")
        self._key_input.setEchoMode(QLineEdit.Password)
        self._key_input.setStyleSheet(INPUT_STYLE)
        key_row.addWidget(self._key_input, 1)
        form_layout.addWidget(self._key_widget)
        # 地址 + 模型
        am_row = QHBoxLayout()
        am_row.setSpacing(10)
        al = QLabel("服务地址")
        al.setStyleSheet("color: #8899bb; font-size: 12px; background: transparent;")
        am_row.addWidget(al)
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("http://localhost:8080")
        self._url_input.setStyleSheet(INPUT_STYLE)
        am_row.addWidget(self._url_input, 2)
        ml = QLabel("模型")
        ml.setStyleSheet("color: #8899bb; font-size: 12px; background: transparent;")
        am_row.addWidget(ml)
        self._model_input = QComboBox()
        self._model_input.setEditable(True)
        self._model_input.lineEdit().setPlaceholderText("qwen2.5:7b")
        self._model_input.setStyleSheet(INPUT_STYLE)
        am_row.addWidget(self._model_input, 2)
        self._refresh_btn = QPushButton("扫描")
        self._refresh_btn.setFixedWidth(52)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(22, 44, 90, 190);
                color: #7799bb;
                border: 1px solid rgba(70, 130, 200, 45);
                border-radius: 14px;
                padding: 6px 0;
                font-size: 11px;
            }
            QPushButton:hover { background: rgba(38, 66, 140, 230); }
        """)
        self._refresh_btn.clicked.connect(self._refresh_ollama_models)
        am_row.addWidget(self._refresh_btn)
        form_layout.addLayout(am_row)
        layout.addWidget(form)
        layout.addSpacing(10)
        # ── 点火按钮 ──
        self._ignite_btn = QPushButton("点火测试")
        self._ignite_btn.setFixedSize(220, 46)
        self._ignite_btn.setCursor(Qt.PointingHandCursor)
        self._ignite_btn.clicked.connect(self._test_connection)
        layout.addWidget(self._ignite_btn, alignment=Qt.AlignCenter)
        # 状态
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #778899; font-size: 12px; background: transparent;")
        layout.addWidget(self._status_label)
        # ── 启动引擎按钮 ──
        self._launch_btn = QPushButton("启动引擎 · 进入智能中心")
        self._launch_btn.setFixedSize(280, 52)
        self._launch_btn.setCursor(Qt.PointingHandCursor)
        self._launch_btn.setEnabled(False)
        self._launch_btn.clicked.connect(self._enter_dashboard)
        layout.addWidget(self._launch_btn, alignment=Qt.AlignCenter)
        layout.addSpacing(6)
        # ── 普通操作按钮 ──
        self._normal_btn = QPushButton("普通操作 · 无需引擎")
        self._normal_btn.setFixedSize(280, 42)
        self._normal_btn.setCursor(Qt.PointingHandCursor)
        self._normal_btn.clicked.connect(self._enter_normal_mode)
        self._normal_btn.setStyleSheet("""
            QPushButton {
                background: rgba(16, 26, 44, 160);
                color: #667788;
                border: 1px solid rgba(60, 80, 110, 50);
                border-radius: 22px;
                font-size: 13px;
                letter-spacing: 4px;
            }
            QPushButton:hover {
                background: rgba(20, 32, 52, 210);
                color: #8899aa;
                border: 1px solid rgba(80, 100, 130, 80);
            }
        """)
        layout.addWidget(self._normal_btn, alignment=Qt.AlignCenter)
        layout.addSpacing(8)
        back = QLabel("← 返回登舱口")
        back.setAlignment(Qt.AlignCenter)
        back.setStyleSheet("color: #445566; font-size: 11px; background: transparent;")
        back.setCursor(Qt.PointingHandCursor)
        back.mousePressEvent = lambda e: self._go_back()
        layout.addWidget(back)
        root.setFixedWidth(660)
        root.move((self.width() - 660) // 2, 35)
    def _card_style(self, fid: str) -> str:
        info = FUEL_TYPES[fid]
        c = info["icon_color"]
        qc = QColor(c)
        selected = fid == self._selected_provider
        border = f"1px solid {c}" if selected else "1px solid rgba(40, 70, 110, 35)"
        bg = "rgba(14, 24, 44, 240)" if selected else "rgba(8, 14, 28, 210)"
        shadow = f"rgba({qc.red()},{qc.green()},{qc.blue()},60)" if selected else "transparent"
        return f"""
            QPushButton {{
                background: {bg};
                color: {'#ddeeff' if selected else '#889999'};
                border: {border};
                border-radius: 10px;
                font-size: 12px;
                line-height: 1.5;
                padding-top: 4px;
            }}
            QPushButton:hover {{
                background: rgba(16, 26, 48, 240);
                border: 1px solid {c};
            }}
        """
    def _update_fuel_cards(self) -> None:
        for fid, data in self._fuel_cards.items():
            data["btn"].setStyleSheet(self._card_style(fid))
    def _select_provider(self, pid: str) -> None:
        self._selected_provider = pid
        self._update_fuel_cards()
        info = PROVIDERS[pid]
        fuel = FUEL_TYPES[pid]
        self._url_input.setText(info["base_url"])
        self._key_widget.setVisible(info["needs_key"])
        self._refresh_btn.setVisible(info.get("needs_model_list", False))
        defaults = {
            "ollama": "qwen2.5:7b",
            "openai": "gpt-4o-mini",
            "deepseek": "deepseek-chat",
            "claude": "claude-3-5-sonnet-20241022",
            "qwen": "qwen-plus",
            "custom": "",
        }
        self._model_input.clear()
        self._model_input.addItem(defaults.get(pid, ""))
        self._model_input.setEditText(defaults.get(pid, ""))
        self._status_label.setText(f"已选择燃料：{fuel['name']}")
        self._status_label.setStyleSheet(f"color: {fuel['icon_color']}; font-size: 12px; background: transparent;")
        self._launch_btn.setEnabled(False)
        self._launch_btn.setStyleSheet(self._launch_style(False))
        self._connected = False
        self._engine.set_glow(0.3)
    def _build_config(self) -> ModelConfig:
        info = PROVIDERS[self._selected_provider]
        return ModelConfig(
            provider=self._selected_provider,
            api_key=self._key_input.text().strip() if info["needs_key"] else "",
            base_url=self._url_input.text().strip() or info["base_url"],
            model_name=self._model_input.currentText().strip(),
        )
    def _test_connection(self) -> None:
        config = self._build_config()
        if not config.model_name:
            QMessageBox.warning(self, "配置不完整", "请输入模型名称（燃料型号）")
            return
        self._ignite_btn.setEnabled(False)
        self._status_label.setText("正在点火... 引擎预热中")
        self._status_label.setStyleSheet("color: #ffaa44; font-size: 12px; background: transparent;")
        self._engine.set_glow(0.6)
        self._test_thread = ConnectionTestThread(config)
        self._test_thread.result_ready.connect(self._on_test_result)
        self._test_thread.start()
    def _on_test_result(self, result: dict) -> None:
        self._ignite_btn.setEnabled(True)
        if result["ok"]:
            fuel = FUEL_TYPES[self._selected_provider]
            self._status_label.setText(f"点火成功！{fuel['name']} 运行正常")
            self._status_label.setStyleSheet(f"color: #00ee88; font-size: 12px; background: transparent;")
            self._launch_btn.setEnabled(True)
            self._launch_btn.setStyleSheet(self._launch_style(True))
            self._connected = True
            self._engine.set_glow(0.9)
        else:
            msg = result.get("message", "点火失败")
            self._status_label.setText(f"点火失败：{msg}")
            self._status_label.setStyleSheet("color: #ff4060; font-size: 12px; background: transparent;")
            self._launch_btn.setEnabled(False)
            self._launch_btn.setStyleSheet(self._launch_style(False))
            self._engine.set_glow(0.4)
    def _refresh_ollama_models(self) -> None:
        config = self._build_config()
        try:
            client = LLMClient(config)
            models = client.fetch_ollama_models()
            self._model_input.clear()
            if models:
                for m in models:
                    self._model_input.addItem(m, m)
                self._model_input.setCurrentIndex(0)
                self._status_label.setText(f"已扫描到 {len(models)} 个本地引擎")
                self._status_label.setStyleSheet("color: #00cc88; font-size: 12px; background: transparent;")
            else:
                self._status_label.setText("未检测到本地引擎，请确保 Ollama 正在运行")
                self._status_label.setStyleSheet("color: #ffaa44; font-size: 12px; background: transparent;")
        except Exception as e:
            self._status_label.setText(f"扫描失败: {e}")
            self._status_label.setStyleSheet("color: #ff4060; font-size: 12px; background: transparent;")
    def _launch_style(self, enabled: bool) -> str:
        if enabled:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #0088dd, stop:0.5 #0066bb, stop:1 #003377);
                    color: white;
                    border: 1px solid rgba(0, 200, 255, 140);
                    border-radius: 24px;
                    font-size: 15px;
                    font-weight: 700;
                    letter-spacing: 6px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #00aaff, stop:0.5 #0088dd, stop:1 #004499);
                }
            """
        return """
            QPushButton {
                background: rgba(16, 26, 44, 190);
                color: #445566;
                border: 1px solid rgba(30, 50, 80, 35);
                border-radius: 24px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 6px;
            }
        """
    def _enter_dashboard(self) -> None:
        config = self._build_config()
        self._save_to_iqra(config)
        from core.modules.intelligence.intelligence_window import IntelligenceWindow
        self._center = IntelligenceWindow()
        self._center.show()
        self.close()
    def _save_to_iqra(self, config: dict) -> None:
        """将 connect_window 选中的配置写入 iqra_config.json"""
        import json, os
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "iqra", "data"
        )
        os.makedirs(data_dir, exist_ok=True)
        cfg_path = os.path.join(data_dir, "iqra_config.json")
        # 读取已有配置（保留其他供应商）
        existing = {}
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception as e:
                print(f"[connect_window] 加载配置失败: {e}")
        cloud_providers = existing.get("cloud_providers", {})
        local_providers = existing.get("local_providers", {})
        provider_id = config.provider
        is_local = provider_id == "ollama"
        provider_type = "openai_compatible"
        # 构建 base_url：LLMClient 的 PROVIDERS 中 base_url + api_path 去掉末尾 /chat/completions
        info = PROVIDERS[provider_id]
        raw_base = info.get("base_url", "")
        api_path = info.get("api_path", "/v1/chat/completions")
        if api_path.endswith("/chat/completions"):
            api_prefix = api_path[:-len("/chat/completions")]
        elif api_path.endswith("/messages"):
            api_prefix = api_path[:-len("/messages")]
        else:
            api_prefix = api_path.rstrip("/")
        base_url = (raw_base.rstrip("/") + api_prefix) if api_prefix else raw_base
        provider_data = {
            "name": info["name"].replace(" (本地)", "").replace(" (云端)", ""),
            "provider_type": provider_type,
            "base_url": base_url,
            "model": config.model_name,
            "api_key": config.api_key,
        }
        if is_local:
            local_providers[provider_id] = provider_data
        else:
            cloud_providers[provider_id] = provider_data
        iqra_config = {
            "active_provider_id": provider_id,
            "active_provider_type": "local" if is_local else "cloud",
            "cloud_providers": cloud_providers,
            "local_providers": local_providers,
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(iqra_config, f, indent=2, ensure_ascii=False)
    def _enter_normal_mode(self) -> None:
        """无 AI 引擎 — 直接进入智能中心，使用规则引擎"""
        from core.modules.intelligence.intelligence_window import IntelligenceWindow
        self._center = IntelligenceWindow()
        self._center.show()
        self.close()
    def _go_back(self) -> None:
        from core.modules.auth.login_window import LoginWindow
        self._login = LoginWindow()
        self._login.show()
        self.close()
    def _paint_hud(self, event) -> None:
        """HUD 装饰覆盖"""
        # 先让 Qt 完成正常的 widget 绘制（包括子控件的绘制准备）
        QWidget.paintEvent(self._hud, event)
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()
        cx = w // 2
        top = 100
        # 引擎舱标签
        painter.setPen(QPen(QColor(40, 80, 140, 80), 1))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(cx - 120, top - 25, 240, 20),
                         Qt.AlignCenter, "ENGINE BAY · FUEL INJECTION")
        painter.end()
```
