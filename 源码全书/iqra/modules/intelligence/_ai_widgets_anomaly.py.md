# `iqra/modules/intelligence/_ai_widgets_anomaly.py`

> 路径：`iqra/modules/intelligence/_ai_widgets_anomaly.py` | 行数：121


---


```python
# -*- coding: utf-8 -*-
"""异常检测 Widget — AnomalyDetectorWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~115 行）
为纯后端模块 anomaly_detector / self_monitor / performance_monitor 提供可视化界面
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout,
    QGroupBox, QTextEdit, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class AnomalyDetectorWidget(QWidget):
    """异常检测可视化面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.anomaly_detector import AnomalyDetector
        from modules.intelligence.self_monitor import SelfMonitor
        from modules.intelligence.performance_monitor import PerformanceMonitor

        self._detector = AnomalyDetector()
        self._self_monitor = SelfMonitor()
        self._perf_monitor = PerformanceMonitor()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🔍 异常检测引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)

        desc = QLabel("实时监控销售/库存/财务/客户行为/系统五大维度，自动识别异常模式")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        types_group = QGroupBox("检测维度")
        types_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        types_layout = QGridLayout(types_group)
        types_layout.setSpacing(10)

        dimensions = [
            ("📊 销售异常", "突然下降/激增检测"),
            ("📦 库存异常", "负库存、异常消耗"),
            ("💰 财务异常", "大额交易、收支异常"),
            ("👤 客户异常", "频繁退货、异常订单"),
            ("⚙ 系统异常", "数据不一致、重复记录"),
        ]
        for i, (name, desc) in enumerate(dimensions):
            card = QFrame()
            card.setStyleSheet("QFrame { background: #f7fafc; border-radius: 8px; padding: 8px; }")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            nl = QLabel(name)
            nl.setFont(QFont("PingFang SC", 14, QFont.Bold))
            nl.setStyleSheet("color: #2c3e50;")
            card_layout.addWidget(nl)
            dl = QLabel(desc)
            dl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            card_layout.addWidget(dl)
            types_layout.addWidget(card, i // 3, i % 3)

        layout.addWidget(types_group)

        btn_layout = QHBoxLayout()
        run_btn = QPushButton("▶ 运行检测")
        run_btn.setMinimumHeight(40)
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setStyleSheet("QPushButton { background: #3498db; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #2980b9; }")
        run_btn.clicked.connect(self._run_detection)
        btn_layout.addWidget(run_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("检测结果将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)

    def _run_detection(self):
        self._output.setText("🔍 正在执行异常检测...\n")
        try:
            result = self._detector.detect_all()
            summary = result.get('summary', {})
            anomalies = result.get('anomalies', [])

            self._output.append(f"✅ 检测完成")
            self._output.append(f"   总计异常: {summary.get('total_anomalies', 0)}")
            self._output.append(f"   严重: {summary.get('critical', 0)} | 警告: {summary.get('warning', 0)} | 信息: {summary.get('info', 0)}")

            health = self._self_monitor.health_check()
            checks = health.get('checks', {})
            self._output.append(f"\n🏥 系统健康检查:")
            for check_name, check_result in checks.items():
                if isinstance(check_result, dict):
                    if 'exists' in check_result:
                        status_icon = '✅' if check_result['exists'] else '❌'
                        self._output.append(f"   {status_icon} {check_name}")
                    elif 'total_gb' in check_result:
                        self._output.append(f"   💾 磁盘: {check_result['free_gb']:.1f}GB 可用 / {check_result['total_gb']:.1f}GB ({check_result['usage_pct']:.1f}%)")
                else:
                    self._output.append(f"   ℹ️ {check_name}: {check_result}")
            self._output.append(f"   总体状态: {health.get('status', '未知')}")

            critical = [a for a in anomalies if a.get('severity') == 'critical']
            if critical:
                self._output.append(f"\n🚨 严重异常:")
                for a in critical:
                    self._output.append(f"   • {a.get('message', '')}")
        except Exception as e:
            self._output.append(f"❌ 检测出错: {e}")

```
