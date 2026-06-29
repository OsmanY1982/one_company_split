# ── 紧凑工具栏样式常量 ──
PROVIDER_COMBO_STYLE = """
    QComboBox {
        background: rgba(20,12,40,200); color: #ccbbee;
        border: 1px solid rgba(120,200,80,35); border-radius: 6px;
        padding: 3px 8px; font-size: 11px;
    }
    QComboBox:hover { border: 1px solid rgba(140,220,100,120); }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #99bb88; margin-right:: 6px; }
    QComboBox QAbstractItemView {
        background: rgba(15,8,30,240); color: #ccbbdd;
        border: 1px solid rgba(120,200,80,40); selection-background-color: rgba(100,180,60,50);
    }
"""

BTN_SWITCH = """
    QPushButton {
        background: rgba(0,180,100,50); color: #88ffcc;
        border: 1px solid rgba(0,220,120,80); border-radius: 6px;
        padding: 3px 12px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(0,210,120,80); color: #aaffdd; }
    QPushButton:disabled { background: rgba(0,100,60,25); color: #558866; border-color: rgba(0,120,60,30); }
"""

BTN_GEAR = """
    QPushButton {
        background: rgba(100,140,200,35); color: #99bbee; border: none;
        border-radius: 12px; font-size: 13px;
    }
    QPushButton:hover { background: rgba(120,160,220,60); }
"""

BTN_STOP = """
    QPushButton {
        background: #aa2222;
        color: #ffffff;
        border: 2px solid #ff4444;
        border-radius: 16px;
        padding: 6px 18px;
        font-size: 11px;
        font-weight: 700;
    }
    QPushButton:hover { background: #cc3333; }
"""

BTN_UPLOAD = """
    QPushButton {
        background: rgba(120,100,180,40);
        color: #bbaaee;
        border: 1px solid rgba(140,110,200,60);
        border-radius: 15px;
        padding: 0 12px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton:hover { background: rgba(140,120,200,65); }
"""

FILE_PILL_STYLE = """
    QPushButton {
        background: rgba(255,170,80,40);
        color: #ffbb66;
        border: 1px solid rgba(255,170,80,70);
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 10px;
    }
    QPushButton:hover { background: rgba(255,100,60,70); color: #ffffff; }
"""

BTN_MIC = """
    QPushButton {
        background: #2d8a4e;
        color: #ffffff;
        border: 2px solid #44cc66;
        border-radius: 15px;
        font-size: 13px;
        font-weight: 700;
    }
    QPushButton:hover { background: #3aa85e; }
    QPushButton:pressed { background: #1e6b3a; }
"""

BTN_SPEAK = """
    QPushButton {
        background: rgba(80,200,160,40);
        color: #88ffcc;
        border: 1px solid rgba(80,220,160,60);
        border-radius: 16px;
        padding: 6px 14px;
        font-size: 11px;
        font-weight: 600;
    }
    QPushButton:hover { background: rgba(100,230,180,65); }
"""

# ── 模型选择器 Mixin（热切换增强版）──
import traceback

from PyQt5.QtCore import Qt, QTimer

from core.modules.auth.model_config_panel import (
    PRESET_PROVIDERS, LOCAL_SERVICES, PROVIDER_MODELS, ModelConfigDialog,
)
from core.modules.auth.model_config_panel import _load_iqra_config


class _ModelSelectorMixin:
    """模型选择器（供应商下拉 + 模型下拉 + 自动热切换 + 设置 + 刷新）"""

    # ─── 供应商下拉 ───
    def _populate_provider_combo(self):
        """填充供应商下拉：合并预设云端供应商 + 本地服务 + 已保存的自定义配置"""
        self.cb_provider.blockSignals(True)
        self.cb_provider.clear()

        config = _load_iqra_config()
        active_pid = config.get("active_provider_id", "")
        self._current_provider_id = active_pid

        # ── 云端供应商 ──
        self.cb_provider.addItem("── 云端 ──")
        self.cb_provider.model().item(self.cb_provider.count() - 1).setEnabled(False)
        for p in PRESET_PROVIDERS:
            self.cb_provider.addItem(f"☁  {p['name']}", p["id"])

        saved_cloud = config.get("cloud_providers", {})
        for pid, pdata in saved_cloud.items():
            if pid not in {p["id"] for p in PRESET_PROVIDERS}:
                self.cb_provider.addItem(f"☁  {pdata.get('name', pid)}", pid)

        # ── 本地服务 ──
        self.cb_provider.addItem("── 本地 ──")
        self.cb_provider.model().item(self.cb_provider.count() - 1).setEnabled(False)
        for s in LOCAL_SERVICES:
            self.cb_provider.addItem(f"🖥  {s['name']}", s["id"])

        saved_local = config.get("local_providers", {})
        for pid, pdata in saved_local.items():
            if pid not in {s["id"] for s in LOCAL_SERVICES}:
                self.cb_provider.addItem(f"🖥  {pdata.get('name', pid)}", pid)

        if active_pid:
            for i in range(self.cb_provider.count()):
                if self.cb_provider.itemData(i) == active_pid:
                    self.cb_provider.setCurrentIndex(i)
                    break

        self.cb_provider.blockSignals(False)
        self._on_provider_changed(self.cb_provider.currentIndex())

    def _on_provider_changed(self, idx: int):
        """供应商切换时：更新模型下拉列表，自动设为当前选中模型"""
        if idx < 0:
            return
        pid = self.cb_provider.itemData(idx)
        if not pid:
            return

        models = []

        preset = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
        if preset:
            hardcoded = PROVIDER_MODELS.get(preset["name"], None)
            models = hardcoded if hardcoded else preset.get("models", [])
        else:
            local = next((s for s in LOCAL_SERVICES if s["id"] == pid), None)
            if local:
                models = local.get("models", [])

        # 从 AgentBridge 拉取运行中的模型列表（优先动态列表）
        if self._bridge and hasattr(self._bridge, "list_all_models"):
            try:
                all_models = self._bridge.list_all_models()
                for m in all_models:
                    if isinstance(m, str):
                        mn = m
                    elif isinstance(m, dict):
                        mn = m.get("name") or m.get("model") or m.get("id")
                    else:
                        continue
                    if mn and mn not in models:
                        models.append(mn)
            except Exception:
                traceback.print_exc()
        elif not models and pid in {s["id"] for s in LOCAL_SERVICES}:
            try:
                from core.modules.intelligence.agent_bridge import AgentBridgeModelMixin
                all_models = AgentBridgeModelMixin.list_all_models()
                for m in all_models:
                    if isinstance(m, str):
                        mn = m
                    elif isinstance(m, dict):
                        mn = m.get("name") or m.get("model") or m.get("id")
                    else:
                        continue
                    if mn and mn not in models:
                        models.append(mn)
            except Exception:
                pass

        self.cb_model.blockSignals(True)
        self.cb_model.clear()
        if models:
            for m in models:
                self.cb_model.addItem(m, m)
            if self._current_model:
                idx_m = self.cb_model.findText(self._current_model)
                if idx_m >= 0:
                    self.cb_model.setCurrentIndex(idx_m)
        else:
            self.cb_model.addItem("（无可用模型列表）", "")
        self.cb_model.blockSignals(False)

        self._update_switch_visibility()

    # ─── 模型下拉变更 → 自动热切换 ───
    def _on_model_changed(self, idx: int):
        """模型下拉变更时：自动执行热切换（无需手动点击切换按钮）"""
        if idx < 0:
            return
        model = self.cb_model.itemData(idx)
        if not model:
            return
        self._perform_switch(model)

    # ─── 自动热切换核心 ───
    def _perform_switch(self, model: str):
        """执行模型热切换（自动 + 手动共用）"""
        if getattr(self, "_switching", False):
            return

        provider_id = self.cb_provider.currentData()
        if not provider_id:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 请先选择一个供应商</p>'
            )
            return

        if not self._bridge or not hasattr(self._bridge, "switch_model"):
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] AgentBridge 未连接，无法切换模型</p>'
            )
            return

        self._switching = True
        self._update_switch_visibility()

        try:
            success = self._bridge.switch_model(provider_id, model)
            if success:
                self._current_model = model
                self._current_provider_id = provider_id
                prov = self._bridge.get_provider_info() if hasattr(self._bridge, "get_provider_info") else {}
                prov_name = prov.get("name", provider_id)
                self.lbl_status.setText(f"AgentBridge: {prov_name} / {model}")
                self.lbl_status.setStyleSheet("color: #44cc88; font-size: 11px; background: transparent;")
                self.ai_chat.append(
                    f'<p style="color:#44cc88;font-size:10px;">[系统] 已切换模型: {prov_name} / {model}</p>'
                )
                self._refresh_model_list()
            else:
                self._current_model = getattr(self, "_prev_model", None)
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 切换失败: 未找到供应商配置（{provider_id}）。请先通过 ⚙ 设置配置 API Key。</p>'
                )
                self._restore_model_selection()
        except Exception as e:
            self._current_model = getattr(self, "_prev_model", None)
            self.ai_chat.append(
                f'<p style="color:#ffaa44;font-size:10px;">[系统] 切换失败: {e}</p>'
            )
            self._restore_model_selection()
        finally:
            self._switching = False
            self._update_switch_visibility()

    def _restore_model_selection(self):
        """切换失败时回退模型下拉选中项"""
        prev = getattr(self, "_prev_model", None)
        if prev:
            idx = self.cb_model.findText(prev)
            if idx >= 0:
                self.cb_model.blockSignals(True)
                self.cb_model.setCurrentIndex(idx)
                self.cb_model.blockSignals(False)

    def _update_switch_visibility(self):
        """更新切换按钮状态：热切换模式下仅在切换中禁用"""
        if getattr(self, "_switching", False):
            self.btn_switch.setText("切换中...")
            self.btn_switch.setEnabled(False)
        else:
            self.btn_switch.setText("切换")
            self.btn_switch.setEnabled(True)

    # ─── 手动切换按钮（保留作为兜底）───
    def _on_switch_clicked(self):
        """手动点击切换按钮：保留作为备用（热切换已在模型下拉变更时自动执行）"""
        model = self.cb_model.currentData()
        if not model:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 请先选择一个有效模型</p>'
            )
            return

        self._prev_model = getattr(self, "_current_model", None)
        self._perform_switch(model)

    # ─── 打开完整模型配置 ───
    def _open_model_settings(self):
        """打开 ModelConfigDialog 弹窗进行完整模型配置（含 API Key 设置）"""
        dlg = ModelConfigDialog(self, bridge=self._bridge)
        if self._embedded:
            dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
            dlg.setAttribute(Qt.WA_ShowWithoutActivating, False)
        dlg.accepted.connect(self._on_model_settings_closed)
        dlg.show()
        if self._embedded:
            dlg.raise_()
            dlg.activateWindow()

    def _on_model_settings_closed(self):
        """模型设置弹窗关闭后：刷新全量列表并同步到 AgentBridge 当前模型"""
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()
        self._populate_provider_combo()
        self._refresh_model_list()

    # ─── 刷新模型列表 ───
    def _refresh_model_list(self):
        """从 AgentBridge 拉取全量模型列表，同步到供应商+模型下拉框"""
        self._prev_model = getattr(self, "_current_model", None)

        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()
        if self._bridge and hasattr(self._bridge, "get_provider_info"):
            prov = self._bridge.get_provider_info()
            prov_name = prov.get("name", "")
            for i in range(self.cb_provider.count()):
                pid = self.cb_provider.itemData(i)
                if pid:
                    preset = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
                    if preset and preset["name"] == prov_name:
                        self._current_provider_id = pid
                        break
                    local = next((s for s in LOCAL_SERVICES if s["id"] == pid), None)
                    if local and local["name"] == prov_name:
                        self._current_provider_id = pid
                        break

        self._all_models = []
        if self._bridge and hasattr(self._bridge, "list_all_models"):
            try:
                self._all_models = self._bridge.list_all_models()
            except Exception:
                traceback.print_exc()

        current_idx = self.cb_provider.currentIndex()
        if current_idx >= 0:
            self._on_provider_changed(current_idx)

        if self._bridge and hasattr(self._bridge, "get_provider_info"):
            prov = self._bridge.get_provider_info()
            self.lbl_status.setText(
                f"AgentBridge: {prov.get('name', 'OPCclaw')} / {prov.get('model', self._current_model)}"
            )
            self.lbl_status.setStyleSheet("color: #44cc88; font-size: 11px; background: transparent;")
