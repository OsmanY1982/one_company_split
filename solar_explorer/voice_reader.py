# -*- coding: utf-8 -*-
"""
语音朗读模块 — macOS TTS (say)
非阻塞朗读，支持中文语音 Tingting
"""
import subprocess
import threading

CHINESE_VOICE = "Tingting"
# 备选: "Tingting" (普通话女声), "Sin-ji" (粤语)


class VoiceReader:
    """系统 TTS 朗读器 — 非阻塞"""

    def __init__(self):
        self._proc = None
        self._state = "ready"  # ready / speaking / done

    @property
    def is_speaking(self):
        return self._state == "speaking"

    @property
    def state(self):
        return self._state

    def speak(self, text, lang="zh-CN"):
        """朗读文本（非阻塞）"""
        if not text or not text.strip():
            return
        self.stop()
        self._state = "speaking"

        def _run():
            try:
                self._proc = subprocess.Popen(
                    ["say", "-v", CHINESE_VOICE, text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._proc.wait()
                self._state = "done"
            except Exception:
                self._state = "ready"

        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        """停止朗读"""
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=0.5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._state = "ready"
