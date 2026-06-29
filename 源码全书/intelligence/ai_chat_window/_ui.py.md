# `intelligence/ai_chat_window/_ui.py`

> 路径：`intelligence/ai_chat_window/_ui.py` | 行数：342


---


```python
# ── UI Mixin（__init__ / _build_ui / _toggle_sidebar）──
import traceback
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit,
    QPushButton, QLabel, QComboBox, QApplication, QSplitter,
)
from PyQt5.QtCore import Qt

from core.modules.intelligence.ai_chat_styles import (
    INPUT_STYLE, BTN_PRIMARY, BTN_DANGER, BTN_SETTINGS,
)
from core.modules.intelligence.chat_session_manager import ChatSessionManager
from core.modules.intelligence.session_context import session_ctx

from ._model_selector import (
    PROVIDER_COMBO_STYLE, BTN_SWITCH, BTN_GEAR, BTN_STOP,
    BTN_UPLOAD, FILE_PILL_STYLE, BTN_MIC, BTN_SPEAK,
)


class _UIMixin:
    """__init__ / _build_ui / _toggle_sidebar"""

    def __init__(self, parent=None, iqra_engine=None, floating_mode=False, voice=None, embedded=False, session_id=None):
        super().__init__(parent)
        self._embedded = embedded

        if not embedded:
            self.setWindowFlags(
                Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
            )
            self.setAttribute(Qt.WA_DeleteOnClose)
            self.setWindowTitle("AI助手 · NEURAL v5")
            self.setMinimumSize(600, 400)
            self.resize(780, 580)

        self.setStyleSheet("background: rgba(10,5,20,240);")

        self._bridge = iqra_engine
        self._streaming = False
        self._stream_buffer = ""
        self._stream_block = 0
        self._stream_finalized = False

        if session_id is None:
            session_id = session_ctx.current_session_id
        self._current_session_id = session_id
        self._current_title = session_ctx.current_title

        session_ctx.register_window(self)
        if self._bridge:
            session_ctx.set_agent_bridge(self._bridge)
        self._messages = []
        self._msg_copy_map = {}
        self._next_msg_id = 0

        session_ctx.add_message_listener(self._on_external_message)

        self._voice_input = None
        self._voice_recording = False

        self._speak_process = None

        self._attached_files = []
        self._file_pills = []

        self._suppress_self_notify = False

        self._all_models = []
        self._current_model = ""
        self._current_provider_id = ""
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()

        self._build_ui()
        self._populate_provider_combo()
        self._refresh_model_list()

        # DEBUG
        print(f"[AIChatWindow DEBUG] btn_upload: visible={self.btn_upload.isVisible()} size={self.btn_upload.size()} geo={self.btn_upload.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_mic: visible={self.btn_mic.isVisible()} size={self.btn_mic.size()} geo={self.btn_mic.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_send: visible={self.btn_send.isVisible()} size={self.btn_send.size()} geo={self.btn_send.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_stop: visible={self.btn_stop.isVisible()} size={self.btn_stop.size()} geo={self.btn_stop.geometry()}")
        print(f"[AIChatWindow DEBUG] ai_input: visible={self.ai_input.isVisible()} size={self.ai_input.size()} geo={self.ai_input.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_speak: visible={self.btn_speak.isVisible()} enabled={self.btn_speak.isEnabled()} size={self.btn_speak.size()} geo={self.btn_speak.geometry()}")

        if not embedded:
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                self.move((geom.width() - self.width()) // 2,
                           (geom.height() - self.height()) // 2)

        if self._bridge and self._current_session_id:
            try:
                msgs = self._bridge.load_session(self._current_session_id)
                if msgs:
                    self._messages = msgs
                    for msg in msgs:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "user":
                            self._append_user_msg(content)
                        elif role == "assistant":
                            self._append_ai_msg(content)
                        elif role == "tool":
                            self.ai_chat.append(
                                f'<p style="color:#888;font-size:10px;margin:0;">{content}</p>'
                            )
                    print(f"[AIChatWindow] 从引擎恢复 {len(msgs)} 条消息 (session={self._current_session_id})")
            except Exception as e:
                print(f"[AIChatWindow] 加载会话历史失败: {e}")

    # ─── UI ───
    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        # ── 顶部工具栏 ──
        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        if self._bridge is not None:
            prov = self._bridge.get_provider_info() if hasattr(self._bridge, "get_provider_info") else {}
            status_text = f"AgentBridge: {prov.get('name', 'OPCclaw')} / {prov.get('model', self._current_model)}"
            status_color = "#44cc88"
        else:
            status_text = "引擎未连接 — 离线分析模式"
            status_color = "#ff6644"

        self.lbl_status = QLabel(status_text)
        self.lbl_status.setStyleSheet(
            f"color: {status_color}; font-size: 11px; background: transparent;"
        )
        top_row.addWidget(self.lbl_status)

        # 侧边栏折叠按钮
        self._sidebar_visible = True
        self.btn_toggle_sidebar = QPushButton("◀")
        self.btn_toggle_sidebar.setToolTip("隐藏左侧会话列表")
        self.btn_toggle_sidebar.setFixedSize(24, 20)
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background: rgba(170,80,255,30); color: #bb99dd; border: none;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(170,80,255,60); color: #ddccff; }
        """)
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        top_row.addWidget(self.btn_toggle_sidebar)

        top_row.addStretch()

        # 供应商下拉
        prov_lbl = QLabel("供应商:")
        prov_lbl.setStyleSheet("color: #88aa88; font-size: 11px; background: transparent;")
        top_row.addWidget(prov_lbl)

        self.cb_provider = QComboBox()
        self.cb_provider.setMinimumWidth(130)
        self.cb_provider.setStyleSheet(PROVIDER_COMBO_STYLE)
        self.cb_provider.currentIndexChanged.connect(self._on_provider_changed)
        top_row.addWidget(self.cb_provider)

        # 模型下拉
        model_lbl = QLabel("模型:")
        model_lbl.setStyleSheet("color: #9988aa; font-size: 11px; background: transparent;")
        top_row.addWidget(model_lbl)

        self.cb_model = QComboBox()
        self.cb_model.setMinimumWidth(150)
        self.cb_model.setStyleSheet("""
            QComboBox {
                background: rgba(20,12,40,200); color: #ddccff;
                border: 1px solid rgba(170,80,255,35); border-radius: 6px;
                padding: 3px 8px; font-size: 11px;
            }
            QComboBox:hover { border: 1px solid rgba(180,100,255,120); }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #9988bb; margin-right: 6px; }
            QComboBox QAbstractItemView {
                background: rgba(15,8,30,240); color: #ccbbdd;
                border: 1px solid rgba(170,80,255,40); selection-background-color: rgba(150,60,220,50);
            }
        """)
        top_row.addWidget(self.cb_model)

        # 切换按钮
        self.btn_switch = QPushButton("切换")
        self.btn_switch.setToolTip("切换到选中的供应商和模型（热切换模式下自动切换，按钮仅备用）")
        self.btn_switch.setStyleSheet(BTN_SWITCH)
        self.btn_switch.clicked.connect(self._on_switch_clicked)
        self.cb_model.currentIndexChanged.connect(self._on_model_changed)
        top_row.addWidget(self.btn_switch)

        # 刷新模型按钮
        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setToolTip("刷新模型列表")
        self.btn_refresh.setFixedSize(28, 24)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,35); color: #99bbee; border: none;
                border-radius: 12px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(120,160,220,60); }
        """)
        self.btn_refresh.clicked.connect(self._refresh_model_list)
        top_row.addWidget(self.btn_refresh)

        # 设置按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setToolTip("打开完整模型配置（设置 API Key 等）")
        settings_btn.setFixedSize(28, 24)
        settings_btn.setStyleSheet(BTN_GEAR)
        settings_btn.clicked.connect(self._open_model_settings)
        top_row.addWidget(settings_btn)

        # embedded 模式：关闭对话按钮
        if self._embedded:
            close_btn = QPushButton("关闭对话")
            close_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(220,60,60,50); color: #ff8888;
                    border: 1px solid rgba(255,80,80,80); border-radius: 6px;
                    padding: 3px 12px; font-size: 11px; font-weight: 600;
                }
                QPushButton:hover { background: rgba(255,70,70,80); color: #ffaaaa; }
            """)
            close_btn.clicked.connect(self.chat_close_requested.emit)
            top_row.addWidget(close_btn)

        l.addLayout(top_row)

        # ── 左右分栏 ──
        self._session_manager = ChatSessionManager(self._bridge)
        self._session_manager.session_selected.connect(self._on_session_selected)
        self._session_manager.new_chat_requested.connect(self._on_new_session)
        self._session_manager.session_copy_requested.connect(self._on_session_copy)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.addWidget(self._session_manager)

        # 右侧对话面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.ai_chat = QTextBrowser()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setOpenLinks(False)
        self.ai_chat.anchorClicked.connect(self._on_anchor_clicked)
        self.ai_chat.setAcceptDrops(True)
        self.ai_chat.dragEnterEvent = self._drag_enter_event
        self.ai_chat.dropEvent = self._drop_event
        self.ai_chat.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ai_chat.customContextMenuRequested.connect(self._on_chat_context_menu)
        self.ai_chat.setStyleSheet("""
            QTextBrowser {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        right_layout.addWidget(self.ai_chat, 1)

        # 附件标签行
        self._pills_container = QWidget()
        self._pills_layout = QHBoxLayout(self._pills_container)
        self._pills_layout.setContentsMargins(0, 0, 0, 0)
        self._pills_layout.setSpacing(4)
        self._pills_layout.addStretch()
        self._pills_container.setVisible(False)
        right_layout.addWidget(self._pills_container)

        # 输入行
        ir = QHBoxLayout()

        self.btn_upload = QPushButton("文件")
        self.btn_upload.setToolTip("上传文件或图片（支持拖拽到对话区）")
        self.btn_upload.setFixedSize(50, 30)
        self.btn_upload.setStyleSheet(BTN_UPLOAD)
        self.btn_upload.clicked.connect(self._on_upload_clicked)
        ir.addWidget(self.btn_upload)

        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("输入问题，或拖拽文件到对话区...")
        self.ai_input.setStyleSheet(INPUT_STYLE)
        self.ai_input.returnPressed.connect(self._ai_send)
        ir.addWidget(self.ai_input, 1)

        self.btn_mic = QPushButton("语音")
        self.btn_mic.setToolTip("点击开始语音输入（Apple 语音识别，6秒超时自动发送）")
        self.btn_mic.setFixedSize(60, 30)
        self.btn_mic.setStyleSheet(BTN_MIC)
        self.btn_mic.clicked.connect(self._toggle_voice_input)
        ir.addWidget(self.btn_mic)

        self.btn_send = QPushButton("发送")
        self.btn_send.setStyleSheet(BTN_PRIMARY)
        self.btn_send.clicked.connect(self._ai_send)
        ir.addWidget(self.btn_send)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setStyleSheet(BTN_STOP)
        self.btn_stop.clicked.connect(self._on_stop_generation)
        self.btn_stop.setVisible(False)
        ir.addWidget(self.btn_stop)

        clear_btn = QPushButton("清屏")
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(self._on_clear_chat)
        ir.addWidget(clear_btn)

        self.btn_speak = QPushButton("朗读")
        self.btn_speak.setToolTip("朗读最后一条 AI 回复")
        self.btn_speak.setStyleSheet(BTN_SPEAK)
        self.btn_speak.clicked.connect(self._on_speak_clicked)
        ir.addWidget(self.btn_speak)

        right_layout.addLayout(ir)

        self._splitter.addWidget(right_widget)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        l.addWidget(self._splitter, 1)

    # ─── 侧边栏折叠 ───
    def _toggle_sidebar(self):
        self._sidebar_visible = not self._sidebar_visible
        if self._sidebar_visible:
            self._session_manager.show()
            self.btn_toggle_sidebar.setText("◀")
            self.btn_toggle_sidebar.setToolTip("隐藏左侧会话列表")
        else:
            self._session_manager.hide()
            self.btn_toggle_sidebar.setText("▶")
            self.btn_toggle_sidebar.setToolTip("显示左侧会话列表")

```
