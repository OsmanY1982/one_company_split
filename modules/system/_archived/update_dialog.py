"""
检查更新 — 基于本地 CHANGELOG.md 的版本更新日志查看器
"""
import os
import traceback
import re
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame,
)
from PyQt5.QtCore import Qt

# ═══════ 路径工具 ═══════
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_version_path():
    candidates = [
        os.path.join(_PROJECT_ROOT, "version.txt"),
    ]
    try:
        import sys
        candidates.insert(0, os.path.join(sys._MEIPASS, "version.txt"))
    except Exception:
        pass  # gracefully degrade on I/O failure
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def get_current_version() -> str:
    path = _get_version_path()
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                line = f.readline().strip()
                if line:
                    return line
        except Exception:
            traceback.print_exc()
    return "1.0.0"


def _get_changelog_path():
    p = os.path.join(_PROJECT_ROOT, "CHANGELOG.md")
    if os.path.exists(p):
        return p
    return None


def _parse_changelog(filepath: str) -> list[dict]:
    """解析 CHANGELOG.md，返回版本条目列表 [{version, date, sections: [{title, items}]}]"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        traceback.print_exc()
        return []

    entries = []
    current_entry = None
    current_section = None
    header_re = re.compile(r'^##\s+v?([\d.]+)\s*[-–—]\s*(.+)$')

    for line in lines:
        h = header_re.match(line)
        if h:
            if current_entry:
                if current_section:
                    current_entry.setdefault("sections", []).append(current_section)
                entries.append(current_entry)
            current_entry = {"version": h.group(1), "date": h.group(2).strip(), "sections": []}
            current_section = None
            continue
        if current_entry is None:
            continue
        stripped = line.rstrip()
        if stripped.startswith("### "):
            if current_section:
                current_entry.setdefault("sections", []).append(current_section)
            current_section = {"title": stripped[4:].strip(), "items": []}
            continue
        if current_section is not None and stripped.startswith("- ") and stripped[2:].strip():
            current_section["items"].append(stripped[2:].strip())
            continue

    if current_section:
        current_entry.setdefault("sections", []).append(current_section)
    if current_entry:
        entries.append(current_entry)
    return entries


def _format_changelog_html(entries: list[dict]) -> str:
    """将 changelog 条目格式化为 HTML，用于 QTextEdit"""
    if not entries:
        return '<p style="color:#667788;">暂无更新日志。</p>'

    parts = []
    for entry in entries:
        parts.append(
            f'<h3 style="color:#00cc88;margin-bottom:4px;">'
            f'v{entry["version"]} — {entry["date"]}'
            f'</h3>'
        )
        for sec in entry.get("sections", []):
            parts.append(
                f'<p style="color:#8899cc;margin:6px 0 2px 0;font-weight:600;">'
                f'{sec["title"]}</p>'
            )
            for item in sec.get("items", []):
                parts.append(
                    f'<p style="color:#7788aa;margin:1px 0 1px 12px;font-size:11px;">'
                    f'• {item}'
                    f'</p>'
                )
        parts.append('<hr style="border:0;border-top:1px solid rgba(0,140,220,15);margin:8px 0;">')
    return ''.join(parts)


class UpdateDialog(QDialog):
    """检查更新对话框 — 读取 CHANGELOG.md 展示真实版本历史"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("检查更新")
        self.setFixedSize(480, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._current_version = get_current_version()
        self._changelog_path = _get_changelog_path()
        self._entries = []

        self._build_ui()
        self._apply_style()
        self._load_changelog()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 24, 28, 24)

        # ── 标题行 ──
        title_row = QHBoxLayout()
        icon_label = QLabel("◆")
        icon_label.setObjectName("title_icon")
        title_row.addWidget(icon_label)

        title = QLabel("检查更新")
        title.setObjectName("dialog_title")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        # ── 版本信息行 ──
        ver_frame = QFrame()
        ver_frame.setObjectName("info_frame")
        ver_layout = QVBoxLayout(ver_frame)
        ver_layout.setSpacing(6)
        ver_layout.setContentsMargins(16, 12, 16, 12)

        ver_row = QHBoxLayout()
        ver_row.addWidget(QLabel("当前版本"))
        self._ver_label = QLabel(self._current_version)
        self._ver_label.setObjectName("ver_value")
        self._ver_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ver_row.addWidget(self._ver_label)
        ver_layout.addLayout(ver_row)

        changelog_row = QHBoxLayout()
        changelog_row.addWidget(QLabel("更新日志来源"))
        self._source_label = QLabel(
            os.path.basename(self._changelog_path) if self._changelog_path else "未找到"
        )
        self._source_label.setObjectName("last_check")
        self._source_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        changelog_row.addWidget(self._source_label)
        ver_layout.addLayout(changelog_row)

        layout.addWidget(ver_frame)

        # ── 更新日志区域 ──
        changelog_label = QLabel("更新日志")
        changelog_label.setObjectName("section_label")
        layout.addWidget(changelog_label)

        self._changelog_view = QTextEdit()
        self._changelog_view.setReadOnly(True)
        self._changelog_view.setObjectName("changelog_area")
        self._changelog_view.setPlaceholderText("暂无更新日志。\n请确保项目根目录存在 CHANGELOG.md。")
        layout.addWidget(self._changelog_view, 1)

        # ── 按钮行 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        refresh_btn = QPushButton("刷新日志")
        refresh_btn.setObjectName("check_btn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_changelog)
        btn_row.addWidget(refresh_btn)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a1020, stop:1 #060e1a);
                border: 1px solid rgba(0, 160, 240, 40);
                border-radius: 12px;
            }
            QLabel {
                color: #8899bb;
                font-size: 12px;
                background: transparent;
            }
            #title_icon {
                color: #00a8f0;
                font-size: 14px;
            }
            #dialog_title {
                color: #c0d0ee;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            #info_frame {
                background: rgba(8, 16, 30, 200);
                border: 1px solid rgba(0, 140, 220, 30);
                border-radius: 8px;
            }
            #ver_value {
                color: #00cc88;
                font-size: 13px;
                font-weight: 700;
                font-family: "Menlo", monospace;
            }
            #last_check {
                color: #667788;
                font-size: 11px;
                font-family: "Menlo", monospace;
            }
            #section_label {
                color: #667799;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 2px;
            }
            #changelog_area {
                background: rgba(6, 12, 26, 220);
                color: #7788aa;
                border: 1px solid rgba(0, 140, 220, 25);
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
                font-family: "Menlo", monospace;
            }
            QScrollBar:vertical {
                background: rgba(8, 14, 26, 150);
                width: 4px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(60, 120, 200, 40);
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton {
                border-radius: 16px;
                padding: 7px 20px;
                font-size: 12px;
                font-weight: 600;
            }
            #check_btn {
                background: rgba(0, 140, 240, 30);
                color: #88ccee;
                border: 1px solid rgba(0, 180, 255, 50);
            }
            #check_btn:hover {
                background: rgba(0, 160, 255, 50);
            }
            #close_btn {
                background: rgba(40, 50, 70, 120);
                color: #8899bb;
                border: 1px solid rgba(60, 80, 120, 40);
            }
            #close_btn:hover {
                background: rgba(60, 80, 120, 160);
            }
        """)

    def _load_changelog(self):
        if not self._changelog_path or not os.path.exists(self._changelog_path):
            self._changelog_view.setHtml(
                '<p style="color:#886644;">未找到 CHANGELOG.md，请在项目根目录创建该文件。</p>'
            )
            return
        self._entries = _parse_changelog(self._changelog_path)
        if not self._entries:
            self._changelog_view.setHtml(
                '<p style="color:#667788;">更新日志为空或格式无法解析。</p>'
            )
            return
        html = _format_changelog_html(self._entries)
        self._changelog_view.setHtml(html)
        mtime = os.path.getmtime(self._changelog_path)
        self._source_label.setText(
            f"CHANGELOG.md ({datetime.fromtimestamp(mtime).strftime('%m-%d %H:%M')})"
        )
