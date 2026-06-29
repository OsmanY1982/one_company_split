"""
I18n Window - 桌面端国际化设置窗口
PyQt5 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QTabWidget, QLineEdit, QTextEdit, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal

from i18n_service import I18nService, get_i18n


class I18nWindow(QMainWindow):
    """国际化设置窗口"""
    
    language_changed = pyqtSignal(str)  # language_code
    
    def __init__(self):
        super().__init__()
        self.service = get_i18n()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("国际化设置")
        self.setGeometry(100, 100, 900, 600)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 语言设置页
        self.language_tab = QWidget()
        self.init_language_tab()
        self.tabs.addTab(self.language_tab, "语言设置")
        
        # 翻译管理页
        self.translation_tab = QWidget()
        self.init_translation_tab()
        self.tabs.addTab(self.translation_tab, "翻译管理")
        
        # 导入导出页
        self.import_export_tab = QWidget()
        self.init_import_export_tab()
        self.tabs.addTab(self.import_export_tab, "导入导出")
    
    def init_language_tab(self):
        """初始化语言设置页"""
        layout = QVBoxLayout(self.language_tab)
        
        # 当前语言
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("当前语言:"))
        self.current_lang_label = QLabel()
        self.current_lang_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        current_layout.addWidget(self.current_lang_label)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # 语言选择
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("切换语言:"))
        
        self.lang_combo = QComboBox()
        languages = self.service.get_supported_languages()
        for code, name in languages.items():
            self.lang_combo.addItem(f"{name} ({code})", code)
        
        # 设置当前语言
        current_index = self.lang_combo.findData(self.service.get_language())
        if current_index >= 0:
            self.lang_combo.setCurrentIndex(current_index)
        
        select_layout.addWidget(self.lang_combo)
        
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self.apply_language)
        select_layout.addWidget(apply_btn)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # 语言信息
        info_group = QWidget()
        info_layout = QVBoxLayout(info_group)
        
        self.lang_info = QLabel()
        self.lang_info.setWordWrap(True)
        info_layout.addWidget(self.lang_info)
        
        layout.addWidget(info_group)
        
        # 示例文本
        example_group = QWidget()
        example_layout = QVBoxLayout(example_group)
        example_layout.addWidget(QLabel("示例文本:"))
        
        self.example_text = QTextEdit()
        self.example_text.setReadOnly(True)
        self.example_text.setMaximumHeight(200)
        example_layout.addWidget(self.example_text)
        
        layout.addWidget(example_group)
        
        layout.addStretch()
    
    def init_translation_tab(self):
        """初始化翻译管理页"""
        layout = QVBoxLayout(self.translation_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("语言:"))
        self.trans_lang_combo = QComboBox()
        languages = self.service.get_supported_languages()
        for code, name in languages.items():
            self.trans_lang_combo.addItem(f"{name} ({code})", code)
        self.trans_lang_combo.currentIndexChanged.connect(self.load_translations)
        toolbar.addWidget(self.trans_lang_combo)
        
        toolbar.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索键或翻译")
        self.search_input.textChanged.connect(self.filter_translations)
        toolbar.addWidget(self.search_input)
        
        save_btn = QPushButton("保存更改")
        save_btn.clicked.connect(self.save_translations)
        toolbar.addWidget(save_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 翻译表格
        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(3)
        self.trans_table.setHorizontalHeaderLabels(["键", "翻译", "操作"])
        self.trans_table.setColumnWidth(0, 250)
        self.trans_table.setColumnWidth(1, 400)
        layout.addWidget(self.trans_table)
    
    def init_import_export_tab(self):
        """初始化导入导出页"""
        layout = QVBoxLayout(self.import_export_tab)
        
        # 导入
        import_group = QWidget()
        import_layout = QVBoxLayout(import_group)
        import_layout.addWidget(QLabel("导入翻译文件:"))
        
        import_btn_layout = QHBoxLayout()
        
        import_json_btn = QPushButton("导入 JSON")
        import_json_btn.clicked.connect(lambda: self.import_translations('json'))
        import_btn_layout.addWidget(import_json_btn)
        
        import_btn_layout.addStretch()
        import_layout.addLayout(import_btn_layout)
        
        layout.addWidget(import_group)
        
        # 导出
        export_group = QWidget()
        export_layout = QVBoxLayout(export_group)
        export_layout.addWidget(QLabel("导出翻译文件:"))
        
        export_btn_layout = QHBoxLayout()
        
        export_json_btn = QPushButton("导出 JSON")
        export_json_btn.clicked.connect(lambda: self.export_translations('json'))
        export_btn_layout.addWidget(export_json_btn)
        
        export_btn_layout.addStretch()
        export_layout.addLayout(export_btn_layout)
        
        layout.addWidget(export_group)
        
        # 缺失翻译
        missing_group = QWidget()
        missing_layout = QVBoxLayout(missing_group)
        missing_layout.addWidget(QLabel("缺失翻译:"))
        
        check_btn = QPushButton("检查缺失翻译")
        check_btn.clicked.connect(self.check_missing_translations)
        missing_layout.addWidget(check_btn)
        
        self.missing_text = QTextEdit()
        self.missing_text.setReadOnly(True)
        missing_layout.addWidget(self.missing_text)
        
        layout.addWidget(missing_group)
        
        layout.addStretch()
    
    def load_data(self):
        """加载数据"""
        self.update_language_info()
        self.load_translations()
    
    def update_language_info(self):
        """更新语言信息"""
        current = self.service.get_language()
        languages = self.service.get_supported_languages()
        
        self.current_lang_label.setText(f"{languages.get(current, current)}")
        
        # 更新示例文本
        examples = [
            f"应用名称: {self.service.t('app_name')}",
            f"欢迎语: {self.service.t('welcome')}",
            f"登录: {self.service.t('login')}",
            f"保存: {self.service.t('save')}",
            f"货币: {self.service.format_currency(1234.56)}",
            f"日期: {self.service.format_date(__import__('datetime').date.today())}",
            f"状态: {self.service.t('status_pending')}",
            f"消息: {self.service.t('msg_search_result', count=42)}",
        ]
        
        self.example_text.setText("\n".join(examples))
        
        # 语言信息
        info_text = f"""
        <b>语言代码:</b> {current}<br>
        <b>货币符号:</b> {self.service.t('currency_symbol')}<br>
        <b>货币代码:</b> {self.service.t('currency_code')}<br>
        <b>日期格式:</b> {self.service.t('date_format')}<br>
        <b>时间格式:</b> {self.service.t('time_format')}<br>
        """
        self.lang_info.setText(info_text)
    
    def apply_language(self):
        """应用语言设置"""
        language = self.lang_combo.currentData()
        if language:
            self.service.set_language(language)
            self.update_language_info()
            self.language_changed.emit(language)
            QMessageBox.information(self, "成功", f"语言已切换为: {language}")
    
    def load_translations(self):
        """加载翻译列表"""
        language = self.trans_lang_combo.currentData()
        if not language:
            return
        
        translations = self.service.translations.get(language, {})
        
        self.trans_table.setRowCount(len(translations))
        
        for i, (key, value) in enumerate(sorted(translations.items())):
            self.trans_table.setItem(i, 0, QTableWidgetItem(key))
            
            # 可编辑的翻译
            value_item = QTableWidgetItem(value)
            value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
            self.trans_table.setItem(i, 1, value_item)
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, k=key: self.delete_translation(k))
            btn_layout.addWidget(delete_btn)
            
            btn_layout.setContentsMargins(5, 0, 5, 0)
            self.trans_table.setCellWidget(i, 2, btn_widget)
    
    def filter_translations(self):
        """筛选翻译"""
        search = self.search_input.text().lower()
        
        for i in range(self.trans_table.rowCount()):
            key_item = self.trans_table.item(i, 0)
            value_item = self.trans_table.item(i, 1)
            
            if key_item and value_item:
                key = key_item.text().lower()
                value = value_item.text().lower()
                
                match = search in key or search in value
                self.trans_table.setRowHidden(i, not match)
    
    def save_translations(self):
        """保存翻译更改"""
        language = self.trans_lang_combo.currentData()
        if not language:
            return
        
        translations = {}
        for i in range(self.trans_table.rowCount()):
            key_item = self.trans_table.item(i, 0)
            value_item = self.trans_table.item(i, 1)
            
            if key_item and value_item:
                translations[key_item.text()] = value_item.text()
        
        # 保存到服务
        for key, value in translations.items():
            self.service.add_translation(language, key, value)
        
        QMessageBox.information(self, "成功", "翻译已保存")
    
    def delete_translation(self, key: str):
        """删除翻译"""
        language = self.trans_lang_combo.currentData()
        if not language:
            return
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除键 '{key}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if key in self.service.translations.get(language, {}):
                del self.service.translations[language][key]
                self.load_translations()
    
    def import_translations(self, format: str):
        """导入翻译"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入翻译文件",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                
                language = self.trans_lang_combo.currentData()
                if language and isinstance(translations, dict):
                    for key, value in translations.items():
                        self.service.add_translation(language, key, value)
                    
                    self.load_translations()
                    QMessageBox.information(self, "成功", "翻译已导入")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
    
    def export_translations(self, format: str):
        """导出翻译"""
        language = self.trans_lang_combo.currentData()
        if not language:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出翻译文件",
            f"translations_{language}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                import json
                translations = self.service.translations.get(language, {})
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"翻译已导出到: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
    
    def check_missing_translations(self):
        """检查缺失翻译"""
        language = self.trans_lang_combo.currentData()
        if not language:
            return
        
        missing = self.service.get_missing_translations(language)
        
        if missing:
            self.missing_text.setText("\n".join(missing))
        else:
            self.missing_text.setText("无缺失翻译")


# 便捷函数
def show_i18n_window():
    """显示国际化设置窗口"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = I18nWindow()
    window.show()
    return window
