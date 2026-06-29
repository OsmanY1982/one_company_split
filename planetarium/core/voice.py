"""
语音输入模块 — 基于 faster-whisper 离线识别
支持中文/英文，纯本地运行，无需网络
降级方案：文本输入替代语音输入
"""
import traceback
import subprocess
import os
import tempfile
import wave
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt


# ─── 可用后端检测 ───
def _check_faster_whisper():
    try:
        import faster_whisper
        return True
    except ImportError:
        return False

def _check_whisper():
    try:
        import whisper
        return True
    except ImportError:
        return False

def _check_speech_recognition():
    try:
        import speech_recognition
        return True
    except ImportError:
        return False


class VoiceListener(QThread):
    """后台语音监听线程 — 优先 faster-whisper，降级 speech_recognition"""
    result_ready = pyqtSignal(str)   # 识别结果
    status_changed = pyqtSignal(str, str)  # (状态, 细节)

    def __init__(self):
        super().__init__()
        self._running = False
        self._language = "zh"
        self._model = None
        self._preferred_backend = self._detect_backend()

    def _detect_backend(self):
        if _check_faster_whisper():
            return "faster-whisper"
        if _check_whisper():
            return "whisper"
        if _check_speech_recognition():
            return "speech_recognition"
        return "none"

    def run(self):
        self._running = True
        self.status_changed.emit("listening", f"后端: {self._preferred_backend}")

        try:
            if self._preferred_backend == "faster-whisper":
                result = self._recognize_faster_whisper()
            elif self._preferred_backend == "whisper":
                result = self._recognize_whisper()
            elif self._preferred_backend == "speech_recognition":
                result = self._recognize_with_sr()
            else:
                self.status_changed.emit("error", "无可用的语音识别后端")
                return

            if result:
                self.result_ready.emit(result)
                self.status_changed.emit("done", result)
            else:
                self.status_changed.emit("fallback", "未识别到语音，请尝试文字输入")
        except Exception as e:
            self.status_changed.emit("error", str(e))
            traceback.print_exc()

        self._running = False

    # ─── faster-whisper 离线识别 ───
    def _recognize_faster_whisper(self) -> str:
        """使用 faster-whisper 进行本地离线语音识别"""
        from deps.install_deps import ensure
        try:
            import faster_whisper
        except ImportError:
            ensure("faster-whisper")
            import faster_whisper

        # 录制音频
        self.status_changed.emit("recording", "正在聆听...")
        audio_path = self._record_audio(duration=6, sample_rate=16000)
        if not audio_path:
            return ""

        # 加载模型
        self.status_changed.emit("transcribing", "正在识别...")
        if self._model is None:
            try:
                model_size = "small"  # small 对中文较好，tiny 更快但精度低
                self._model = faster_whisper.WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                    num_workers=2,
                )
            except Exception:
                # 降级到 tiny
                self._model = faster_whisper.WhisperModel(
                    "tiny",
                    device="cpu",
                    compute_type="int8",
                    num_workers=2,
                )

        segments, info = self._model.transcribe(
            audio_path,
            language=self._language,
            beam_size=5,
            vad_filter=True,
        )

        text_parts = []
        for seg in segments:
            if seg.text.strip():
                text_parts.append(seg.text.strip())

        # 清理临时文件
        try:
            os.unlink(audio_path)
        except Exception:
            pass

        return " ".join(text_parts)

    # ─── openai-whisper 离线识别 ───
    def _recognize_whisper(self) -> str:
        """使用 openai-whisper 进行本地离线语音识别"""
        from deps.install_deps import ensure
        try:
            import whisper
        except ImportError:
            ensure("openai-whisper")
            import whisper

        self.status_changed.emit("recording", "正在聆听...")
        audio_path = self._record_audio(duration=6, sample_rate=16000)
        if not audio_path:
            return ""

        self.status_changed.emit("transcribing", "正在识别...")
        if self._model is None:
            self._model = whisper.load_model("small")

        result = self._model.transcribe(
            audio_path,
            language=self._language,
            fp16=False,
        )

        try:
            os.unlink(audio_path)
        except Exception:
            pass

        return result.get("text", "").strip()

    # ─── speech_recognition 识别（需要网络） ───
    def _recognize_with_sr(self) -> str:
        """使用 speech_recognition 库 + 系统麦克风"""
        from deps.install_deps import ensure
        try:
            import speech_recognition as sr
        except ImportError:
            ensure("speech_recognition")
            ensure("pyaudio")
            import speech_recognition as sr

        r = sr.Recognizer()
        self.status_changed.emit("recording", "正在聆听...")
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=8)

        self.status_changed.emit("transcribing", "识别中 (Google)...")
        try:
            text = r.recognize_google(audio, language="zh-CN")
            return text
        except sr.UnknownValueError:
            try:
                text = r.recognize_google(audio, language="en-US")
                return text
            except Exception:
                return ""
        except sr.RequestError:
            try:
                text = r.recognize_sphinx(audio, language="zh-CN")
                return text
            except Exception:
                return ""

    # ─── 音频录制 ───
    def _record_audio(self, duration=6, sample_rate=16000) -> str:
        """用 pyaudio 录制音频并保存为临时 wav"""
        try:
            import pyaudio
        except ImportError:
            self.status_changed.emit("error", "pyaudio 未安装，请运行: pip install pyaudio")
            return ""

        try:
            import wave
        except ImportError:
            wave = None

        p = pyaudio.PyAudio()
        chunk = 1024
        fmt = pyaudio.paInt16
        channels = 1

        try:
            stream = p.open(
                format=fmt,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk,
            )
        except Exception as e:
            p.terminate()
            self.status_changed.emit("error", f"无法打开麦克风: {e}")
            return ""

        frames = []
        for _ in range(0, int(sample_rate / chunk * duration)):
            if not self._running:
                break
            try:
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
            except Exception:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

        if not frames:
            return ""

        # 写入临时 wav
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="voice_")
        os.close(fd)
        wf = wave.open(path, "wb")
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(fmt))
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
        wf.close()

        return path

    def stop(self):
        self._running = False
        self.status_changed.emit("idle", "")


# ─── 文字输入回退对话框 ───
class TextFallbackDialog(QDialog):
    """当语音识别失败时，弹出文本输入框作为替代"""
    text_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文字输入 · CREW")
        self.setMinimumSize(500, 200)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0414, stop:1 #1a0a2e);
                border: 1px solid rgba(170,80,255,40); border-radius: 12px;
            }
            QLabel { color: #bb99dd; background: transparent; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        label = QLabel("语音未识别到内容，请在此输入：")
        label.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(label)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("输入您想说的话...")
        self._text_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #ddccff;
                border: 1px solid rgba(170,80,255,35); border-radius: 8px;
                padding: 10px; font-size: 13px;
            }
        """)
        layout.addWidget(self._text_edit, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(40,30,60,150); color: #8877aa;
                border: 1px solid rgba(128,80,210,40); border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: rgba(60,50,80,180); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        submit_btn = QPushButton("提交")
        submit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(170,80,255,30); color: #ddaaff;
                border: 1px solid rgba(170,80,255,50); border-radius: 6px;
                padding: 8px 20px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(170,80,255,60); color: #ffffff; }
        """)
        submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(submit_btn)
        layout.addLayout(btn_row)

    def _on_submit(self):
        text = self._text_edit.toPlainText().strip()
        if text:
            self.text_submitted.emit(text)
            self.accept()


# ─── TTS 语音播报 ───
def speak(text: str, voice: str = "Tingting", rate: int = 200):
    """使用 macOS say 命令进行中文语音播报"""
    try:
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), text],
            capture_output=True,
            timeout=15,
        )
    except Exception:
        pass
