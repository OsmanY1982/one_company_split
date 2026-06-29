"""
激励广告播放器
支持两种模式：
1. 视频广告（有视频文件时）
2. 内置倒计时广告（无视频文件时自动降级）
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout,
    QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QLinearGradient, QPen
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

import os
import random
from datetime import datetime
from services.ad_service import AdService


# 广告视频目录
AD_VIDEO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "ads", "videos"
)


# ── 内置赞助内容（倒计时广告用）──

SPONSOR_CONTENTS = [
    {
        "title": "一人公司 · 宇宙版",
        "body": (
            "感谢您使用「一人公司·宇宙版」！\n\n"
            "太阳系天文馆已收录 252 颗已命名天体，"
            "支持缩放、拖拽、语音朗读和星谱浏览。\n\n"
            "升级 VIP 会员可解锁全部模块，"
            "享受无限次使用和更多专属功能。"
        ),
        "accent": "#ff8844",
    },
    {
        "title": "探索太阳系的秘密",
        "body": (
            "您知道吗？\n\n"
            "木星拥有 95 颗已确认卫星，"
            "其中木卫二冰层下可能存在液态海洋，"
            "是太阳系中除地球外最有可能存在生命的地方。\n\n"
            "土星环由数十亿冰粒和岩石碎片组成，"
            "宽度可达 28 万公里，但厚度不到 1 公里。"
        ),
        "accent": "#44aaff",
    },
    {
        "title": "天文冷知识",
        "body": (
            "金星的一天比一年还长——\n"
            "自转周期 243 个地球日，公转仅需 225 天。\n\n"
            "如果你在土星上能找到足够大的水池，\n"
            "土星会浮在水面上——它的密度比水还低。\n\n"
            "天王星几乎是躺着转的，自转轴倾斜 98 度，\n"
            "可能是远古时期被一颗大天体撞歪的。"
        ),
        "accent": "#aa66ff",
    },
    {
        "title": "从地球到太阳系边缘",
        "body": (
            "光从太阳到地球需要约 8 分钟，\n"
            "而到海王星需要约 4 小时。\n\n"
            "旅行者 1 号于 1977 年发射，\n"
            "至今已飞行超过 240 亿公里，\n"
            "是目前离地球最远的人造物体。\n\n"
            "它仍在以每秒约 17 公里的速度\n"
            "向星际空间深处飞去。"
        ),
        "accent": "#44dd88",
    },
    {
        "title": "一人公司 · 关于我们",
        "body": (
            "「一人公司」是一个致力于\n"
            "用技术让复杂知识变得触手可及的项目。\n\n"
            "一个人，一台电脑，\n"
            "把浩瀚宇宙装进屏幕。\n\n"
            "每一行代码都在探索\n"
            "如何让天文科普更直观、更有趣。\n\n"
            "感谢您的支持，让我们能继续前行。"
        ),
        "accent": "#ffcc33",
    },
]


def _list_ad_videos():
    """列出所有可用广告视频"""
    if not os.path.isdir(AD_VIDEO_DIR):
        return []
    return sorted([
        f for f in os.listdir(AD_VIDEO_DIR)
        if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))
    ])


# ═══════════════════════════════════════════════════════
# 内置倒计时广告页 (无视频降级方案)
# ═══════════════════════════════════════════════════════

class CountdownAdPage(QWidget):
    """内置倒计时广告：展示赞助内容 + 倒计时 + 领取奖励"""

    COUNTDOWN_MIN = 15
    COUNTDOWN_MAX = 30

    ad_completed = pyqtSignal(int)
    ad_dismissed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedSize(540, 420)

        import random as _random
        self._countdown = self._initial_countdown = _random.randint(self.COUNTDOWN_MIN, self.COUNTDOWN_MAX)
        self._claimed = False

        self._setup_ui()
        self._start_countdown()

    def _setup_ui(self):
        self.setStyleSheet("background: #0a0a18;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QHBoxLayout()
        self._title_label = QLabel("赞助内容")
        self._title_label.setStyleSheet(
            "color: #aaa; font-size: 11px; font-family: 'PingFang SC';"
        )
        title_bar.addWidget(self._title_label)
        title_bar.addStretch()
        layout.addLayout(title_bar)
        layout.addSpacing(12)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,30);")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(18)

        # 随机选一篇赞助内容
        content = random.choice(SPONSOR_CONTENTS)
        accent = content["accent"]

        # 大标题
        title = QLabel(content["title"])
        title.setStyleSheet(
            f"color: {accent}; font-size: 22px; font-weight: bold;"
            " font-family: 'PingFang SC'; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(16)

        # 正文
        body = QLabel(content["body"])
        body.setWordWrap(True)
        body.setStyleSheet(
            "color: #aab; font-size: 13px; line-height: 1.8;"
            " font-family: 'PingFang SC'; background: transparent;"
            " padding: 0 20px;"
        )
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(body, 1)

        # 底部
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 12, 0, 0)

        # 倒计时圆环 + 文字
        self._countdown_widget = _CountdownRing(self)
        self._countdown_widget.setFixedSize(48, 48)
        bottom.addWidget(self._countdown_widget)

        bottom.addSpacing(10)

        countdown_info = QVBoxLayout()
        self._countdown_label = QLabel(f"观看中 · {self._countdown} 秒后可领取")
        self._countdown_label.setStyleSheet(
            "color: #888; font-size: 12px; font-family: 'PingFang SC';"
            " background: transparent;"
        )
        countdown_info.addWidget(self._countdown_label)

        self._hint_label = QLabel("请耐心等待 · 感谢支持")
        self._hint_label.setStyleSheet(
            "color: #555; font-size: 10px; font-family: 'PingFang SC';"
            " background: transparent;"
        )
        countdown_info.addWidget(self._hint_label)
        bottom.addLayout(countdown_info)

        bottom.addStretch()

        # 领取按钮（倒计时结束前禁用）
        self._claim_btn = QPushButton("✓  领取 1 小时延长")
        self._claim_btn.setEnabled(False)
        self._claim_btn.setStyleSheet(
            "QPushButton {"
            " background: #333; color: #666; border: none; border-radius: 8px;"
            " padding: 10px 24px; font-size: 14px; font-family: 'PingFang SC';"
            " }"
            " QPushButton:enabled {"
            " background: #ff6600; color: #fff;"
            " }"
            " QPushButton:enabled:hover { background: #ff8833; }"
        )
        self._claim_btn.clicked.connect(self._on_claim)
        bottom.addWidget(self._claim_btn)

        layout.addLayout(bottom)

    def _start_countdown(self):
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._countdown -= 1
        self._countdown_widget.set_state(
            1 - self._countdown / self._initial_countdown, self._countdown
        )

        if self._countdown <= 0:
            self._timer.stop()
            self._countdown_label.setText("观看完成！点击领取奖励 →")
            self._countdown_label.setStyleSheet(
                "color: #ffaa44; font-size: 12px; font-family: 'PingFang SC';"
                " background: transparent;"
            )
            self._hint_label.setText("感谢您的耐心等待")
            self._claim_btn.setEnabled(True)
        else:
            self._countdown_label.setText(f"观看中 · {self._countdown} 秒后可领取")

    def _on_claim(self):
        if self._claimed:
            return
        self._claimed = True
        self._timer.stop()
        self.ad_completed.emit(3600)
        self.close()

    def closeEvent(self, event):
        if hasattr(self, '_timer'):
            self._timer.stop()
        if not self._claimed:
            self.ad_dismissed.emit()
        event.accept()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 深色背景
        p.setBrush(QColor(10, 10, 24))
        p.setPen(Qt.NoPen)
        p.drawRect(self.rect())

        # 顶部渐变条
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(255, 100, 30, 30))
        grad.setColorAt(0.5, QColor(100, 80, 255, 20))
        grad.setColorAt(1, QColor(30, 150, 255, 30))
        p.setBrush(grad)
        p.drawRect(0, 0, self.width(), 3)

        # 边框
        p.setPen(QPen(QColor(60, 60, 100, 80), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 12, 12)


# ── 倒计时圆环 ──

class _CountdownRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._seconds = 0
        self.setStyleSheet("background: transparent;")

    def set_state(self, pct: float, seconds: int):
        self._progress = min(max(pct, 0.0), 1.0)
        self._seconds = seconds
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        r = min(cx, cy) - 3

        # 背景环
        p.setPen(QPen(QColor(50, 50, 70), 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # 进度弧
        if self._progress > 0:
            pen = QPen(QColor(255, 140, 40), 3)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            span = int(self._progress * 360 * 16)
            p.drawArc(int(cx - r), int(cy - r), int(r * 2), int(r * 2),
                      90 * 16, -span)

        # 秒数
        p.setPen(QColor(200, 200, 220))
        font = QFont("PingFang SC", 10, QFont.Bold)
        p.setFont(font)
        p.drawText(QRectF(cx - r, cy - r, r * 2, r * 2),
                   Qt.AlignCenter, str(self._seconds))


# ═══════════════════════════════════════════════════════
# 主播放器（自动选择模式）
# ═══════════════════════════════════════════════════════

class AdPlayerWidget(QWidget):
    """激励广告播放器：优先视频，降级倒计时"""

    ad_completed = pyqtSignal(int)
    ad_dismissed = pyqtSignal()

    def __init__(self, parent=None, user_id: str = "default"):
        super().__init__(parent)
        self.user_id = user_id
        self._ad_service = AdService(user_id)
        self._ad_duration = 0
        self._elapsed = 0
        self._completed = False
        self._current_ad_path = ""
        self._ad_id = ""

        # 倒计时模式（无视频时）
        self._countdown_mode = False
        self._countdown_page = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background: #000000;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._video_widget = QVideoWidget(self)
        self._video_widget.setMinimumSize(480, 270)
        layout.addWidget(self._video_widget, 1)

        self._player = QMediaPlayer(self)
        self._player.setVideoOutput(self._video_widget)
        self._player.stateChanged.connect(self._on_state_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(20, 8, 20, 12)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setStyleSheet(
            "QProgressBar { background: #333; border: none; border-radius: 2px; }"
            " QProgressBar::chunk { background: #ff6600; border-radius: 2px; }"
        )
        bottom.addWidget(self._progress_bar, 1)

        self._time_label = QLabel("--")
        self._time_label.setStyleSheet(
            "color: #aaa; font-size: 12px; font-family: 'PingFang SC';"
        )
        self._time_label.setFixedWidth(50)
        self._time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom.addWidget(self._time_label)

        self._reward_btn = QPushButton("✓  领取奖励")
        self._reward_btn.setStyleSheet(
            "QPushButton {"
            " background: #ff6600; color: #fff; border: none; border-radius: 6px;"
            " padding: 8px 20px; font-size: 14px; font-family: 'PingFang SC';"
            " }"
            " QPushButton:hover { background: #ff8833; }"
        )
        self._reward_btn.clicked.connect(self._on_reward_claim)
        self._reward_btn.hide()
        bottom.addWidget(self._reward_btn)

        self._close_btn = QPushButton("✕ 放弃奖励")
        self._close_btn.setStyleSheet(
            "QPushButton {"
            " background: transparent; color: #666; border: 1px solid #444;"
            " border-radius: 6px; padding: 8px 16px; font-size: 12px;"
            " font-family: 'PingFang SC';"
            " }"
            " QPushButton:hover { color: #aaa; border-color: #888; }"
        )
        self._close_btn.clicked.connect(self._on_close)
        bottom.addWidget(self._close_btn)

        layout.addLayout(bottom)

        self._tip_label = QLabel("广告播放中，请勿关闭…", self)
        self._tip_label.setStyleSheet(
            "color: rgba(255,255,255,120); font-size: 11px;"
            " font-family: 'PingFang SC'; background: transparent;"
        )
        self._tip_label.setAlignment(Qt.AlignCenter)
        self._tip_label.hide()

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def play_ad(self, ad_path: str) -> bool:
        if not os.path.exists(ad_path):
            return False
        self._countdown_mode = False
        self._current_ad_path = ad_path
        self._ad_id = os.path.splitext(os.path.basename(ad_path))[0]
        self._elapsed = 0
        self._completed = False
        self._ad_duration = 0
        self._progress_bar.setValue(0)
        self._time_label.setText("--")
        self._reward_btn.hide()
        self._close_btn.hide()
        self._video_widget.show()
        url = QUrl.fromLocalFile(ad_path)
        self._player.setMedia(QMediaContent(url))
        self._player.play()
        self._timer.start()
        self._tip_label.show()
        return True

    def auto_play(self) -> bool:
        """自动选择模式：有视频播视频，没视频用倒计时"""
        videos = _list_ad_videos()
        if videos:
            path = os.path.join(AD_VIDEO_DIR, random.choice(videos))
            return self.play_ad(path)

        # 降级：内置倒计时广告
        return self._play_countdown()

    def _play_countdown(self) -> bool:
        """启动内置倒计时广告"""
        self._countdown_mode = True
        self._ad_id = f"builtin_{datetime.now().strftime('%H%M%S')}"
        self._ad_duration = 0  # 倒计时模式时长由 CountdownAdPage 内部管理
        self._elapsed = 0
        self._completed = False

        # 隐藏视频播放器的底部控制栏（倒计时页自己管）
        self._video_widget.hide()
        self._progress_bar.hide()
        self._time_label.hide()
        self._reward_btn.hide()
        self._close_btn.hide()
        self._tip_label.hide()

        # 倒计时页作为子 widget 嵌入
        self._countdown_page = CountdownAdPage(self)
        self.layout().insertWidget(0, self._countdown_page)
        self._countdown_page.ad_completed.connect(self._on_countdown_completed)
        self._countdown_page.ad_dismissed.connect(self._on_countdown_dismissed)

        self._timer.start()
        return True

    def _on_countdown_completed(self, extend_seconds):
        self._completed = True
        self.ad_completed.emit(extend_seconds)
        self._cleanup()
        self.close()

    def _on_countdown_dismissed(self):
        if not self._completed:
            self.ad_dismissed.emit()
        self._cleanup()
        self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._tip_label.setGeometry(0, 10, self.width(), 20)

    def closeEvent(self, event):
        self._cleanup()
        event.accept()

    def _on_duration_changed(self, duration_ms):
        if self._countdown_mode:
            return
        self._ad_duration = duration_ms / 1000.0
        mins = int(self._ad_duration // 60)
        secs = int(self._ad_duration % 60)
        self._time_label.setText(f"{mins}:{secs:02d}")

    def _on_position_changed(self, pos_ms):
        if self._ad_duration > 0 and not self._countdown_mode:
            pct = int(pos_ms / (self._ad_duration * 10))
            self._progress_bar.setValue(min(pct, 100))

    def _on_state_changed(self, state):
        if self._countdown_mode:
            return
        if state == QMediaPlayer.StoppedState and \
           self._player.mediaStatus() == QMediaPlayer.EndOfMedia:
            self._completed = True
            self._timer.stop()
            self._show_reward_ui()

    def _tick(self):
        self._elapsed += 1
        if self._ad_duration > 0 and not self._countdown_mode:
            remaining = max(0, int(self._ad_duration - self._elapsed))
            mins = remaining // 60
            secs = remaining % 60
            self._time_label.setText(f"{mins}:{secs:02d}")

    def _show_reward_ui(self):
        self._tip_label.hide()
        self._time_label.setText("完成！")
        self._reward_btn.show()
        self._close_btn.show()

    def _on_reward_claim(self):
        checksum = self._ad_service._make_checksum(
            self._ad_id, self._ad_duration, self._ad_duration
        )
        result = self._ad_service.verify_watch(
            ad_id=self._ad_id,
            watch_duration=self._ad_duration,
            ad_duration=self._ad_duration,
            checksum=checksum,
        )
        if result["success"]:
            self.ad_completed.emit(result["extend_seconds"])
        else:
            self.ad_dismissed.emit()
        self._cleanup()
        self.close()

    def _on_close(self):
        if self._completed:
            self.ad_dismissed.emit()
        else:
            ratio = self._elapsed / max(self._ad_duration, 1)
            if ratio >= 0.85:
                checksum = self._ad_service._make_checksum(
                    self._ad_id, self._elapsed, self._ad_duration
                )
                result = self._ad_service.verify_watch(
                    ad_id=self._ad_id,
                    watch_duration=self._elapsed,
                    ad_duration=self._ad_duration,
                    checksum=checksum,
                )
                if result["success"]:
                    self.ad_completed.emit(result["extend_seconds"])
            else:
                self.ad_dismissed.emit()
        self._cleanup()
        self.close()

    def _cleanup(self):
        self._timer.stop()
        if not self._countdown_mode:
            self._player.stop()
            self._player.setMedia(QMediaContent())
