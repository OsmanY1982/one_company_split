# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
- 标签1: 💬 AI 对话 (iqra ChatWindow)
- 标签2: ⚡ 快捷工具 (模板、本地模型、系统状态)
- 标签3~6: 增强功能（智能对话、快捷操作、系统监控、高级功能）

改进:
- 添加 Ollama 本地模型管理（检测、启动、下载、切换）
- 添加多尺寸模型（超小/中等/大模型）
- 增强本地模型使用体验
- 优化界面布局
- 优化导入路径管理，提升模块加载稳定性
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# ── 路径管理 ──────────────────────────────────────────────────────────────────
# 确保项目根目录（one_company_desktop）在 sys.path 中，
# 使「from iqra.xxx import ...」和「from core.modules.intelligence.xxx import ...」
# 在所有调用场景下均可正常工作。
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────

from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGridLayout, QMessageBox,
    QGroupBox, QComboBox, QDialog, QFormLayout, QCheckBox,
    QProgressBar, QTextEdit, QPlainTextEdit, QApplication,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, QObject, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QParallelAnimationGroup
from PyQt5.QtGui import QFont, QPalette

from core.modules.intelligence._stubs import app_state


# ═══════════════════════════════════════════
# 动画效果工具
# ═══════════════════════════════════════════

class ButtonAnimationHelper:
    """按钮悬停动画助手 - 为QPushButton添加平滑悬停效果"""
    
    @staticmethod
    def apply_hover_animation(button, hover_color=None, pressed_color=None):
        """为按钮应用悬停动画效果
        
        Args:
            button: QPushButton实例
            hover_color: 悬停时的背景色（可选，使用样式表中的颜色）
            pressed_color: 按下时的背景色（可选）
        """
        # 保存原始样式表
        original_style = button.styleSheet()
        button._original_style = original_style
        
        # 设置鼠标追踪
        button.setMouseTracking(True)
        button.setCursor(Qt.PointingHandCursor)
        
        # 安装事件过滤器来实现平滑过渡
        button._animation_helper = ButtonHoverFilter(button, hover_color, pressed_color)
        button.installEventFilter(button._animation_helper)
    
    @staticmethod
    def apply_scale_animation(button, scale_factor=1.05):
        """为按钮应用缩放悬停动画
        
        Args:
            button: QPushButton实例
            scale_factor: 悬停时放大的倍数（默认1.05 = 105%）
        """
        button._scale_factor = scale_factor
        button._original_geometry = None
        button.setMouseTracking(True)
        button.setCursor(Qt.PointingHandCursor)
        
        # 安装事件过滤器
        button._scale_helper = ButtonScaleFilter(button, scale_factor)
        button.installEventFilter(button._scale_helper)


class ButtonHoverFilter(QObject):
    """按钮悬停事件过滤器 - 实现平滑的颜色过渡动画"""
    
    def __init__(self, button, hover_color=None, pressed_color=None):
        super().__init__(button)
        self.button = button
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        
        # 创建动画
        self.animation = QPropertyAnimation(button, b"styleSheet")
        self.animation.setDuration(200)  # 200ms过渡
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == event.Enter:
                # 鼠标进入 - 添加悬停效果
                self._apply_hover_style()
                return True
            elif event.type() == event.Leave:
                # 鼠标离开 - 恢复原始样式
                self._apply_normal_style()
                return True
            elif event.type() == event.MouseButtonPress:
                # 鼠标按下
                self._apply_pressed_style()
                return True
            elif event.type() == event.MouseButtonRelease:
                # 鼠标释放
                if self.button.underMouse():
                    self._apply_hover_style()
                else:
                    self._apply_normal_style()
                return True
        
        return super().eventFilter(obj, event)
    
    def _apply_hover_style(self):
        """应用悬停样式"""
        current_style = self.button.styleSheet()
        
        # 提取背景色并创建悬停版本
        if "background-color:" in current_style:
            # 已有背景色，添加透明度或亮度变化
            lines = current_style.split("\n")
            new_lines = []
            for line in lines:
                if "background-color:" in line:
                    # 添加悬停时的阴影效果
                    if "border-radius:" in current_style:
                        # 保持原有样式，添加轻微阴影
                        line = line.replace(";", "; box-shadow: 0 2px 8px rgba(0,0,0,0.15);")
                new_lines.append(line)
            self.button.setStyleSheet("\n".join(new_lines))
        else:
            # 没有背景色，添加默认悬停效果
            self.button.setStyleSheet(current_style + "\nQPushButton:hover { background-color: rgba(0,0,0,0.05); }")
    
    def _apply_normal_style(self):
        """恢复普通样式"""
        if hasattr(self.button, '_original_style'):
            self.button.setStyleSheet(self.button._original_style)
    
    def _apply_pressed_style(self):
        """应用按下样式"""
        current_style = self.button.styleSheet()
        # 添加按下时的偏移效果
        if "padding:" in current_style:
            # 已有padding，添加轻微偏移
            pass
        self.button.setStyleSheet(current_style + "\nQPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }")


class ButtonScaleFilter(QObject):
    """按钮缩放事件过滤器 - 实现悬停时轻微放大效果"""
    
    def __init__(self, button, scale_factor):
        super().__init__(button)
        self.button = button
        self.scale_factor = scale_factor
        self.animation = None
    
    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == event.Enter:
                self._animate_scale(self.scale_factor)
                return True
            elif event.type() == event.Leave:
                self._animate_scale(1.0)
                return True
        
        return super().eventFilter(obj, event)
    
    def _animate_scale(self, target_scale):
        """动画缩放按钮"""
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self.button, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        current = self.button.geometry()
        if not hasattr(self.button, '_original_geometry') or self.button._original_geometry is None:
            self.button._original_geometry = QRect(current)
        
        original = self.button._original_geometry
        width = original.width()
        height = original.height()
        
        new_width = int(width * target_scale)
        new_height = int(height * target_scale)
        delta_w = new_width - width
        delta_h = new_height - height
        
        new_geometry = QRect(
            original.x() - delta_w // 2,
            original.y() - delta_h // 2,
            new_width,
            new_height
        )
        
        self.animation.setStartValue(current)
        self.animation.setEndValue(new_geometry)
        self.animation.start()


class LoadingAnimationHelper:
    """加载动画助手 - 为耗时操作提供视觉反馈"""
    
    @staticmethod
    def create_loading_button(button, original_text=None):
        """将按钮转换为加载状态
        
        Args:
            button: QPushButton实例
            original_text: 原始文本（可选，会自动保存）
        """
        if original_text:
            button._original_text = original_text
        else:
            button._original_text = button.text()
        
        button.setText("⏳ 处理中...")
        button.setEnabled(False)
        
        # 添加加载动画样式
        loading_style = button.styleSheet()
        loading_style += "\nQPushButton:disabled { background-color: #cbd5e0; color: #718096; }"
        button.setStyleSheet(loading_style)
    
    @staticmethod
    def restore_button(button, new_text=None):
        """恢复按钮到正常状态
        
        Args:
            button: QPushButton实例
            new_text: 新文本（可选，使用原始文本）
        """
        if new_text:
            button.setText(new_text)
        elif hasattr(button, '_original_text'):
            button.setText(button._original_text)
        
        button.setEnabled(True)
    
    @staticmethod
    def create_progress_overlay(parent_widget, message="加载中..."):
        """创建加载遮罩层
        
        Args:
            parent_widget: 父组件
            message: 加载提示信息
        
        Returns:
            QFrame: 遮罩层组件
        """
        overlay = QFrame(parent_widget)
        overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
            }
        """)
        overlay.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignCenter)
        
        # 加载图标（使用文字模拟）
        loading_label = QLabel("⏳")
        loading_label.setFont(QFont("PingFang SC", 48))
        loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(loading_label)
        
        # 加载文字
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #2c3e50; font-size: 16px; font-weight: 600;")
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        # 进度条
        progress = QProgressBar()
        progress.setRange(0, 0)  # 不确定模式
        progress.setMinimumWidth(200)
        progress.setMaximumWidth(300)
        progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                text-align: center;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #2b6cb0;
                border-radius: 5px;
            }
        """)
        layout.addWidget(progress)
        
        overlay.progress = progress
        overlay.message_label = message_label
        
        return overlay


class TabTransitionHelper:
    """标签页切换动画助手"""
    
    @staticmethod
    def apply_tab_transition(tab_widget, duration=250):
        """为QTabWidget添加切换动画
        
        Args:
            tab_widget: QTabWidget实例
            duration: 动画持续时间（毫秒）
        """
        tab_widget._transition_duration = duration
        tab_widget._current_widget = None
        tab_widget._next_widget = None
        tab_widget._animation = None
        
        # 连接标签页切换信号
        tab_widget.currentChanged.connect(
            lambda index: TabTransitionHelper._on_tab_changed(tab_widget, index)
        )
    
    @staticmethod
    def _on_tab_changed(tab_widget, index):
        """处理标签页切换"""
        if index < 0 or index >= tab_widget.count():
            return
        
        new_widget = tab_widget.widget(index)
        if not new_widget:
            return
        
        # 创建淡入动画
        animation = QPropertyAnimation(new_widget, b"windowOpacity")
        animation.setDuration(tab_widget._transition_duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 设置初始透明度
        new_widget.setWindowOpacity(0.0)
        new_widget.show()
        
        # 启动动画
        animation.start()
        tab_widget._animation = animation


# ═══════════════════════════════════════════
# 尝试导入超级智能模块（可选依赖）
# ═══════════════════════════════════════════
try:
    from core.modules.intelligence.super_intelligence import SuperIntelligence
    from core.modules.intelligence.intelligence_integration import upgrade_engine
    SUPER_INTELLIGENCE_AVAILABLE = True
except ImportError:
    SUPER_INTELLIGENCE_AVAILABLE = False


# ═══════════════════════════════════════════
# 快捷提问模板
# ═══════════════════════════════════════════

QUICK_TEMPLATES = [
    ("📊 数据分析", "请分析以下数据并给出建议：\n\n"),
    ("📝 文案撰写", "请帮我撰写以下内容：\n\n"),
    ("💡 头脑风暴", "请就以下主题进行头脑风暴，给出 5 个创意点子：\n\n"),
    ("🔧 代码辅助", "请帮我解决以下编程问题：\n\n"),
    ("📧 邮件撰写", "请帮我撰写一封邮件，主题是：\n\n"),
    ("📋 会议纪要", "请将以下内容整理成会议纪要：\n\n"),
    ("📈 商业计划", "请帮我分析以下商业计划：\n\n"),
    ("🎯 决策建议", "请就以下情况给出决策建议：\n\n"),
]

# 推荐的本地模型（均支持 chat + tools）
# 注意：Gemma 系列（gemma2:*）不支持工具调用，仅能 completion
RECOMMENDED_MODELS = [
    # 超小模型 - 快速测试用
    ("qwen2.5:0.5b", "通义千问 2.5 (0.5B) - 极速测试", "400MB"),
    ("llama3.2:1b", "Llama 3.2 (1B) - 超轻量", "1.3GB"),
    ("qwen2.5:1.5b", "通义千问 2.5 (1.5B) - 轻量中文", "1.0GB"),
    ("phi3:mini", "Phi-3 Mini (3.8B) - 微软轻量", "2.3GB"),
    # 中等模型 - 日常使用
    ("llama3.2:3b", "Llama 3.2 (3B) - 轻量快速", "2.0GB"),
    ("qwen2.5:3b", "通义千问 2.5 (3B) - 中文轻量", "1.9GB"),
    ("deepseek-r1:1.5b", "DeepSeek-R1 (1.5B) - 推理入门", "1.1GB"),
    # 大模型 - 高性能
    ("qwen2.5:7b", "通义千问 2.5 (7B) - 中文优秀", "4.5GB"),
    ("deepseek-r1:7b", "DeepSeek-R1 (7B) - 推理能力强", "4.7GB"),
    ("mistral:7b", "Mistral (7B) - 通用推理", "4.4GB"),
    ("phi4:14b", "Phi-4 (14B) - 微软出品", "9.1GB"),
    # 超大型模型 - 企业级性能（需高配硬件）
    ("qwen2.5:14b", "通义千问 2.5 (14B) - 中文大型", "8.9GB"),
    ("qwen2.5:32b", "通义千问 2.5 (32B) - 企业中文", "~20GB"),
    ("qwen2.5:72b", "通义千问 2.5 (72B) - 旗舰中文", "~45GB"),
    ("deepseek-r1:14b", "DeepSeek-R1 (14B) - 推理大型", "~9GB"),
    ("deepseek-r1:32b", "DeepSeek-R1 (32B) - 推理企业级", "~20GB"),
    ("deepseek-r1:70b", "DeepSeek-R1 (70B) - 推理旗舰", "~43GB"),
    ("llama3.1:8b", "Llama 3.1 (8B) - Meta 最新", "~5GB"),
    ("llama3.3:70b", "Llama 3.3 (70B) - Meta 旗舰", "~40GB"),
    ("mixtral:8x7b", "Mixtral 8x7B - MoE 混合专家", "~26GB"),
    ("command-r:35b", "Command R (35B) - Cohere", "~20GB"),
    ("qwq:32b", "QwQ (32B) - 通义推理", "~20GB"),
    ("mistral-large", "Mistral Large - 欧洲旗舰", "~60GB"),
]


# ═══════════════════════════════════════════
