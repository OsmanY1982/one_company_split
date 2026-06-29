# `iqra/modules/intelligence/enhanced_chat.py`

> 路径：`iqra/modules/intelligence/enhanced_chat.py` | 行数：469


---


```python
# -*- coding: utf-8 -*-
"""
增强型聊天窗口 - 集成7项核心AI能力
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QCheckBox, QGroupBox,
    QMessageBox, QProgressBar, QSplitter, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor

# 尝试导入增强工具
try:
    from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

try:
    from modules.intelligence.super_intelligence import SuperIntelligence
    SUPER_INTELLIGENCE_AVAILABLE = True
except ImportError:
    SUPER_INTELLIGENCE_AVAILABLE = False


class ToolExecutionThread(QThread):
    """工具执行线程"""
    result_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(str)

    def __init__(self, assistant, tool_name, params):
        super().__init__()
        self.assistant = assistant
        self.tool_name = tool_name
        self.params = params

    def run(self):
        try:
            self.progress_update.emit(f"正在执行: {self.tool_name}...")
            result = self.assistant.execute_tool(self.tool_name, self.params)
            self.result_ready.emit({
                'success': True,
                'result': result,
                'tool': self.tool_name
            })
        except Exception as e:
            self.result_ready.emit({
                'success': False,
                'error': str(e),
                'tool': self.tool_name
            })


class EnhancedChatWidget(QWidget):
    """增强型聊天组件 - 支持工具调用"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._assistant = None
        self._intel = None
        self._current_thread = None
        self._build_ui()
        self._init_systems()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 顶部控制栏
        control_layout = QHBoxLayout()

        # 模式选择
        control_layout.addWidget(QLabel("模式:"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["标准对话", "超级智能", "工具模式"])
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        control_layout.addWidget(self._mode_combo)

        # 功能开关
        self._tools_cb = QCheckBox("启用工具")
        self._tools_cb.setChecked(True)
        control_layout.addWidget(self._tools_cb)

        self._reasoning_cb = QCheckBox("深度推理")
        self._reasoning_cb.setChecked(True)
        control_layout.addWidget(self._reasoning_cb)

        self._learning_cb = QCheckBox("主动学习")
        self._learning_cb.setChecked(True)
        control_layout.addWidget(self._learning_cb)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 主内容区分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：对话历史
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("对话历史"))
        self._chat_history = QTextEdit()
        self._chat_history.setReadOnly(True)
        self._chat_history.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,220); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        left_layout.addWidget(self._chat_history)

        # 输入区域
        input_layout = QHBoxLayout()
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("输入消息... (支持自然语言调用工具)")
        self._input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._input_field)

        send_btn = QPushButton("发送")
        send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(150,60,220,40); color: #ddaaff;
                padding: 8px 20px;
                border: 1px solid rgba(170,80,240,60);
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(170,80,240,70); }
        """)
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        left_layout.addLayout(input_layout)

        splitter.addWidget(left_panel)

        # 右侧：工具面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("可用工具"))
        self._tool_list = QListWidget()
        self._tool_list.setStyleSheet("""
            QListWidget {
                background: rgba(8,4,16,200); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35);
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(170,80,255,25);
            }
            QListWidget::item:selected {
                background: rgba(150,60,220,60);
                color: #ddaaff;
            }
        """)
        right_layout.addWidget(self._tool_list)

        # 工具详情
        self._tool_detail = QTextEdit()
        self._tool_detail.setReadOnly(True)
        self._tool_detail.setPlaceholderText("选择工具查看详情...")
        self._tool_detail.setMaximumHeight(150)
        right_layout.addWidget(self._tool_detail)

        # 执行按钮
        self._exec_btn = QPushButton("▶ 执行选中工具")
        self._exec_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60,180,100,40); color: #88ffbb;
                padding: 10px;
                border: 1px solid rgba(80,200,120,55);
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(80,200,120,70); }
            QPushButton:disabled { background: rgba(80,80,100,40); }
        """)
        self._exec_btn.clicked.connect(self._execute_selected_tool)
        right_layout.addWidget(self._exec_btn)

        splitter.addWidget(right_panel)
        splitter.setSizes([700, 300])

        layout.addWidget(splitter)

        # 状态栏
        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet("color: #776699; padding: 5px; background: transparent;")
        layout.addWidget(self._status_label)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

    def _init_systems(self):
        """初始化AI系统"""
        if ENHANCED_AVAILABLE:
            try:
                self._assistant = EnhancedAIAssistant()
                self._refresh_tool_list()
                self._status_label.setText("增强工具系统已加载")
            except Exception as e:
                self._status_label.setText(f"工具系统加载失败: {str(e)}")
        else:
            self._status_label.setText("增强工具不可用")
            self._tools_cb.setEnabled(False)

        if SUPER_INTELLIGENCE_AVAILABLE:
            try:
                self._intel = SuperIntelligence()
                self._status_label.setText(self._status_label.text() + " | 超级智能已加载")
            except Exception as e:
                print(f"[enhanced_chat] SuperIntelligence 加载失败: {e}")

    def _refresh_tool_list(self):
        """刷新工具列表"""
        self._tool_list.clear()
        if not self._assistant:
            return

        tools = self._assistant.list_tools()
        for tool in tools:
            item = QListWidgetItem(f"{tool.get('icon', '🔧')} {tool['name']}")
            item.setData(Qt.UserRole, tool)
            self._tool_list.addItem(item)

        self._tool_list.itemClicked.connect(self._on_tool_selected)

    def _on_tool_selected(self, item):
        """工具被选中"""
        tool = item.data(Qt.UserRole)
        detail = f"""
<b>{tool.get('icon', '🔧')} {tool['name']}</b><br/>
{tool.get('description', '无描述')}<br/><br/>
<b>参数:</b><br/>
"""
        params = tool.get('parameters', {})
        if params:
            for name, info in params.items():
                detail += f"• {name}: {info.get('description', '')} ({info.get('type', 'string')})<br/>"
        else:
            detail += "无参数<br/>"

        self._tool_detail.setHtml(detail)

    def _on_mode_changed(self, mode):
        """模式切换"""
        if mode == "工具模式":
            self._tools_cb.setChecked(True)
            self._tools_cb.setEnabled(False)
        else:
            self._tools_cb.setEnabled(True)

    def _send_message(self):
        """发送消息"""
        message = self._input_field.text().strip()
        if not message:
            return

        self._input_field.clear()
        self._append_message("用户", message)

        mode = self._mode_combo.currentText()

        if mode == "超级智能" and self._intel:
            self._handle_super_intelligence(message)
        elif mode == "工具模式" or (self._tools_cb.isChecked() and self._assistant):
            self._handle_tool_mode(message)
        else:
            self._append_message("AI", "标准对话模式 - 请切换到超级智能或工具模式以使用增强功能")

    def _handle_super_intelligence(self, message):
        """处理超级智能模式"""
        self._status_label.setText("🧠 超级智能分析中...")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)

        try:
            result = self._intel.process(message)
            reasoning = result.get('reasoning', {})

            # 显示推理过程
            if isinstance(reasoning, dict):
                intent = reasoning.get('intent', {})
                if isinstance(intent, dict):
                    self._append_message("🧠 AI", f"意图识别: {intent.get('primary', 'unknown')}")

                strategy = reasoning.get('strategy', {})
                if isinstance(strategy, dict):
                    steps = strategy.get('steps', [])
                    if steps:
                        self._append_message("🧠 AI", f"执行策略: {' → '.join(steps)}")

            # 显示推荐
            recs = result.get('recommendations', {})
            if isinstance(recs, dict):
                tools = recs.get('suggested_tools', [])
                if tools:
                    self._append_message("🧠 AI", f"推荐工具: {', '.join(tools)}")

            # 显示洞察
            insights = result.get('insights', [])
            if insights:
                for insight in insights:
                    self._append_message("💡 洞察", insight)

            # 如果有执行结果
            execution = result.get('execution')
            if execution:
                self._append_message("🛠️ 执行", str(execution))

        except Exception as e:
            self._append_message("❌ 错误", str(e))
        finally:
            self._progress.setVisible(False)
            self._status_label.setText("就绪")

    def _handle_tool_mode(self, message):
        """处理工具模式"""
        if not self._assistant:
            self._append_message("❌ 错误", "工具系统未初始化")
            return

        self._status_label.setText("🔧 执行工具...")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)

        # 使用超级智能解析意图（如果可用）
        tool_name = None
        params = {"query": message}

        if self._intel and self._reasoning_cb.isChecked():
            try:
                result = self._intel.process(message)
                recs = result.get('recommendations', {})
                if isinstance(recs, dict):
                    tools = recs.get('suggested_tools', [])
                    if tools:
                        tool_name = tools[0]
                        self._append_message("🧠 AI", f"智能选择工具: {tool_name}")
            except Exception:
                pass

        # 如果没有智能选择，尝试直接匹配
        if not tool_name:
            # 简单关键词匹配
            if 'web_search' in message.lower():
                tool_name = 'web_search'
            elif ('网页搜索' in message or '网络搜索' in message or 
                  ('搜索' in message and ('网页' in message or '网络' in message or '在线' in message))):
                tool_name = 'web_search'
            elif '搜索' in message or '查找' in message:
                tool_name = 'multi_search'
            elif '文件' in message or '读取' in message:
                tool_name = 'file_read'
            elif '写' in message or '保存' in message:
                tool_name = 'file_write'
            elif 'web_fetch' in message or 'fetch' in message.lower():
                tool_name = 'web_fetch_page'
            elif '浏览器' in message or '网页' in message:
                tool_name = 'browser_navigate'
            elif '爬虫' in message or '抓取' in message or '爬取' in message:
                tool_name = 'web_scrape' if '批量' not in message else 'batch_scrape'
            elif '任务' in message or '定时' in message:
                tool_name = 'schedule_task'
            elif '记忆' in message:
                tool_name = 'memory_save'
            elif '会话' in message:
                tool_name = 'session_create'
            else:
                self._append_message("AI", f"未识别到匹配工具，请在工具面板中手动选择工具执行。\n您的输入: {message}")
                self._progress.setVisible(False)
                self._status_label.setText("就绪")
                return

        # 执行工具
        self._execute_tool_async(tool_name, params)

    def _execute_tool_async(self, tool_name, params):
        """异步执行工具"""
        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.wait()

        self._current_thread = ToolExecutionThread(self._assistant, tool_name, params)
        self._current_thread.result_ready.connect(self._on_tool_result)
        self._current_thread.progress_update.connect(self._on_tool_progress)
        self._current_thread.start()

    def _on_tool_progress(self, msg):
        """工具执行进度"""
        self._status_label.setText(msg)

    def _on_tool_result(self, result):
        """工具执行结果"""
        self._progress.setVisible(False)

        if result['success']:
            self._append_message("🛠️ 结果", f"工具: {result['tool']}\n{str(result['result'])}")
        else:
            self._append_message("❌ 错误", f"工具: {result['tool']}\n{result['error']}")

        self._status_label.setText("就绪")

    def _execute_selected_tool(self):
        """执行选中的工具"""
        item = self._tool_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个工具")
            return

        tool = item.data(Qt.UserRole)
        tool_name = tool['name']

        # 构建参数对话框（简化版）
        params = {}
        for param_name, param_info in tool.get('parameters', {}).items():
            # 使用默认值或空值
            params[param_name] = param_info.get('default', '')

        self._execute_tool_async(tool_name, params)

    def _append_message(self, sender, message):
        """添加消息到历史"""
        colors = {
            "用户": "#ffaa44",
            "AI": "#44ccff",
            "🧠 AI": "#aa88dd",
            "💡 洞察": "#ffcc44",
            "🛠️ 结果": "#44cc88",
            "🛠️ 执行": "#44cc88",
            "❌ 错误": "#ff6666",
        }
        color = colors.get(sender, "#776699")

        self._chat_history.append(f"""
<div style='margin: 8px 0;'>
    <span style='color: {color}; font-weight: bold;'>{sender}:</span>
    <span style='color: #ccbbdd;'>{message}</span>
</div>
""")

        # 滚动到底部
        scrollbar = self._chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


if __name__ == "__main__":
    # 测试运行
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = EnhancedChatWidget()
    widget.setWindowTitle("增强型聊天 - 7项核心AI能力")
    widget.resize(1200, 800)
    widget.show()
    sys.exit(app.exec_())

```
