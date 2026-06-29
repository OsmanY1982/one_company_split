# `iqra/modules/intelligence/ai_chat_window/_voice.py`

> 路径：`iqra/modules/intelligence/ai_chat_window/_voice.py` | 行数：198


---


```python
# ── 语音输入 + 朗读 Mixin ──
import re
import subprocess
import threading

from PyQt5.QtCore import QTimer

from modules.intelligence.session_context import session_ctx
from modules.intelligence.voice_interface import VoiceInterface


class _VoiceMixin:
    """语音输入 / 朗读 / closeEvent"""

    # ─── 语音输入 ───
    def _toggle_voice_input(self):
        if self._voice_recording:
            self._stop_voice_input()
        else:
            self._start_voice_input()

    def _start_voice_input(self):
        if self._voice_recording:
            return

        if self._voice_input is None:
            self._voice_input = VoiceInterface(stt_engine="apple")
            self._voice_input.recognition_result.connect(self._on_voice_input_result)
            self._voice_input.recognition_status.connect(self._on_voice_input_status)
            self._voice_input.error_occurred.connect(self._on_voice_input_error)

        self._voice_recording = True
        self.btn_mic.setText("⏹")
        self.btn_mic.setToolTip("录音中…点击停止")
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background: rgba(220,60,50,60);
                color: #ff6666;
                border: 1px solid rgba(255,80,70,120);
                border-radius: 18px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(240,70,60,80); }
        """)

        self.ai_chat.append(
            '<p style="color:#ffaa44;font-size:10px;">🎤 语音输入中…请说话（最长6秒）</p>'
        )

        try:
            self._voice_input.start_listening(timeout=6.0)
        except Exception as e:
            self._on_voice_input_error(f"启动语音输入失败: {e}")

    def _stop_voice_input(self):
        self._voice_recording = False
        self.btn_mic.setText("🎤")
        self.btn_mic.setToolTip("点击开始语音输入（6秒超时自动发送）")
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,45);
                color: #99bbee;
                border: 1px solid rgba(100,140,200,70);
                border-radius: 18px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(130,170,230,70); }
        """)
        if self._voice_input:
            try:
                self._voice_input.stop_listening()
            except Exception:
                import traceback; traceback.print_exc()

    def _on_voice_input_result(self, text: str):
        text = text.strip()
        if not text:
            return
        self._stop_voice_input()
        self.ai_chat.append(
            f'<p style="color:#88aa88;font-size:10px;">🎤 识别: {text}</p>'
        )
        self.ai_input.setText(text)
        self._ai_send()

    def _on_voice_input_status(self, status: str):
        pass

    def _on_voice_input_error(self, error: str):
        self._stop_voice_input()
        self.ai_chat.append(
            f'<p style="color:#ff6644;font-size:10px;">语音输入错误: {error}</p>'
        )

    # ─── 朗读 ───
    def _on_speak_clicked(self):
        print("[Speak] _on_speak_clicked called", flush=True)
        try:
            self._do_speak()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Speak] 按钮回调异常: {e}", flush=True)
            try:
                self.ai_chat.append(
                    f'<p style="color:#ff6644;font-size:10px;">[系统] 朗读失败: {e}</p>'
                )
            except Exception:
                import traceback; traceback.print_exc()

    def _do_speak(self):
        last_ai = None
        for msg in reversed(self._messages):
            if msg.get("role") == "assistant":
                last_ai = msg["content"]
                break
        if not last_ai:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 没有可朗读的 AI 回复</p>'
            )
            return

        self._terminate_speak()

        clean_text = re.sub(r'<[^>]+>', '', last_ai).strip()

        self._set_speak_button("朗读中...", """
            QPushButton {
                background: rgba(255,180,60,60); color: #ffaa44;
                border: 1px solid rgba(255,180,60,100); border-radius: 16px;
                padding: 6px 14px; font-size: 11px; font-weight: 600;
            }
        """)

        def _run():
            try:
                proc = subprocess.Popen(
                    ['say', '-v', 'Tingting'],
                    stdin=subprocess.PIPE,
                )
                self._speak_process = proc
                proc.communicate(input=clean_text.encode('utf-8'))
            except Exception as e:
                print(f"[Speak] 朗读失败: {e}")
            QTimer.singleShot(0, self._restore_speak_button)

        threading.Thread(target=_run, daemon=True).start()

    def _set_speak_button(self, text, style):
        self.btn_speak.setText(text)
        self.btn_speak.setStyleSheet(style)
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

    def _restore_speak_button(self):
        self.btn_speak.setText("朗读")
        self.btn_speak.setStyleSheet("""
            QPushButton {
                background: rgba(80,200,160,40); color: #88ffcc;
                border: 1px solid rgba(80,220,160,60); border-radius: 16px;
                padding: 6px 14px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(100,230,180,65); }
        """)

    def _terminate_speak(self):
        if self._speak_process and self._speak_process.poll() is None:
            try:
                self._speak_process.terminate()
                self._speak_process.wait(timeout=2)
            except Exception:
                try:
                    self._speak_process.kill()
                except Exception:
                    pass
        self._speak_process = None

    def closeEvent(self, event):
        self._terminate_speak()
        if self._messages and self._bridge:
            try:
                self._bridge.save_session(self._messages, self._current_session_id)
            except Exception as e:
                print(f"[AIChatWindow] closeEvent 保存失败: {e}")
        if hasattr(self, '_session_manager'):
            try:
                self._session_manager._load_sessions()
            except Exception:
                import traceback; traceback.print_exc()
        session_ctx.unregister_window(self)
        session_ctx.remove_message_listener(self._on_external_message)
        if self._voice_input:
            try:
                self._voice_input.stop_listening()
            except Exception:
                import traceback; traceback.print_exc()
        from PyQt5.QtWidgets import QWidget
        QWidget.closeEvent(self, event)

```
