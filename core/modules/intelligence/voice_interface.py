# -*- coding: utf-8 -*-
"""
语音交互模块 — macOS 原生 Apple Speech Framework + say 命令
零第三方依赖（PyObjC 除外），离线可用，中文识别准确率高
"""

import subprocess
import time
import os
import threading
from typing import Optional, Union

from PyQt5.QtCore import QThread, pyqtSignal, QObject
from core.dark_tool_theme import DARK_TEXT, DARK_TEXT_MUTED, DARK_BTN_PRIMARY, DARK_BTN_DANGER, DARK_PREVIEW_STYLE, ACCENT_BLUE_DIM

# WhisperRecognizer is optional (depends on numpy + faster_whisper)
try:
    from core.modules.intelligence.whisper_recognizer import WhisperRecognizer
    _HAVE_WHISPER = True
except ImportError:
    _HAVE_WHISPER = False


# ═══════════ 语音识别（Apple Speech Framework） ═══════════

class AppleSpeechRecognizer(QThread):
    """基于 Apple Speech Framework 的语音识别线程"""
    text_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, locale: str = "zh_CN", timeout: float = 10.0):
        super().__init__()
        self.locale = locale
        self.timeout = timeout
        self._running = True

    def run(self):
        try:
            from Speech import (
                SFSpeechRecognizer, SFSpeechAudioBufferRecognitionRequest,
                SFSpeechRecognizerAuthorizationStatus,
            )
            import AVFoundation

            # 权限检查
            # pyobjc 12.x: authorizationStatus() 返回 int
            # 3 = Authorized, 0 = NotDetermined, 1 = Denied, 2 = Restricted
            status = SFSpeechRecognizer.authorizationStatus()
            if status == 0:  # NotDetermined — 主动请求授权
                self.status_changed.emit("正在请求语音识别权限...")
                # requestAuthorization 是异步回调，用信号量等结果
                import threading
                auth_event = threading.Event()
                auth_result = [0]

                def auth_handler(status_val):
                    auth_result[0] = int(status_val)
                    auth_event.set()

                SFSpeechRecognizer.requestAuthorization_(auth_handler)
                # 等待系统弹窗（最多等 30 秒）
                if not auth_event.wait(timeout=30.0):
                    self.error_occurred.emit("语音识别授权超时，请在系统设置中手动开启")
                    return
                status = auth_result[0]
                if status != 3:
                    if status == 1:
                        self.error_occurred.emit("语音识别权限被拒绝，请在 系统设置 → 隐私与安全性 → 语音识别 中开启")
                    else:
                        self.error_occurred.emit("语音识别权限未授权，请在系统设置中开启")
                    return
            elif status != 3:
                if status == 1:
                    self.error_occurred.emit("语音识别权限被拒绝，请在 系统设置 → 隐私与安全性 → 语音识别 中开启")
                else:
                    self.error_occurred.emit("语音识别权限未授权，请在系统设置中开启")
                return

            ns_locale = __import__('Foundation', fromlist=['NSLocale']).NSLocale
            locale_obj = ns_locale.localeWithLocaleIdentifier_(self.locale)
            recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale_obj)
            if not recognizer or not recognizer.isAvailable():
                self.error_occurred.emit("当前地区的语音识别不可用")
                return

            audio_engine = AVFoundation.AVAudioEngine.alloc().init()
            input_node = audio_engine.inputNode()
            bus = 0
            native_format = input_node.outputFormatForBus_(bus)

            request = SFSpeechAudioBufferRecognitionRequest.alloc().init()
            # macOS 26+ 中 shouldReportPartialResults 为只读属性
            try:
                request.shouldReportPartialResults = True
            except (AttributeError, Exception):
                pass  # 新版 SDK 默认已启用部分结果
            request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition()

            input_node.installTapOnBus_bufferSize_format_block_(
                bus, 1024, native_format,
                lambda buf, _when: request.appendAudioPCMBuffer_(buf),
            )

            audio_engine.prepare()
            objc_module = __import__('objc', fromlist=['objc'])
            error_ptr = objc_module.objc.nil
            success, _ = audio_engine.startAndReturnError_(error_ptr)
            if not success:
                self.error_occurred.emit("无法启动麦克风")
                return

            self.status_changed.emit("正在聆听...")

            result_container = [""]

            def result_handler(result, error):
                if not self._running:
                    return
                if error:
                    ns_error = error
                    self.error_occurred.emit(f"识别错误: {ns_error}")
                elif result:
                    final_str = result.bestTranscription().formattedString()
                    if result.isFinal():
                        result_container[0] = final_str
                    else:
                        self.text_ready.emit(final_str)

            task = recognizer.recognitionTaskWithRequest_resultHandler_(
                request, result_handler,
            )

            elapsed = 0.0
            while self._running and elapsed < self.timeout:
                time.sleep(0.1)
                elapsed += 0.1
                if task.isFinishing() or task.isCancelled():
                    break

            if self._running:
                task.finish()
            audio_engine.stop()
            input_node.removeTapOnBus_(bus)

            final_text = result_container[0]
            if not final_text.strip() and hasattr(task, 'bestTranscription') and task.bestTranscription():
                final_text = task.bestTranscription().formattedString()

            if final_text.strip():
                self.text_ready.emit(final_text)
            else:
                self.error_occurred.emit("未能识别到语音")

        except ImportError as e:
            self.error_occurred.emit(f"缺少依赖: {e}")
        except Exception as e:
            self.error_occurred.emit(f"语音识别异常: {e}")

    def stop(self):
        self._running = False


# ═══════════ 语音合成（macOS say 命令） ═══════════

class AppleSpeechSynthesizer(QThread):
    """基于 macOS say 命令的语音合成线程"""
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, voice: str = "Flo", rate: int = 180):
        """
        Args:
            text: 要合成的文本
            voice: 语音名（Flo/Meijia/Eddy/Reed）
            rate: 语速（字/分钟），默认 180
        """
        super().__init__()
        self.text = text
        self.voice = voice
        self.rate = rate

    def run(self):
        try:
            cmd = ["say", "-v", self.voice, "-r", str(self.rate), self.text]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.finished.emit()
            else:
                self.error_occurred.emit(f"语音合成失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.error_occurred.emit("语音合成超时")
        except FileNotFoundError:
            self.error_occurred.emit("系统未找到 say 命令")
        except Exception as e:
            self.error_occurred.emit(f"语音合成异常: {e}")


# ═══════════ 语音交互接口 ═══════════

class VoiceInterface(QObject):
    """语音交互统一接口 — 识别 + 合成 + 状态管理"""

    recognition_result = pyqtSignal(str)
    recognition_status = pyqtSignal(str)
    synthesis_done = pyqtSignal()
    error_occurred = pyqtSignal(str)

    CHINESE_VOICES = [
        ("Flo",     180),    # 大陆女声，自然流畅
        ("Meijia",  175),    # 台湾女声，甜美
        ("Eddy",    180),    # 大陆男声
        ("Reed",    185),    # 男声
    ]

    def __init__(self, stt_engine: str = "apple", tts_engine: str = "apple"):
        super().__init__()
        self._recognizer: Optional[Union[AppleSpeechRecognizer, WhisperRecognizer]] = None
        self._synthesizer: Optional[AppleSpeechSynthesizer] = None
        self._is_listening = False
        self._voice_index = 0
        self._whisper_thread: Optional[threading.Thread] = None
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine

    # ── 识别 ──

    def start_apple_listening(self, timeout: float = 8.0, locale: str = "zh_CN"):
        """Apple Speech 语音识别（唤醒模式入口）"""
        self.start_listening(timeout=timeout, locale=locale)

    def start_listening(self, timeout: float = 8.0, locale: str = "zh_CN"):
        """开始语音识别 — 根据 stt_engine 自动选择后端"""
        if self._is_listening:
            return

        self._is_listening = True

        if self.stt_engine == "whisper" and _HAVE_WHISPER:
            self._start_whisper_listening(timeout)
        else:
            self._start_apple_listening(timeout, locale)

    def _start_apple_listening(self, timeout: float, locale: str):
        """Apple Speech 原生识别（零依赖，macOS 内置）"""
        self._recognizer = AppleSpeechRecognizer(locale=locale, timeout=timeout)
        self._recognizer.status_changed.connect(self.recognition_status.emit)
        self._recognizer.text_ready.connect(self.recognition_result.emit)
        self._recognizer.error_occurred.connect(self._on_recognition_error)
        self._recognizer.finished.connect(self._on_recognition_finished)
        self._recognizer.start()

    def _start_whisper_listening(self, timeout: float):
        """Whisper 识别（faster-whisper large-v3，纯本地高精度）"""
        self.recognition_status.emit("加载 Whisper 模型...")
        self._recognizer = WhisperRecognizer(model_size="large-v3")
        self._recognizer.status_changed.connect(self.recognition_status.emit)
        self._recognizer.error_occurred.connect(self._on_recognition_error)
        self._whisper_thread = threading.Thread(
            target=self._whisper_listen_worker, args=(timeout,), daemon=True
        )
        self._whisper_thread.start()

    def _whisper_listen_worker(self, timeout: float):
        """Whisper 后台识别线程 — 调用 listen_once 并发射信号"""
        try:
            self.recognition_status.emit("正在聆听...")
            result = self._recognizer.listen_once(timeout=timeout)
            if result:
                self.recognition_result.emit(result)
            else:
                self.error_occurred.emit("未识别到语音")
            self._on_recognition_finished()
        except Exception as e:
            self._on_recognition_error(str(e))

    def stop_listening(self):
        self._is_listening = False
        if self._recognizer:
            if isinstance(self._recognizer, WhisperRecognizer):
                self._recognizer.stop()
            elif self._recognizer.isRunning():
                self._recognizer.stop()
                self._recognizer.wait(1500)

    def is_listening(self) -> bool:
        return self._is_listening

    def _on_recognition_error(self, error: str):
        self._is_listening = False
        self.error_occurred.emit(error)

    def _on_recognition_finished(self):
        self._is_listening = False

    # ── 合成 ──

    def speak(self, text: str, voice: str = None):
        """朗读文本（直接播放），自动停止旧播报防止重叠"""
        # 终止旧的合成器，防止重叠播报
        self.stop_speaking()

        v = voice or self.CHINESE_VOICES[self._voice_index][0]
        r = self.CHINESE_VOICES[self._voice_index][1]
        self._synthesizer = AppleSpeechSynthesizer(text, voice=v, rate=r)
        self._synthesizer.finished.connect(lambda: self.synthesis_done.emit())
        self._synthesizer.error_occurred.connect(lambda e: self.error_occurred.emit(e))
        self._synthesizer.start()

    def stop_speaking(self):
        """停止当前语音合成（如果有的话）"""
        if self._synthesizer and self._synthesizer.isRunning():
            self._synthesizer.terminate()
            self._synthesizer.wait(500)
            self._synthesizer = None

    # ── 切换语音 ──

    def next_voice(self) -> str:
        self._voice_index = (self._voice_index + 1) % len(self.CHINESE_VOICES)
        return self.CHINESE_VOICES[self._voice_index][0]

    def current_voice(self) -> str:
        return self.CHINESE_VOICES[self._voice_index][0]

    def current_voice_label(self) -> str:
        return f"{self.CHINESE_VOICES[self._voice_index][0]} ({self.CHINESE_VOICES[self._voice_index][1]}wpm)"


# ═══════════ 语音交互面板 Widget ═══════════

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt


class VoiceWidget(QDialog):
    """语音交互面板 — 供 AI 助手星球路由使用"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._voice = VoiceInterface()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("语音接口")
        self.setMinimumSize(500, 420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("Mac 本地语音交互")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {DARK_TEXT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 状态显示
        self._status_label = QLabel("就绪")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._status_label)

        # 语音选择
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("语音:"))
        self._voice_label = QLabel(self._voice.current_voice_label())
        self._voice_label.setStyleSheet("font-weight: bold;")
        voice_layout.addWidget(self._voice_label)
        voice_layout.addStretch()
        switch_btn = QPushButton("切换语音")
        switch_btn.clicked.connect(self._on_switch_voice)
        voice_layout.addWidget(switch_btn)
        layout.addLayout(voice_layout)

        # 识别结果区
        self._result_area = QTextEdit()
        self._result_area.setReadOnly(True)
        self._result_area.setPlaceholderText("语音识别结果将显示在这里...")
        self._result_area.setMaximumHeight(120)
        layout.addWidget(self._result_area)

        # 合成输入区
        synth_layout = QHBoxLayout()
        self._synth_input = QLineEdit()
        self._synth_input.setPlaceholderText("输入要让 Mac 朗读的文字...")
        synth_layout.addWidget(self._synth_input)

        speak_btn = QPushButton("朗读")
        speak_btn.setStyleSheet(DARK_BTN_PRIMARY)
        speak_btn.clicked.connect(self._on_speak)
        synth_layout.addWidget(speak_btn)
        layout.addLayout(synth_layout)

        # 录音按钮
        record_btn = QPushButton("开始录音（8秒）")
        record_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c; color: white; padding: 12px;
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        record_btn.clicked.connect(self._on_record)
        layout.addWidget(record_btn)

        layout.addStretch()

    def _connect_signals(self):
        self._voice.recognition_result.connect(self._on_result)
        self._voice.recognition_status.connect(self._on_status)
        self._voice.error_occurred.connect(self._on_error)

    def _on_switch_voice(self):
        name = self._voice.next_voice()
        self._voice_label.setText(self._voice.current_voice_label())
        self._status_label.setText(f"已切换到 {name}")

    def _on_record(self):
        self._result_area.clear()
        self._status_label.setText("正在录音...")
        self._voice.start_listening(timeout=8.0)

    def _on_speak(self):
        text = self._synth_input.text().strip()
        if text:
            self._status_label.setText("正在朗读...")
            self._voice.speak(text)

    def _on_result(self, text: str):
        self._result_area.append(f"[识别] {text}")

    def _on_status(self, status: str):
        self._status_label.setText(status)

    def _on_error(self, error: str):
        self._result_area.append(f"[错误] {error}")
        self._status_label.setText("错误")


# ═══════════ 快捷测试 ═══════════

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    vi = VoiceInterface()
    vi.recognition_result.connect(lambda t: print(f"识别: {t}"))
    vi.error_occurred.connect(lambda e: print(f"错误: {e}"))

    print("开始语音识别（8秒）...")
    vi.start_listening(timeout=8.0)
    sys.exit(app.exec_())
