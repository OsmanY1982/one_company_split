"""
ChatSessionManager — AI对话 · 会话列表管理面板（左侧边栏）
用于 AIChatWindow 左侧，展示所有历史会话并提供切换/搜索/删除/导出能力。
"""
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit, QLabel, QMenu,
    QMessageBox, QFileDialog, QDialog, QInputDialog,
)
from PyQt5.QtCore import pyqtSignal, Qt, QSize


class ChatSessionManager(QWidget):
    """AI对话 — 会话列表管理面板（左侧边栏）"""

    session_selected = pyqtSignal(str, str)     # session_id, title
    new_chat_requested = pyqtSignal()            # 请求新建会话
    session_copy_requested = pyqtSignal(str)     # session_id（请求复制会话）

    def __init__(self, agent_bridge, parent=None):
        super().__init__(parent)
        self._agent = agent_bridge
        self._sessions = []
        self._current_session_id = ""
        self.setFixedWidth(240)
        self.setStyleSheet("""
            ChatSessionManager {
                background-color: #1a1a2e;
                border-right: 1px solid #2a2a4a;
            }
            QLabel#section_title {
                color: #8888aa;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                text-transform: uppercase;
            }
            QPushButton#new_chat_btn {
                background-color: #3a3a6e;
                color: #e0e0ff;
                border: 1px solid #5a5a8e;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#new_chat_btn:hover {
                background-color: #4a4a8e;
                border-color: #7a7aae;
            }
            QLineEdit#search_box {
                background-color: #12122a;
                color: #ccccdd;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QListWidget#session_list {
                background-color: transparent;
                border: none;
                outline: none;
                color: #ccccdd;
                font-size: 12px;
            }
            QListWidget#session_list::item {
                padding: 8px 10px;
                border-bottom: 1px solid #1f1f3a;
            }
            QListWidget#session_list::item:hover {
                background-color: #252545;
            }
            QListWidget#session_list::item:selected {
                background-color: #2a2a5a;
                border-left: 2px solid #6a6aff;
            }
        """)
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        header = QHBoxLayout()
        header.setContentsMargins(10, 10, 10, 6)
        title_label = QLabel("对话历史")
        title_label.setObjectName("section_title")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # 新建按钮
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 0, 10, 8)
        new_btn = QPushButton("+ 新建对话")
        new_btn.setObjectName("new_chat_btn")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_chat)
        btn_layout.addWidget(new_btn)
        layout.addLayout(btn_layout)

        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(10, 0, 10, 8)
        self._search_box = QLineEdit()
        self._search_box.setObjectName("search_box")
        self._search_box.setPlaceholderText("搜索对话...")
        self._search_box.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_box)
        layout.addLayout(search_layout)

        # 会话列表
        self._list_widget = QListWidget()
        self._list_widget.setObjectName("session_list")
        self._list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list_widget, 1)

        # 底部信息
        bottom = QHBoxLayout()
        bottom.setContentsMargins(10, 6, 10, 8)
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #666688; font-size: 10px;")
        bottom.addWidget(self._count_label)
        layout.addLayout(bottom)

    def _load_sessions(self):
        """从 agent_bridge 加载所有会话列表"""
        try:
            sessions = self._agent.list_sessions()
            self._sessions = sorted(
                sessions,
                key=lambda x: x.get("updated_at", ""),
                reverse=True,
            )
            self._refresh_list()
        except Exception as e:
            print(f"[ChatSessionManager] 加载会话列表失败: {e}")
            self._sessions = []

    def set_sessions(self, sessions: list, current_id: str = ""):
        """兼容 Iqra Sidebar 的推送式 API"""
        self._sessions = sessions
        self._current_session_id = current_id
        self._refresh_list()
        if current_id:
            for i in range(self._list_widget.count()):
                item = self._list_widget.item(i)
                if item and item.data(Qt.UserRole) == current_id:
                    self._list_widget.setCurrentItem(item)
                    break

    def _refresh_list(self, filter_text: str = ""):
        """刷新列表显示"""
        # 阻塞信号，避免 takeItem/addItem 过程中的信号抖动导致重入（参考 sidebar_panel.set_sessions）
        self._list_widget.blockSignals(True)
        try:
            # 必须逐个 removeItemWidget 再清空列表。
            # Qt 的 clear() 只删除 QListWidgetItem，不自动清理 setItemWidget 设置的 QWidget，
            # 导致孤立 widget 累积在 viewport 下，干扰后续 item 的鼠标事件和信号连接。
            while self._list_widget.count():
                item = self._list_widget.takeItem(0)
                if item:
                    self._list_widget.removeItemWidget(item)

            filtered = self._sessions
            if filter_text:
                ft = filter_text.lower()
                filtered = [
                    s for s in self._sessions
                    if ft in s.get("title", "").lower()
                ]

            for s in filtered:
                sid = s.get("id") or s.get("session_id", "")
                title = s.get("title", "未命名对话")[:30]
                msg_count = s.get("message_count", 0)
                updated = s.get("updated_at", "")
                try:
                    dt = datetime.fromisoformat(updated)
                    if dt.date() == datetime.now().date():
                        time_str = dt.strftime("今天 %H:%M")
                    else:
                        time_str = dt.strftime("%m-%d %H:%M")
                except Exception:
                    time_str = ""

                # 自定义行控件: 标题 + 信息 + 操作按钮
                row = QWidget()
                row.setStyleSheet("background: transparent;")
                row.setCursor(Qt.PointingHandCursor)
                row.mousePressEvent = lambda e, sid=sid, t=title: self._select_session(sid, t)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(8, 4, 4, 4)
                row_layout.setSpacing(4)

                # 左侧文本区域
                text_widget = QWidget()
                text_layout = QVBoxLayout(text_widget)
                text_layout.setContentsMargins(0, 0, 0, 0)
                text_layout.setSpacing(1)

                title_lbl = QLabel(title)
                title_lbl.setStyleSheet("color: #ccccdd; font-size: 12px; font-weight: bold; background: transparent;")
                title_lbl.setCursor(Qt.PointingHandCursor)
                title_lbl.mousePressEvent = lambda e, sid=sid, t=title: self._select_session(sid, t)
                text_layout.addWidget(title_lbl)

                info_lbl = QLabel(f"{msg_count}条消息 · {time_str}")
                info_lbl.setStyleSheet("color: #666688; font-size: 10px; background: transparent;")
                text_layout.addWidget(info_lbl)

                row_layout.addWidget(text_widget, 1)

                # ⋮ 三点菜单按钮
                menu_btn = QPushButton("⋮")
                menu_btn.setFixedSize(24, 20)
                menu_btn.setCursor(Qt.PointingHandCursor)
                menu_btn.setToolTip("更多操作")
                menu_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent; color: #666688; border: none;
                        border-radius: 4px; font-size: 14px; font-weight: bold;
                    }
                    QPushButton:hover { background: rgba(120,140,200,30); color: #8899cc; }
                """)
                menu_btn.clicked.connect(lambda checked, ses=sid, btn=menu_btn: self._show_session_menu(ses, btn))
                row_layout.addWidget(menu_btn)

                item = QListWidgetItem()
                item.setData(Qt.UserRole, sid)
                self._list_widget.addItem(item)
                self._list_widget.setItemWidget(item, row)
                # 补偿样式表 QListWidget::item { padding: 8px 10px; } 的垂直 padding (8+8=16px)，
                # 否则 row widget 的文本会被上下截断，只显示一半。
                sh = row.sizeHint()
                item.setSizeHint(QSize(max(sh.width(), 200), max(sh.height(), 40) + 16))

            self._count_label.setText(f"共 {len(filtered)} 个会话")
        finally:
            self._list_widget.blockSignals(False)

    def _on_search(self, text: str):
        self._refresh_list(text)

    def _on_new_chat(self):
        self.new_chat_requested.emit()

    def _on_open_folder(self):
        """打开对话文件存储目录。若当前有选中会话，则定位到该文件。"""
        import subprocess
        import platform
        try:
            sessions_dir = self._agent.get_sessions_dir()
            # 优先：当前有选中会话 → 定位到该文件
            item = self._list_widget.currentItem()
            if item:
                session_id = item.data(Qt.UserRole)
                if session_id:
                    filepath = os.path.join(sessions_dir, f"{session_id}.json")
                    if os.path.exists(filepath):
                        if platform.system() == "Darwin":
                            subprocess.Popen(["open", "-R", filepath])
                        elif platform.system() == "Windows":
                            subprocess.Popen(["explorer", "/select,", filepath])
                        else:
                            subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
                        return
            # 降级：打开整个目录
            if not os.path.exists(sessions_dir):
                os.makedirs(sessions_dir, exist_ok=True)
            if platform.system() == "Darwin":
                subprocess.Popen(["open", sessions_dir])
            elif platform.system() == "Windows":
                os.startfile(sessions_dir)
            else:
                subprocess.Popen(["xdg-open", sessions_dir])
        except Exception as e:
            self._styled_warning("打开失败", f"无法打开对话文件夹:\n{e}")

    def _show_in_finder(self, session_id: str):
        """在 Finder 中定位并选中指定会话文件"""
        import subprocess
        import platform
        try:
            sessions_dir = self._agent.get_sessions_dir()
            filepath = os.path.join(sessions_dir, f"{session_id}.json")
            if not os.path.exists(filepath):
                self._styled_warning("文件不存在", f"会话文件不存在:\n{filepath}")
                return
            if platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", filepath])
            elif platform.system() == "Windows":
                subprocess.Popen(["explorer", "/select,", filepath])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
        except Exception as e:
            self._styled_warning("打开失败", f"无法定位会话文件:\n{e}")

    def _select_session(self, session_id: str, title: str):
        """选中会话（从自定义 item widget 触发）"""
        self._current_session_id = session_id
        self.session_selected.emit(session_id, title)

    def _show_session_menu(self, session_id: str, anchor_btn: QPushButton):
        """点击 ⋮ 弹出的操作菜单"""
        print(f"[Menu] _show_session_menu, session_id={session_id}", flush=True)
        # 获取当前置顶状态
        pinned = False
        sess_title = "对话"
        for s in self._sessions:
            if s.get("id") == session_id or s.get("session_id") == session_id:
                pinned = s.get("pinned", False)
                sess_title = s.get("title", "对话")
                break

        menu = self._build_context_menu(session_id, pinned)
        menu.exec_(anchor_btn.mapToGlobal(anchor_btn.rect().bottomLeft()))

    def _build_context_menu(self, session_id: str, pinned: bool = False) -> QMenu:
        """构建统一的操作菜单（供 ⋮ 按钮和右键共用）"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e3a;
                color: #ccccdd;
                border: 1px solid #2a2a4a;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2a2a5a;
            }
            QMenu::separator {
                height: 1px; background: #2a2a4a; margin: 4px 8px;
            }
        """)

        pin_action = menu.addAction("📌 取消置顶" if pinned else "📌 置顶")
        rename_action = menu.addAction("✏️ 重命名")
        menu.addSeparator()
        finder_action = menu.addAction("🔍 在 Finder 中显示")
        copy_action = menu.addAction("📋 复制会话ID")
        export_action = menu.addAction("📤 导出会话")
        menu.addSeparator()
        delete_action = menu.addAction("🗑 删除")

        # 信号连接
        print(f"[Menu] 构建菜单 session_id={session_id}, pinned={pinned}", flush=True)
        pin_action.triggered.connect(lambda: self._toggle_pin_session(session_id))
        rename_action.triggered.connect(lambda: self._rename_session(session_id))
        finder_action.triggered.connect(lambda: self._show_in_finder(session_id))
        copy_action.triggered.connect(lambda: self._copy_session_id(session_id))
        export_action.triggered.connect(lambda: self._export_session(session_id))
        delete_action.triggered.connect(lambda: self._delete_session(session_id))

        return menu

    def _copy_session_id(self, session_id: str):
        """复制会话ID到剪贴板并反馈"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(session_id)
        self._count_label.setText("已复制")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._count_label.setText(
            f"共 {len(self._sessions)} 个会话"
        ))

    def _toggle_pin_session(self, session_id: str):
        """切换置顶状态"""
        try:
            now_pinned = self._agent.toggle_pin_session(session_id)
            self._load_sessions()
            status = "已置顶" if now_pinned else "已取消置顶"
            # 简洁提示：用状态栏而非弹窗
            self._count_label.setText(f"{status}")
            # 1.5秒后恢复计数
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._count_label.setText(
                f"共 {len(self._sessions)} 个会话"
            ))
        except Exception as e:
            self._styled_warning("操作失败", f"无法执行置顶操作:\n{e}")

    def _delete_session(self, session_id: str):
        """删除指定会话"""
        if self._list_widget.count() <= 1:
            self._styled_info("无法删除", "至少保留一个会话")
            return
        sess_title = "对话"
        for s in self._sessions:
            sid = s.get("id") or s.get("session_id", "")
            if sid == session_id:
                sess_title = s.get("title", "对话")
                break
        # 自定义深色确认弹窗（macOS 原生按钮 CSS 不生效，用 QDialog）
        dlg = QDialog(self)
        dlg.setWindowTitle("确认删除")
        dlg.setFixedSize(380, 160)
        dlg.setStyleSheet("QDialog { background-color: #1e1e3a; }")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 12)
        msg = QLabel(f"确定要删除「{sess_title}」吗？\n删除后不可恢复。")
        msg.setStyleSheet("color: #cccccc; font-size: 13px; background: transparent;")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        no_btn = QPushButton("取消")
        no_btn.setStyleSheet("""
            QPushButton { background: #3a3a5a; color: #cccccc; border: 1px solid #555577;
                          border-radius: 4px; padding: 6px 24px; font-size: 12px; }
            QPushButton:hover { background: #4a4a6a; }
        """)
        no_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(no_btn)
        yes_btn = QPushButton("确认删除")
        yes_btn.setStyleSheet("""
            QPushButton { background: #cc4444; color: #ffffff; border: none;
                          border-radius: 4px; padding: 6px 24px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background: #dd5555; }
        """)
        yes_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(yes_btn)
        layout.addLayout(btn_row)
        if dlg.exec_() != QDialog.Accepted:
            return
        try:
            ok = self._agent.delete_session(session_id)
            if ok:
                if session_id == self._current_session_id:
                    self._current_session_id = ""
                self._load_sessions()
            else:
                self._styled_warning("删除失败", "无法删除该会话")
        except Exception as e:
            self._styled_warning("删除失败", f"删除出错:\n{e}")

    def _styled_warning(self, title: str, message: str):
        """深色主题警告弹窗（QDialog 自定义，macOS 原生按钮样式不生效）"""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setFixedSize(360, 140)
        dlg.setStyleSheet("QDialog { background-color: #1e1e3a; }")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 12)
        msg = QLabel(message)
        msg.setStyleSheet("color: #cccccc; font-size: 13px; background: transparent;")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton { background: #445577; color: #ffffff; border: 1px solid #5577aa;
                          border-radius: 4px; padding: 6px 24px; font-size: 12px; }
            QPushButton:hover { background: #556688; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)
        dlg.exec_()

    def _styled_info(self, title: str, message: str):
        """深色主题信息弹窗"""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setFixedSize(360, 140)
        dlg.setStyleSheet("QDialog { background-color: #1e1e3a; }")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 12)
        msg = QLabel(message)
        msg.setStyleSheet("color: #cccccc; font-size: 13px; background: transparent;")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton { background: #335577; color: #ffffff; border: 1px solid #5577aa;
                          border-radius: 4px; padding: 6px 24px; font-size: 12px; }
            QPushButton:hover { background: #446688; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)
        dlg.exec_()

    def _rename_session(self, session_id: str):
        """重命名会话"""
        # 获取当前标题
        old_title = "对话"
        for s in self._sessions:
            sid = s.get("id") or s.get("session_id", "")
            if sid == session_id:
                old_title = s.get("title", "对话")
                break

        new_title, ok = QInputDialog.getText(
            self, "重命名会话", "新名称:",
            text=old_title
        )
        if ok and new_title.strip():
            new_title = new_title.strip()[:50]  # 限长 50
            try:
                success = self._agent.rename_session(session_id, new_title)
                if success:
                    self._load_sessions()
                else:
                    self._styled_warning("重命名失败", "无法重命名该会话")
            except Exception as e:
                self._styled_warning("重命名失败", str(e))

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """公共重命名方法（供外部信号直接调用）"""
        if not self._agent:
            return False
        try:
            success = self._agent.rename_session(session_id, new_title.strip()[:50])
            if success:
                self._load_sessions()
            return success
        except Exception as e:
            print(f"[ChatSessionManager] rename_session failed: {e}")
            return False

    def _export_session(self, session_id: str):
        """导出会话（从菜单触发）"""
        try:
            default_name = f"chat_{session_id}"
            path, selected_filter = QFileDialog.getSaveFileName(
                self, "导出会话",
                default_name,
                "JSON文件 (*.json);;Markdown文件 (*.md)",
            )
            if not path:
                return
            msgs = self._agent.load_session(session_id)
            info = None
            for s in self._sessions:
                sid = s.get("id") or s.get("session_id", "")
                if sid == session_id:
                    info = s
                    break

            if path.endswith(".md"):
                lines = [
                    f"# {info.get('title', session_id) if info else session_id}\n",
                    f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
                    "---\n",
                ]
                for msg in msgs:
                    role = msg.get("role", "unknown").upper()
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        lines.append(f"\n### {role}\n")
                        lines.append(content)
                        lines.append("")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            else:
                import json
                data = {
                    "session_id": session_id,
                    "title": info.get("title", "Untitled") if info else "Untitled",
                    "exported_at": datetime.now().isoformat(),
                    "messages": msgs,
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            self._show_export_result_dialog(True, path)
        except Exception as e:
            self._show_export_result_dialog(False, str(e))

    def _show_context_menu(self, pos):
        """右键菜单（复用统一菜单构建器）"""
        item = self._list_widget.itemAt(pos)
        if not item:
            return
        session_id = item.data(Qt.UserRole)

        pinned = False
        for s in self._sessions:
            sid = s.get("id") or s.get("session_id", "")
            if sid == session_id:
                pinned = s.get("pinned", False)
                break

        menu = self._build_context_menu(session_id, pinned)
        menu.exec_(self._list_widget.mapToGlobal(pos))

    def _show_export_result_dialog(self, success: bool, detail: str):
        """自定义暗色主题导出结果弹窗（替代 QMessageBox，macOS 原生按钮不可靠）"""
        dlg = QDialog(self)
        dlg.setWindowTitle("导出成功" if success else "导出失败")
        dlg.setFixedSize(420, 120)
        dlg.setAttribute(Qt.WA_StyledBackground, True)
        dlg.setModal(True)
        dlg.setStyleSheet("""
            QDialog { background-color: #1e1e3a; }
            QLabel { color: #ccccdd; font-size: 13px; }
            QPushButton { background-color: #2a2a4a; color: #ccccdd;
                border: 1px solid #3a3a5a; border-radius: 4px;
                padding: 6px 20px; font-size: 12px; min-width: 70px; }
            QPushButton:hover { background-color: #3a3a6a; }
        """)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 12)
        text = f"已导出到:\n{detail}" if success else f"导出失败:\n{detail}"
        layout.addWidget(QLabel(text))
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)
        dlg.exec_()
