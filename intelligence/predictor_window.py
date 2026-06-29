# -*- coding: utf-8 -*-
"""
销售预测界面
展示销售预测、趋势分析和季节性洞察
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from .sales_predictor import get_predictor


class MetricCard(QFrame):
    """指标卡片"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.setup_ui(title, value, subtitle, color)
    
    def setup_ui(self, title: str, value: str, subtitle: str, color: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        self.setMinimumWidth(200)
        self.setMaximumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; opacity: 0.9;")
        layout.addWidget(self.title_label)
        
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("PingFang SC", 24, QFont.Bold))
        layout.addWidget(self.value_label)
        
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setStyleSheet("font-size: 11px; opacity: 0.8;")
            layout.addWidget(self.subtitle_label)
    
    def update_value(self, value: str, subtitle: str = ""):
        """更新数值"""
        self.value_label.setText(value)
        if subtitle:
            self.subtitle_label.setText(subtitle)


class PredictorWindow(QMainWindow):
    """销售预测主窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.predictor = get_predictor()
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        self.setWindowTitle("销售预测中心")
        self.setMinimumSize(900, 650)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("<h1>销售预测中心</h1>")
        header.addWidget(title)
        header.addStretch()
        
        self.refresh_btn = QPushButton("刷新预测")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # 指标卡片行
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(16)
        
        self.cards = {}
        
        card_configs = [
            ("next_week_pred", "下周预测", "$0", "置信度: -", "#4CAF50"),
            ("today_pred", "今日预测", "$0", "基于历史数据", "#2196F3"),
            ("month_pred", "本月预测", "$0", "趋势: -", "#FF9800"),
            ("accuracy", "模型准确度", "-", "基于近期实际", "#9C27B0"),
        ]
        
        for key, title, value, subtitle, color in card_configs:
            card = MetricCard(title, value, subtitle, color)
            self.cards[key] = card
            self.cards_layout.addWidget(card)
        
        layout.addLayout(self.cards_layout)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 每周预测
        self.weekly_tab = QWidget()
        self.setup_weekly_tab()
        self.tabs.addTab(self.weekly_tab, "每周预测")
        
        # 趋势分析
        self.trend_tab = QWidget()
        self.setup_trend_tab()
        self.tabs.addTab(self.trend_tab, "趋势分析")
        
        # 季节性分析
        self.seasonal_tab = QWidget()
        self.setup_seasonal_tab()
        self.tabs.addTab(self.seasonal_tab, "季节性分析")
        
        layout.addWidget(self.tabs)
    
    def setup_weekly_tab(self):
        """设置每周预测标签页"""
        layout = QVBoxLayout(self.weekly_tab)
        
        # 周预测表格
        self.weekly_table = QTableWidget()
        self.weekly_table.setColumnCount(5)
        self.weekly_table.setHorizontalHeaderLabels([
            "日期", "预测销售额", "预测订单", "置信度", "建议"
        ])
        self.weekly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.weekly_table.setAlternatingRowColors(True)
        
        layout.addWidget(QLabel("<b>未来7天预测</b>"))
        layout.addWidget(self.weekly_table)
        
        # 总结
        self.weekly_summary = QTextEdit()
        self.weekly_summary.setReadOnly(True)
        self.weekly_summary.setMaximumHeight(100)
        self.weekly_summary.setStyleSheet("background-color: #f9f9f9; border-radius: 8px; padding: 8px;")
        layout.addWidget(QLabel("<b>预测总结</b>"))
        layout.addWidget(self.weekly_summary)
    
    def setup_trend_tab(self):
        """设置趋势分析标签页"""
        layout = QVBoxLayout(self.trend_tab)
        
        # 趋势描述
        self.trend_info = QTextEdit()
        self.trend_info.setReadOnly(True)
        self.trend_info.setMinimumHeight(200)
        self.trend_info.setStyleSheet("background-color: #f9f9f9; border-radius: 8px; padding: 12px; font-size: 13px;")
        layout.addWidget(QLabel("<b>趋势分析</b>"))
        layout.addWidget(self.trend_info)
        
        # 最近30天销售
        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(3)
        self.trend_table.setHorizontalHeaderLabels(["日期", "销售额", "订单数"])
        self.trend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("<b>最近30天销售记录</b>"))
        layout.addWidget(self.trend_table)
    
    def setup_seasonal_tab(self):
        """设置季节性分析标签页"""
        layout = QVBoxLayout(self.seasonal_tab)
        
        # 季节性信息
        self.seasonal_info = QTextEdit()
        self.seasonal_info.setReadOnly(True)
        self.seasonal_info.setMinimumHeight(200)
        self.seasonal_info.setStyleSheet("background-color: #f9f9f9; border-radius: 8px; padding: 12px; font-size: 13px;")
        layout.addWidget(QLabel("<b>季节性洞察</b>"))
        layout.addWidget(self.seasonal_info)
        
        # 周分布
        self.weekly_dist_table = QTableWidget()
        self.weekly_dist_table.setColumnCount(3)
        self.weekly_dist_table.setHorizontalHeaderLabels(["星期", "平均销售额", "销售占比"])
        self.weekly_dist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("<b>周销售分布</b>"))
        layout.addWidget(self.weekly_dist_table)
    
    def load_data(self):
        """加载预测数据"""
        try:
            # 获取每周预测
            weekly = self.predictor.predict_next_week()
            
            self.update_cards(weekly)
            self.update_weekly_table(weekly)
            self.update_trend_tab()
            self.update_seasonal_tab()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载预测数据失败: {str(e)}")
    
    def refresh_data(self):
        """刷新数据"""
        self.predictor.refresh_data()
        self.load_data()
    
    def update_cards(self, weekly: dict):
        """更新指标卡片"""
        daily = weekly.get("daily_breakdown", [])
        
        # 下周预测
        next_week_total = sum(d.get("predicted_amount", 0) for d in daily)
        confidence = weekly.get("confidence", 0)
        self.cards["next_week_pred"].update_value(
            f"${next_week_total:,.0f}",
            f"置信度: {confidence:.0f}%"
        )
        
        # 今日预测
        if daily:
            today_pred = daily[0]
            self.cards["today_pred"].update_value(
                f"${today_pred.get('predicted_amount', 0):,.0f}",
                f"{today_pred.get('predicted_orders', 0)} 笔预计"
            )
        
        # 本月预测
        self.cards["month_pred"].update_value(
            f"${next_week_total * 4.3:,.0f}",
            f"趋势: {weekly.get('trend', 'stable')}"
        )
        
        # 准确度
        self.cards["accuracy"].update_value(
            f"{confidence:.0f}%",
            f"模型: 线性回归+季节性"
        )
    
    def update_weekly_table(self, weekly: dict):
        """更新周预测表格"""
        daily = weekly.get("daily_breakdown", [])
        self.weekly_table.setRowCount(len(daily))
        
        for i, day in enumerate(daily):
            self.weekly_table.setItem(i, 0, QTableWidgetItem(day.get("date", "")))
            self.weekly_table.setItem(i, 1, QTableWidgetItem(
                f"${day.get('predicted_amount', 0):,.2f}"
            ))
            self.weekly_table.setItem(i, 2, QTableWidgetItem(
                str(day.get("predicted_orders", 0))
            ))
            self.weekly_table.setItem(i, 3, QTableWidgetItem(
                f"{weekly.get('confidence', 0):.0f}%"
            ))
            
            # 建议
            amount = day.get("predicted_amount", 0)
            avg = sum(d.get("predicted_amount", 0) for d in daily) / max(len(daily), 1)
            if amount > avg * 1.3:
                suggestion = "建议增加备货"
            elif amount < avg * 0.7:
                suggestion = "可适当减少库存"
            else:
                suggestion = "正常运营"
            
            self.weekly_table.setItem(i, 4, QTableWidgetItem(suggestion))
        
        # 更新总结
        total_pred = sum(d.get("predicted_amount", 0) for d in daily)
        trend = weekly.get("trend", "stable")
        
        summary = f"未来7天总预测销售额: ${total_pred:,.0f}"
        if trend == "up":
            summary += " | 趋势向上，建议增加库存准备"
        elif trend == "down":
            summary += " | 趋势向下，注意控制成本"
        else:
            summary += " | 趋势稳定，按常规运营即可"
        
        self.weekly_summary.setText(summary)
    
    def update_trend_tab(self):
        """更新趋势标签页"""
        try:
            # 获取趋势数据
            daily_sales = self.predictor.get_daily_sales(30)
            
            self.trend_table.setRowCount(len(daily_sales))
            
            total = sum(d.get("amount", 0) for d in daily_sales)
            avg = total / max(len(daily_sales), 1)
            
            for i, day in enumerate(daily_sales):
                self.trend_table.setItem(i, 0, QTableWidgetItem(day.get("date", "")))
                self.trend_table.setItem(i, 1, QTableWidgetItem(
                    f"${day.get('amount', 0):,.2f}"
                ))
                self.trend_table.setItem(i, 2, QTableWidgetItem(
                    str(day.get("orders", 0))
                ))
            
            # 趋势分析
            if len(daily_sales) >= 14:
                first_week = sum(d.get("amount", 0) for d in daily_sales[:7])
                last_week = sum(d.get("amount", 0) for d in daily_sales[-7:])
                
                if last_week > first_week * 1.1:
                    trend_desc = "上升"
                    color = "green"
                elif last_week < first_week * 0.9:
                    trend_desc = "下降"
                    color = "red"
                else:
                    trend_desc = "平稳"
                    color = "gray"
                
                growth = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
                
                info = f"""
                <h3>趋势分析</h3>
                <p>近30天销售趋势: <span style="color:{color}; font-weight:bold;">{trend_desc}</span></p>
                <p>日均销售额: <b>${avg:,.2f}</b></p>
                <p>最近7天 vs 前7天: <b>{growth:+.1f}%</b></p>
                <p>总销售额(30天): <b>${total:,.2f}</b></p>
                """
            else:
                info = f"""
                <h3>趋势分析</h3>
                <p>数据点不足，需要更多历史数据才能进行趋势分析。</p>
                <p>当前数据天数: {len(daily_sales)}</p>
                <p>日均销售额: <b>${avg:,.2f}</b></p>
                """
            
            self.trend_info.setHtml(info)
            
        except Exception as e:
            self.trend_info.setText(f"加载趋势数据失败: {str(e)}")
    
    def update_seasonal_tab(self):
        """更新季节性标签页"""
        try:
            seasonal = self.predictor.get_seasonal_analysis()
            
            # 季节性信息
            info = f"""
            <h3>季节性洞察</h3>
            <p>最佳销售日: <b>{seasonal.get('best_day', 'N/A')}</b></p>
            <p>最差销售日: <b>{seasonal.get('worst_day', 'N/A')}</b></p>
            <p>销售高峰时段: <b>{seasonal.get('peak_hours', 'N/A')}</b></p>
            <p>建议: {seasonal.get('recommendation', '暂无建议')}</p>
            """
            self.seasonal_info.setHtml(info)
            
            # 周分布
            weekly_dist = seasonal.get("weekly_distribution", [])
            total_dist = sum(d.get("avg_amount", 0) for d in weekly_dist)
            
            self.weekly_dist_table.setRowCount(len(weekly_dist))
            
            for i, dist in enumerate(weekly_dist):
                self.weekly_dist_table.setItem(i, 0, QTableWidgetItem(dist.get("day", "")))
                self.weekly_dist_table.setItem(i, 1, QTableWidgetItem(
                    f"${dist.get('avg_amount', 0):,.2f}"
                ))
                
                if total_dist > 0:
                    pct = dist.get("avg_amount", 0) / total_dist * 100
                    self.weekly_dist_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))
                else:
                    self.weekly_dist_table.setItem(i, 2, QTableWidgetItem("0%"))
        
        except Exception as e:
            self.seasonal_info.setText(f"加载季节性数据失败: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = PredictorWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
