# `modules/auth/model_setup_window.py`

> 路径：`modules/auth/model_setup_window.py` | 行数：802


---


```python
"""
模型配置窗口 — 登录 → 模型配置 → 主控面板
三种模式：预设云端模型 / 自定义端点 / 本地推理

与 iqra 共享配置格式（iqra_config.json）
"""
import os, sys, json, traceback, math, random
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QCheckBox, QFrame, QApplication,
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QThread, QObject, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont,
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
from core.planet_painter import PLANET_STYLES, paint_planet
from deps.install_deps import ensure

# 模型列表统一走 AgentBridge.list_all_models() 静态方法（数据源：iqra_config.json + Ollama 动态发现）


# ── 预设供应商模板（精简版，完整版在 iqra PROVIDER_TEMPLATES）──

PRESET_PROVIDERS = [
    {"id": "deepseek",        "name": "DeepSeek",         "base_url": "https://api.deepseek.com/v1",                "model": "deepseek-chat",     "desc": "DeepSeek-V3 通用大模型，性价比极高",           "local": False, "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"id": "openai",          "name": "OpenAI",            "base_url": "https://api.openai.com/v1",                  "model": "gpt-4o",            "desc": "GPT-4o / GPT-4 / GPT-3.5 系列",              "local": False, "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"]},
    {"id": "claude",          "name": "Anthropic Claude",  "base_url": "https://api.anthropic.com/v1",               "model": "claude-sonnet-4-20250514", "desc": "Claude Sonnet 4 / Opus 4 系列",          "local": False, "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]},
    {"id": "tongyi",          "name": "通义千问 (阿里云)",   "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus",   "desc": "阿里云通义千问 Qwen 系列",                     "local": False, "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b"]},
    # ⚠️ bailian 已移除（含共享管理员 Key / MaaS 端点）
    {"id": "zhipu",           "name": "智谱 GLM",          "base_url": "https://open.bigmodel.cn/api/paas/v4",       "model": "glm-4-plus",       "desc": "智谱 GLM-4 系列",                              "local": False, "models": ["glm-4-plus", "glm-4-flash", "glm-4v-plus"]},
    {"id": "moonshot",        "name": "Moonshot (月之暗面)", "base_url": "https://api.moonshot.cn/v1",                 "model": "moonshot-v1-8k",   "desc": "月之暗面 Kimi / Moonshot",                    "local": False, "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]},
    {"id": "groq",            "name": "Groq",              "base_url": "https://api.groq.com/openai/v1",              "model": "llama-3.3-70b-versatile", "desc": "Groq LPU 高速推理",                    "local": False, "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]},
    {"id": "together",        "name": "Together AI",       "base_url": "https://api.together.xyz/v1",                 "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "desc": "Together AI 多模型托管", "local": False, "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo"]},
    {"id": "openrouter",      "name": "OpenRouter",        "base_url": "https://openrouter.ai/api/v1",                "model": "openai/gpt-4o",    "desc": "OpenRouter 多模型聚合网关",                   "local": False, "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4-20250514"]},
    {"id": "siliconflow",     "name": "SiliconFlow",       "base_url": "https://api.siliconflow.cn/v1",               "model": "deepseek-ai/DeepSeek-V3", "desc": "硅基流动 多模型推理平台",             "local": False, "models": ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]},
    {"id": "mistral",         "name": "Mistral AI",        "base_url": "https://api.mistral.ai/v1",                   "model": "mistral-large-latest", "desc": "Mistral Large / Small / Codestral",     "local": False, "models": ["mistral-large-latest", "codestral-latest"]},
    {"id": "minimax",         "name": "MiniMax (海螺AI)",   "base_url": "https://api.minimax.chat/v1",                "model": "abab6.5s-chat",    "desc": "MiniMax 海螺AI - ABAB 系列",                "local": False, "models": ["abab6.5s-chat", "abab6.5-chat"]},
    {"id": "cohere",          "name": "Cohere",            "base_url": "https://api.cohere.com/v1",                   "model": "command-r-plus",   "desc": "Cohere Command R/R+ 企业级 RAG",             "local": False, "models": ["command-r-plus", "command-r"]},
    {"id": "stepfun",         "name": "阶跃星辰 StepFun",   "base_url": "https://api.stepfun.com/v1",                  "model": "step-2-16k",       "desc": "阶跃星辰 Step 系列大模型",                   "local": False, "models": ["step-2-16k", "step-1-flash"]},
]

LOCAL_SERVICES = [
    {"id": "ollama",    "name": "Ollama",     "base_url": "http://localhost:11434/v1", "desc": "本地开源大模型运行平台，完全离线",                  "models": []},
    {"id": "lmstudio",  "name": "LM Studio",  "base_url": "http://localhost:1234/v1",  "desc": "图形界面管理模型，开箱即用",                       "models": ["local-model"]},
    {"id": "vllm",      "name": "vLLM",       "base_url": "http://localhost:8000/v1",  "desc": "高性能推理引擎，适合生产环境",                      "models": ["default"]},
    {"id": "llamacpp",  "name": "llama.cpp",  "base_url": "http://localhost:8080/v1",  "desc": "轻量 GGUF 模型推理",                              "models": ["local"]},
]

# ── 配置路径 ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "iqra", "data")
IQRA_CONFIG_PATH = os.path.join(DATA_DIR, "iqra_config.json")


def _save_iqra_config(config_dict: dict):
    """保存配置到 iqra_config.json"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IQRA_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)


def _load_iqra_config() -> dict:
    """加载已有 iqra 配置"""
    try:
        if os.path.exists(IQRA_CONFIG_PATH):
            with open(IQRA_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[model_setup_window] 加载配置失败: {e}")
    return {}


# ═══════════════════════════════════════════
# 星空绘制器（精简版，继承宇宙版视觉风格）
# ═══════════════════════════════════════════

class SetupCosmicBackground(QWidget):
    """模型配置页背景 — 深空星场 + 旋转星系"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = 0
        self._stars = []
        import random
        for _ in range(200):
            self._stars.append({
                "x": random.random(), "y": random.random(),
                "r": random.uniform(0.3, 2.0),
                "a": random.randint(30, 160),
                "speed": random.uniform(0.2, 0.8),
            })
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps (原 40ms)

    def _tick(self):
        self._t += 0.02
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(4, 6, 16))

        # 星场
        for s in self._stars:
            x = s["x"] * w
            y = (s["y"] + s["speed"] * self._t * 0.03) % 1.0 * h
            a = s["a"] + int(40 * (0.5 + 0.5 * (s["y"] % 1.0)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(180, 200, 255, a)))
            painter.drawEllipse(QPointF(x, y), s["r"], s["r"])

        # 中心星系
        cx, cy = w // 2, h // 2
        for i in range(3, 0, -1):
            r = 120 + i * 50
            a = int(6 * (4 - i))
            painter.setPen(QPen(QColor(40, 80, 180, a), 0.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r * 0.6)

        # 旋转光点 → 升级为微型真实纹理星球
        planet_styles = ["neptune", "venus", "mars", "jupiter", "mercury", "uranus", "saturn", "moon"]
        for i in range(8):
            angle = self._t * 0.3 + i * 0.785
            px = cx + math.cos(angle) * 180
            py = cy + math.sin(angle) * 180 * 0.6
            style = PLANET_STYLES.get(planet_styles[i], PLANET_STYLES["neptune"])
            paint_planet(painter, QPointF(px, py), 36, style, anim_t=self._t)

        painter.end()



# ═══════════════════════════════════════════
# 输入框样式
# ═══════════════════════════════════════════

INPUT_STYLE = """
    QLineEdit {
        background: rgba(8, 16, 32, 220);
        color: #99ccff;
        border: 1px solid rgba(60, 140, 240, 45);
        border-radius: 18px;
        padding: 10px 18px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid rgba(0, 200, 255, 160);
        background: rgba(10, 20, 40, 240);
    }
    QLineEdit::placeholder {
        color: #334466;
    }
"""

COMBO_STYLE = """
    QComboBox {
        background: rgba(8, 16, 32, 220);
        color: #99ccff;
        border: 1px solid rgba(60, 140, 240, 45);
        border-radius: 18px;
        padding: 10px 18px;
        font-size: 13px;
    }
    QComboBox:hover { border: 1px solid rgba(0, 200, 255, 140); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: rgba(10, 18, 36, 245);
        color: #99ccff;
        selection-background-color: rgba(40, 100, 200, 80);
        border: 1px solid rgba(60, 140, 240, 50);
        outline: none;
    }
"""

LABEL_STYLE = "color: #6688aa; font-size: 11px; letter-spacing: 2px; background: transparent;"

BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0055cc, stop:1 #0088ff);
        color: white; border: none; border-radius: 22px;
        padding: 10px 40px; font-size: 14px; font-weight: 700;
        letter-spacing: 4px;
    }
    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0077ee, stop:1 #00aaff); }
    QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0044aa, stop:1 #0066cc); }
"""

BTN_SECONDARY = """
    QPushButton {
        background: rgba(30, 40, 60, 200);
        color: #8899aa; border: 1px solid rgba(70, 90, 120, 50);
        border-radius: 22px; padding: 9px 32px; font-size: 13px;
        font-weight: 600; letter-spacing: 3px;
    }
    QPushButton:hover { background: rgba(40, 55, 80, 220); color: #aaccee; }
"""


# ═══════════════════════════════════════════
# ModelSetupWindow — 模型配置窗口
# ═══════════════════════════════════════════

class ModelSetupWindow(QMainWindow):
    """登录后、主控面板前的模型配置窗口"""

    setup_complete = pyqtSignal(dict)  # 发射配置字典

    def __init__(self, username: str = "", role: str = "member",
                 membership_info: dict = None):
        super().__init__()
        self._username = username
        self._role = role
        self._membership_info = membership_info or {}

        self.setWindowTitle("一人公司 — 引擎配置")
        self.setMinimumSize(820, 620)

        # 加载已有配置
        self._existing = _load_iqra_config()

        # 背景
        self._bg = SetupCosmicBackground(self)
        self.setCentralWidget(self._bg)

        # HUD 层
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 820, 620)
        self._build_ui()

        self._hud.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        if self._bg:
            self._bg.setGeometry(0, 0, self.width(), self.height())
        self._relayout()

    def _relayout(self):
        w = self._hud.width()
        card_w = 580
        self._card.setGeometry((w - card_w) // 2, 40, card_w, 520)

    def _build_ui(self):
        self._hud.paintEvent = lambda e: None  # 透明

        # 卡片容器
        self._card = QWidget(self._hud)
        self._card.setStyleSheet("""
            background: rgba(6, 12, 28, 230);
            border: 1px solid rgba(50, 100, 180, 60);
            border-radius: 16px;
        """)
        card_layout = QVBoxLayout(self._card)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("启 动 引 擎")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #aaccee; font-size: 20px; font-weight: 900; "
            "letter-spacing: 12px; background: transparent; padding: 22px 0 10px 0;"
        )
        card_layout.addWidget(title)

        sub = QLabel("选择 AI 模型提供商以激活智能中心")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446688; font-size: 11px; background: transparent; padding-bottom: 14px;")
        card_layout.addWidget(sub)

        # ── 三个 Tab ──
        self._tab_bar = QWidget()
        tab_layout = QHBoxLayout(self._tab_bar)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(40, 0, 40, 0)

        self._tab_preset = QPushButton("预设模型")
        self._tab_custom = QPushButton("自定义端点")
        self._tab_local = QPushButton("本地推理")
        self._tabs = [self._tab_preset, self._tab_custom, self._tab_local]
        for t in self._tabs:
            t.setCheckable(True)
            t.setCursor(Qt.PointingHandCursor)
            t.setFixedHeight(36)
            t.clicked.connect(lambda checked, btn=t: self._switch_tab(btn))
        self._tab_preset.setChecked(True)

        self._update_tab_styles()
        tab_layout.addWidget(self._tab_preset)
        tab_layout.addWidget(self._tab_custom)
        tab_layout.addWidget(self._tab_local)
        card_layout.addWidget(self._tab_bar)
        card_layout.addSpacing(8)

        # ── 内容栈 ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        self._stack.addWidget(self._build_preset_panel())
        self._stack.addWidget(self._build_custom_panel())
        self._stack.addWidget(self._build_local_panel())
        card_layout.addWidget(self._stack, 1)

        # ── 底部按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(40, 12, 40, 20)
        btn_row.setSpacing(16)

        skip_btn = QPushButton("跳过配置 (离线模式)")
        skip_btn.setStyleSheet(BTN_SECONDARY)
        skip_btn.setCursor(Qt.PointingHandCursor)
        skip_btn.clicked.connect(self._skip_setup)
        btn_row.addWidget(skip_btn)

        btn_row.addStretch()

        self._launch_btn = QPushButton("点 火")
        self._launch_btn.setStyleSheet(BTN_PRIMARY)
        self._launch_btn.setCursor(Qt.PointingHandCursor)
        self._launch_btn.clicked.connect(self._launch)
        btn_row.addWidget(self._launch_btn)

        card_layout.addLayout(btn_row)

        self._relayout()

    def _tab_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: rgba(20, 60, 140, 180);
                    color: #ddeeff; border: 1px solid rgba(0, 180, 255, 140);
                    border-bottom: none; border-radius: 14px 14px 0 0;
                    font-size: 12px; font-weight: 700;
                    padding: 8px 20px;
                }
            """
        return """
            QPushButton {
                background: transparent; color: #557799;
                border: 1px solid transparent;
                border-bottom: 1px solid rgba(50, 100, 180, 30);
                border-radius: 14px 14px 0 0;
                font-size: 12px; font-weight: 500;
                padding: 8px 20px;
            }
            QPushButton:hover { color: #88aacc; background: rgba(15, 30, 60, 100); }
        """

    def _update_tab_styles(self):
        for t in self._tabs:
            t.setStyleSheet(self._tab_style(t.isChecked()))

    def _switch_tab(self, btn):
        for t in self._tabs:
            t.setChecked(t == btn)
        self._update_tab_styles()
        idx = self._tabs.index(btn)
        self._stack.setCurrentIndex(idx)

    # ════════════════ 预设模式 ════════════════

    def _build_preset_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        # 提供商选择
        lbl1 = QLabel("模型提供商")
        lbl1.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl1)

        self._preset_provider = QComboBox()
        self._preset_provider.setStyleSheet(COMBO_STYLE)
        self._preset_provider.setMinimumHeight(42)
        for p in PRESET_PROVIDERS:
            icon = "🏠" if p["local"] else "☁️"
            self._preset_provider.addItem(f"{icon}  {p['name']} — {p['desc']}", p["id"])
        self._preset_provider.currentIndexChanged.connect(self._on_preset_provider_changed)
        v.addWidget(self._preset_provider)

        # 模型选择
        lbl2 = QLabel("模型")
        lbl2.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl2)

        self._preset_model = QComboBox()
        self._preset_model.setStyleSheet(COMBO_STYLE)
        self._preset_model.setEditable(True)
        self._preset_model.setMinimumHeight(42)
        v.addWidget(self._preset_model)

        # API Key
        lbl3 = QLabel("API Key")
        lbl3.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl3)

        self._preset_key = QLineEdit()
        self._preset_key.setStyleSheet(INPUT_STYLE)
        self._preset_key.setEchoMode(QLineEdit.Password)
        self._preset_key.setPlaceholderText("输入 API Key（安全存储，不外传）")
        v.addWidget(self._preset_key)

        v.addStretch()

        # 初始化第一个选项
        self._on_preset_provider_changed()
        return panel

    def _on_preset_provider_changed(self):
        idx = self._preset_provider.currentIndex()
        if idx < 0:
            return
        pid = self._preset_provider.currentData()
        provider = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
        if not provider:
            return
        self._preset_model.clear()
        for m in provider.get("models", ["default"]):
            self._preset_model.addItem(m, m)
        # 检查已有配置
        existing_key = ""
        cloud = self._existing.get("cloud_providers", {})
        if pid in cloud:
            existing_key = cloud[pid].get("api_key", "")
            existing_model = cloud[pid].get("model", "")
            idx_m = self._preset_model.findText(existing_model)
            if idx_m >= 0:
                self._preset_model.setCurrentIndex(idx_m)
            elif existing_model:
                self._preset_model.setEditText(existing_model)
        if existing_key:
            self._preset_key.setText(existing_key)

    # ════════════════ 自定义模式 ════════════════

    def _build_custom_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lines = [
            ("API Base URL", "custom_url", "https://api.example.com/v1", False),
            ("API Key", "custom_key", "sk-...", True),
            ("模型名称 (Model Name)", "custom_model", "gpt-4o", False),
        ]
        self._custom_inputs = {}
        for label_text, attr, placeholder, is_pass in lines:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(LABEL_STYLE)
            v.addWidget(lbl)

            le = QLineEdit()
            le.setStyleSheet(INPUT_STYLE)
            le.setPlaceholderText(placeholder)
            if is_pass:
                le.setEchoMode(QLineEdit.Password)
            v.addWidget(le)
            self._custom_inputs[attr] = le

        v.addStretch()

        # 预填已有配置
        existing_custom = self._existing.get("cloud_providers", {}).get("custom", {})
        if existing_custom:
            self._custom_inputs["custom_url"].setText(existing_custom.get("base_url", ""))
            self._custom_inputs["custom_key"].setText(existing_custom.get("api_key", ""))
            self._custom_inputs["custom_model"].setText(existing_custom.get("model", ""))

        return panel

    # ════════════════ 本地模式 ════════════════

    def _build_local_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lbl1 = QLabel("本地推理服务")
        lbl1.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl1)

        self._local_service = QComboBox()
        self._local_service.setStyleSheet(COMBO_STYLE)
        self._local_service.setMinimumHeight(42)
        for s in LOCAL_SERVICES:
            self._local_service.addItem(f"🖥  {s['name']} — {s['desc']}", s["id"])
        self._local_service.currentIndexChanged.connect(self._on_local_service_changed)
        v.addWidget(self._local_service)

        lbl2 = QLabel("Base URL")
        lbl2.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl2)

        self._local_url = QLineEdit()
        self._local_url.setStyleSheet(INPUT_STYLE)
        self._local_url.setPlaceholderText("自动填充")
        v.addWidget(self._local_url)

        lbl3 = QLabel("模型名称")
        lbl3.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl3)

        model_row = QHBoxLayout()
        model_row.setSpacing(8)

        self._local_model = QComboBox()
        self._local_model.setStyleSheet(COMBO_STYLE)
        self._local_model.setEditable(True)
        self._local_model.setMinimumHeight(42)
        model_row.addWidget(self._local_model, stretch=1)

        self._refresh_btn = QPushButton("刷新模型")
        self._refresh_btn.setStyleSheet(BTN_SECONDARY)
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.setFixedHeight(42)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._refresh_local_models)
        model_row.addWidget(self._refresh_btn)

        v.addLayout(model_row)

        v.addStretch()

        self._on_local_service_changed()

        # 预填已有本地配置
        local = self._existing.get("local_providers", {})
        if local:
            first_key = list(local.keys())[0] if local else None
            if first_key:
                idx = self._local_service.findData(first_key)
                if idx >= 0:
                    self._local_service.setCurrentIndex(idx)
                cfg = local[first_key]
                if cfg.get("base_url"):
                    self._local_url.setText(cfg["base_url"])
                if cfg.get("model"):
                    midx = self._local_model.findText(cfg["model"])
                    if midx >= 0:
                        self._local_model.setCurrentIndex(midx)
                    else:
                        self._local_model.setEditText(cfg["model"])

        return panel

    def _on_local_service_changed(self):
        sid = self._local_service.currentData()
        svc = next((s for s in LOCAL_SERVICES if s["id"] == sid), None)
        if not svc:
            return
        self._local_url.setText(svc["base_url"])
        self._local_model.clear()

        # 统一通过 AgentBridge.list_all_models() 获取模型列表
        if sid == "ollama":
            self._refresh_local_models()
        else:
            for m in svc.get("models", ["default"]):
                self._local_model.addItem(m, m)

    def _refresh_local_models(self):
        """通过 AgentBridge.list_all_models() + 直接扫描当前服务获取模型列表"""
        from modules.intelligence.agent_bridge import AgentBridge

        self._local_model.clear()
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("扫描中...")

        local_models = []

        # 优先直连当前选中的本地服务扫描（不依赖已保存的配置）
        sid = self._local_service.currentData()
        url = self._local_url.text().strip()
        if url and "localhost" in url:
            try:
                import urllib.request
                import urllib.parse

                if "11434" in url or sid == "ollama":
                    # Ollama 的 /api/tags 在根路径，不在 base_url 的 /v1 下
                    parsed = urllib.parse.urlparse(url)
                    origin = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 11434}"
                    endpoint = urllib.parse.urljoin(origin + "/", "api/tags")
                    resp = urllib.request.urlopen(endpoint, timeout=5)
                    data = json.loads(resp.read())
                    for m in data.get("models", []):
                        if "name" in m:
                            size = m.get("size", 0)
                            size_str = f" ({size / 1024 / 1024 / 1024:.1f}GB)" if size else ""
                            local_models.append({"model": m["name"], "size": size, "display": f"{m['name']}{size_str}"})
                else:
                    endpoint = urllib.parse.urljoin(url.rstrip("/") + "/", "models")
                    resp = urllib.request.urlopen(endpoint, timeout=5)
                    data = json.loads(resp.read())
                    for m in data.get("data", []):
                        local_models.append({"model": m["id"], "size": 0, "display": m["id"]})
            except Exception as e:
                print(f"[ModelSetup] 直接扫描 {url} 失败: {e}")

        # 补充从已保存配置中读取的模型
        if not local_models:
            try:
                all_models = AgentBridge.list_all_models()
                for m in all_models:
                    if m.get("category") == "local":
                        name = m.get("model", "")
                        size = m.get("size", 0)
                        size_str = f" ({size / 1024 / 1024 / 1024:.1f}GB)" if size else ""
                        local_models.append({"model": name, "size": size, "display": f"{name}{size_str}"})
            except Exception as e:
                print(f"[ModelSetup] agent_bridge 获取模型列表失败: {e}")
                traceback.print_exc()

        if not local_models:
            self._local_model.addItem("（暂无本地模型，请先配置或启动 Ollama）", "")
        else:
            for m in local_models:
                name = m.get("model", "")
                size = m.get("size", 0)
                size_str = f" ({size / 1024 / 1024 / 1024:.1f}GB)" if size else ""
                self._local_model.addItem(f"{name}{size_str}", name)

        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("刷新模型")

    # ════════════════ 操作 ════════════════

    def _get_config(self) -> dict:
        """根据当前选中的 tab 构建 iqra 配置字典"""
        active_tab = self._stack.currentIndex()

        config = {
            "active_provider_id": "",
            "active_provider_type": "",
            "cloud_providers": {},
            "local_providers": {},
        }

        if active_tab == 0:  # 预设模式
            pid = self._preset_provider.currentData()
            key = self._preset_key.text().strip()
            model = self._preset_model.currentText().strip() or self._preset_model.currentData() or ""
            provider = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
            if not provider:
                return None
            config["active_provider_id"] = pid
            config["active_provider_type"] = "cloud"
            config["cloud_providers"][pid] = {
                "name": provider["name"],
                "provider_type": "openai_compatible",
                "base_url": provider["base_url"],
                "api_key": key,
                "model": model,
            }

        elif active_tab == 1:  # 自定义模式
            url = self._custom_inputs["custom_url"].text().strip()
            key = self._custom_inputs["custom_key"].text().strip()
            model = self._custom_inputs["custom_model"].text().strip()
            if not url or not model:
                QMessageBox.warning(self, "参数缺失", "请填写 API Base URL 和模型名称")
                return None
            config["active_provider_id"] = "custom"
            config["active_provider_type"] = "cloud"
            config["cloud_providers"]["custom"] = {
                "name": "自定义 OpenAI 兼容",
                "provider_type": "openai_compatible",
                "base_url": url,
                "api_key": key,
                "model": model,
            }

        elif active_tab == 2:  # 本地模式
            sid = self._local_service.currentData()
            url = self._local_url.text().strip()
            model = self._local_model.currentData() or self._local_model.currentText().strip() or ""
            svc = next((s for s in LOCAL_SERVICES if s["id"] == sid), None)
            if not svc:
                return None
            config["active_provider_id"] = sid
            config["active_provider_type"] = "local"

            config["local_providers"][sid] = {
                "name": svc["name"],
                "provider_type": "openai_compatible",
                "base_url": url,
                "model": model,
                "api_key": "",
            }

        return config

    def _launch(self):
        """点火 — 保存配置并发射信号"""
        config = self._get_config()
        if config is None:
            return

        # 保存
        _save_iqra_config(config)

        # 初始化 iqra 引擎（尝试）
        engine = None
        try:
            engine = self._init_iqra_engine(config)
        except Exception as e:
            print(f"[ModelSetup] iqra engine init failed: {e}")
            traceback.print_exc()

        self.setup_complete.emit({
            "config": config,
            "engine": engine,
            "username": self._username,
            "role": self._role,
            "membership_info": self._membership_info,
        })
        self.close()

    def _skip_setup(self):
        """跳过配置 — 离线模式"""
        config = {"active_provider_id": "", "active_provider_type": "none"}
        self.setup_complete.emit({
            "config": config,
            "engine": None,
            "username": self._username,
            "role": self._role,
            "membership_info": self._membership_info,
        })
        self.close()

    def _init_iqra_engine(self, config: dict):
        """尝试初始化 iqra 引擎，失败返回 None"""
        # 添加 iqra 到 path
        # iqra 位于项目根目录下
        iqra_root = os.path.join(PROJECT_ROOT, "iqra")
        if not os.path.isdir(iqra_root):
            print(f"[ModelSetup] iqra not found at {iqra_root}")
            return None

        if iqra_root not in sys.path:
            sys.path.insert(0, os.path.dirname(iqra_root))
            sys.path.insert(0, iqra_root)

        try:
            from iqra.core.llm_backend import BackendFactory, ProviderConfig

            # iqra/core/__init__.py 会将自身路径插入 sys.path[0]，可能遮蔽 modules/
            if PROJECT_ROOT not in sys.path:
                sys.path.insert(0, PROJECT_ROOT)
            elif sys.path[0] != PROJECT_ROOT:
                sys.path.remove(PROJECT_ROOT)
                sys.path.insert(0, PROJECT_ROOT)

            provider_id = config.get("active_provider_id", "")
            provider_type = config.get("active_provider_type", "")

            if provider_type == "cloud":
                prov_cfg = config.get("cloud_providers", {}).get(provider_id, {})
            elif provider_type == "local":
                prov_cfg = config.get("local_providers", {}).get(provider_id, {})
            else:
                return None

            pc = ProviderConfig(
                name=prov_cfg.get("name", provider_id),
                provider_type=prov_cfg.get("provider_type", "openai_compatible"),
                base_url=prov_cfg.get("base_url", ""),
                api_key=prov_cfg.get("api_key", ""),
                model=prov_cfg.get("model", ""),
            )

            backend = BackendFactory.create(pc)

            # 用 AgentBridge 包装 — 提供工具调用 + 对话历史管理
            try:
                from modules.intelligence.agent_bridge import AgentBridge
                bridge = AgentBridge(backend)
                print(f"[ModelSetup] iqra engine + agent bridge initialized: {provider_id}")
                return bridge
            except ImportError as e:
                print(f"[ModelSetup] AgentBridge import failed: {e}, falling back to raw backend")
                return backend

        except Exception as e:
            print(f"[ModelSetup] iqra init error: {e}")
            return None

```
