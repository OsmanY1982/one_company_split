# `iqra/modules/intelligence/quick_actions.py`

> 路径：`iqra/modules/intelligence/quick_actions.py` | 行数：347


---


```python
# -*- coding: utf-8 -*-
"""
快速操作面板 - 提供常用AI功能的快捷入口
"""

import sys
import os
from typing import Callable, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QLineEdit, QTextEdit, QComboBox, QGroupBox,
    QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class QuickActionThread(QThread):
    """快速操作执行线程"""
    result_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(str)
    
    def __init__(self, action_func, params):
        super().__init__()
        self.action_func = action_func
        self.params = params
        
    def run(self):
        try:
            self.progress_update.emit("执行中...")
            result = self.action_func(**self.params)
            self.result_ready.emit({"success": True, "result": result})
        except Exception as e:
            self.result_ready.emit({"success": False, "error": str(e)})


class QuickActionsWidget(QWidget):
    """快速操作面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_thread = None
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("⚡ 快速操作")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 搜索区域
        search_group = QGroupBox("🔍 快速搜索")
        search_layout = QVBoxLayout(search_group)
        
        search_input_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入搜索关键词...")
        search_input_layout.addWidget(self._search_input)
        
        search_btn = QPushButton("搜索")
        search_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white; padding: 8px 20px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        search_btn.clicked.connect(self._do_search)
        search_input_layout.addWidget(search_btn)
        
        search_layout.addLayout(search_input_layout)
        
        # 搜索引擎选择
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("搜索引擎:"))
        self._engine_combo = QComboBox()
        self._engine_combo.addItems(["必应", "谷歌", "百度", " DuckDuckGo"])
        engine_layout.addWidget(self._engine_combo)
        engine_layout.addStretch()
        search_layout.addLayout(engine_layout)
        
        layout.addWidget(search_group)
        
        # 文件操作区域
        file_group = QGroupBox("📁 文件操作")
        file_layout = QGridLayout(file_group)
        
        # 读取文件
        file_layout.addWidget(QLabel("文件路径:"), 0, 0)
        self._file_path = QLineEdit()
        self._file_path.setPlaceholderText("输入文件路径...")
        file_layout.addWidget(self._file_path, 0, 1)
        
        read_btn = QPushButton("读取")
        read_btn.clicked.connect(self._read_file)
        file_layout.addWidget(read_btn, 0, 2)
        
        # 写入文件
        file_layout.addWidget(QLabel("内容:"), 1, 0)
        self._file_content = QLineEdit()
        self._file_content.setPlaceholderText("输入要写入的内容...")
        file_layout.addWidget(self._file_content, 1, 1)
        
        write_btn = QPushButton("写入")
        write_btn.clicked.connect(self._write_file)
        file_layout.addWidget(write_btn, 1, 2)
        
        layout.addWidget(file_group)
        
        # 代码执行区域
        code_group = QGroupBox("💻 代码执行")
        code_layout = QVBoxLayout(code_group)
        
        self._code_input = QTextEdit()
        self._code_input.setPlaceholderText("输入Python代码...")
        self._code_input.setMaximumHeight(100)
        code_layout.addWidget(self._code_input)
        
        run_btn = QPushButton("▶ 运行代码")
        run_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60; color: white; padding: 10px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #219a52; }
        """)
        run_btn.clicked.connect(self._run_code)
        code_layout.addWidget(run_btn)
        
        layout.addWidget(code_group)
        
        # 浏览器操作
        browser_group = QGroupBox("🌐 浏览器操作")
        browser_layout = QHBoxLayout(browser_group)
        
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("输入URL...")
        browser_layout.addWidget(self._url_input)
        
        screenshot_btn = QPushButton("截图")
        screenshot_btn.clicked.connect(self._take_screenshot)
        browser_layout.addWidget(screenshot_btn)
        
        extract_btn = QPushButton("提取内容")
        extract_btn.clicked.connect(self._extract_content)
        browser_layout.addWidget(extract_btn)
        
        layout.addWidget(browser_group)
        
        # 结果显示
        result_group = QGroupBox("📊 结果")
        result_layout = QVBoxLayout(result_group)
        
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setPlaceholderText("操作结果将显示在这里...")
        result_layout.addWidget(self._result_text)
        
        # 进度条
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        result_layout.addWidget(self._progress)
        
        layout.addWidget(result_group)
        
        layout.addStretch()
        
    def _do_search(self):
        """执行搜索"""
        query = self._search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入搜索关键词")
            return
            
        engine = self._engine_combo.currentText()
        self._run_action(f"搜索: {query} (使用{engine})", self._search, {"query": query, "engine": engine})
        
    def _search(self, query: str, engine: str) -> str:
        """搜索功能"""
        try:
            from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()
            result = assistant.execute_tool('multi_search', {'query': query})
            if result.get('success'):
                return str(result.get('result', '无结果'))
            return f"搜索失败: {result.get('error', '未知错误')}"
        except Exception as e:
            return f"错误: {str(e)}"
            
    def _read_file(self):
        """读取文件"""
        path = self._file_path.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请输入文件路径")
            return
            
        self._run_action(f"读取文件: {path}", self._do_read_file, {"path": path})
        
    def _do_read_file(self, path: str) -> str:
        """执行文件读取"""
        try:
            from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()
            result = assistant.execute_tool('file_read', {'path': path})
            if result.get('success'):
                return result.get('content', '无内容')
            return f"读取失败: {result.get('error', '未知错误')}"
        except Exception as e:
            return f"错误: {str(e)}"
            
    def _write_file(self):
        """写入文件"""
        path = self._file_path.text().strip()
        content = self._file_content.text().strip()
        if not path or not content:
            QMessageBox.warning(self, "提示", "请输入文件路径和内容")
            return
            
        self._run_action(f"写入文件: {path}", self._do_write_file, {"path": path, "content": content})
        
    def _do_write_file(self, path: str, content: str) -> str:
        """执行文件写入"""
        try:
            from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()
            result = assistant.execute_tool('file_write', {'path': path, 'content': content})
            if result.get('success'):
                return "写入成功"
            return f"写入失败: {result.get('error', '未知错误')}"
        except Exception as e:
            return f"错误: {str(e)}"
            
    def _run_code(self):
        """运行代码"""
        code = self._code_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入代码")
            return
            
        self._run_action("执行代码", self._do_run_code, {"code": code})
        
    def _do_run_code(self, code: str) -> str:
        """执行代码"""
        try:
            from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()
            result = assistant.execute_tool('run_code', {'code': code})
            if result.get('success'):
                output = result.get('stdout', '')
                errors = result.get('stderr', '')
                return f"输出:\n{output}\n错误:\n{errors}" if errors else f"输出:\n{output}"
            return f"执行失败: {result.get('error', '未知错误')}"
        except Exception as e:
            return f"错误: {str(e)}"
            
    def _take_screenshot(self):
        """截图"""
        url = self._url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入URL")
            return
            
        self._run_action(f"截图: {url}", self._do_screenshot, {"url": url})
        
    def _do_screenshot(self, url: str) -> str:
        """执行截图"""
        try:
            from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()
            result = assistant.execute_tool('browser_navigate', {'url': url})
            if result.get('success'):
                screenshot_result = assistant.execute_tool('browser_screenshot', {})
                if screenshot_result.get('success'):
                    return f"截图已保存: {screenshot_result.get('path', '未知路径')}"
                return f"截图失败: {screenshot_result.get('error', '未知错误')}"
            return f"导航失败: {result.get('error', '未知错误')}"
        except Exception as e:
            return f"错误: {str(e)}"
            
    def _extract_content(self):
        """提取内容"""
        url = self._url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入URL")
            return
            
        self._run_action(f"提取内容: {url}", self._do_extract, {"url": url})
        
    def _do_extract(self, url: str) -> str:
        """执行内容提取"""
        try:
            from modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()
            result = assistant.execute_tool('browser_navigate', {'url': url})
            if result.get('success'):
                extract_result = assistant.execute_tool('browser_extract', {})
                if extract_result.get('success'):
                    return extract_result.get('text', '无内容')
                return f"提取失败: {extract_result.get('error', '未知错误')}"
            return f"导航失败: {result.get('error', '未知错误')}"
        except Exception as e:
            return f"错误: {str(e)}"
            
    def _run_action(self, description: str, func: Callable, params: Dict[str, Any]):
        """运行操作"""
        if self._current_thread and self._current_thread.isRunning():
            QMessageBox.warning(self, "提示", "有操作正在执行，请等待")
            return
            
        self._result_text.clear()
        self._result_text.append(f"🔄 {description}...")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        
        self._current_thread = QuickActionThread(func, params)
        self._current_thread.result_ready.connect(self._on_result)
        self._current_thread.progress_update.connect(self._on_progress)
        self._current_thread.start()
        
    def _on_progress(self, msg: str):
        """进度更新"""
        self._result_text.append(msg)
        
    def _on_result(self, result: dict):
        """结果处理"""
        self._progress.setVisible(False)
        
        if result['success']:
            self._result_text.append(f"✅ 完成:\n{result['result']}")
        else:
            self._result_text.append(f"❌ 错误:\n{result['error']}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = QuickActionsWidget()
    widget.setWindowTitle("快速操作面板")
    widget.resize(600, 700)
    widget.show()
    sys.exit(app.exec_())

```
