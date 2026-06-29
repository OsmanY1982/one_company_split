# -*- coding: utf-8 -*-
"""
Whisper 语音识别引擎 — faster-whisper large-v3 + sounddevice
极致中文准确率，纯本地离线
"""

import numpy as np
import os
import queue
import sys
import threading
import time
from typing import Optional, Callable

from PyQt5.QtCore import QThread, pyqtSignal


# ── 安全打印：stdout 断开时静默（launchctl 后台运行场景）──
def _wprint(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except OSError:
        pass


# ═══════════ 配置 ═══════════

SAMPLE_RATE = 16000
BLOCK_SIZE = 512         # 每次读取的采样点数
VAD_SILENCE_SEC = 0.6    # 静音持续多久判定为说话结束
VAD_THRESHOLD = 0.015    # RMS 能量阈值（16-bit PCM 归一化到 [-1,1]）

# 当设置了 STT_STDIN_AUDIO=1 环境变量时，从 stdin 读取 float32 音频而非 sounddevice
# 但 stdin 必须是管道（非 TTY），否则回退到 sounddevice
_STDIN_AUDIO = os.environ.get("STT_STDIN_AUDIO", "").strip() == "1"
if _STDIN_AUDIO and sys.stdin.isatty():
    _wprint("[Whisper] STT_STDIN_AUDIO=1 但 stdin 无管道，回退到 sounddevice", flush=True)
    _STDIN_AUDIO = False


# ═══════════ 唤醒词 ═══════════

WAKE_WORDS = ["球球", "星仔", "球球在吗", "小助手", "助理"]


# ═══════════ Whisper 识别器 ═══════════

class WhisperRecognizer(QThread):
    """基于 faster-whisper 的持续语音识别"""

    text_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    wake_detected = pyqtSignal()  # 唤醒词检测到

    def __init__(self, model_size: str = "large-v3", device: str = "auto"):
        super().__init__()
        self.model_size = model_size
        self.device = device
        self._running = True
        self._wake_mode = False      # 是否处于唤醒监听模式
        self._listening = False       # 是否正在监听
        self._audio_queue: queue.Queue = queue.Queue()
        self._model: Optional[object] = None
        self._command_busy = False    # 正在处理命令中（暂停唤醒循环）

    # ── 模型加载 ──

    def _ensure_model(self):
        if self._model is not None:
            return
        _wprint("[Whisper] 开始加载模型...", flush=True)
        self.status_changed.emit("加载 Whisper 模型...")
        from faster_whisper import WhisperModel

        if self.device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device = "cpu"  # faster-whisper 不支持 mps，但 torch 加速可用
                else:
                    device = "cpu"
                _wprint(f"[Whisper] 设备: {device}", flush=True)
            except ImportError:
                device = "cpu"
                _wprint("[Whisper] torch 未安装，使用 CPU", flush=True)
        else:
            device = self.device

        compute = "int8" if device == "cpu" else "float16"
        _wprint(f"[Whisper] 加载模型: {self.model_size}, device={device}, compute={compute}", flush=True)
        self._model = WhisperModel(
            self.model_size, device=device, compute_type=compute
        )
        _wprint("[Whisper] 模型加载完成", flush=True)
        self.status_changed.emit("Whisper 模型就绪")

    # ── 录音 ──

    def _record_loop(self):
        """后台录音线程"""
        if _STDIN_AUDIO:
            self._stdin_record_loop()
        else:
            self._sd_record_loop()

    def _stdin_record_loop(self):
        """从 stdin 读取 float32 音频（由外部 mic_capture 进程提供）"""
        _wprint("[Whisper] stdin 录音线程启动", flush=True)
        self.status_changed.emit("麦克风已开启（管道模式）")
        bytes_per_block = BLOCK_SIZE * 4  # float32 = 4 bytes
        try:
            while self._running:
                raw = sys.stdin.buffer.read(bytes_per_block)
                if not raw or len(raw) < bytes_per_block:
                    time.sleep(0.01)
                    continue
                block = np.frombuffer(raw, dtype=np.float32).reshape(-1, 1)
                if self._listening:
                    self._audio_queue.put(block)
        except Exception as e:
            _wprint(f"[Whisper] stdin 录音错误: {e}", flush=True)
            self.error_occurred.emit(f"stdin 录音错误: {e}")

    def _sd_record_loop(self):
        """后台录音线程（sounddevice）"""
        _wprint("[Whisper] 录音线程启动", flush=True)
        try:
            import sounddevice as sd
        except ImportError:
            _wprint("[Whisper] 缺少 sounddevice 库", flush=True)
            self.error_occurred.emit("缺少 sounddevice 库，请先安装: pip install sounddevice")
            return

        try:
            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=BLOCK_SIZE,
                callback=self._audio_callback,
            )
            stream.start()
            _wprint("[Whisper] 麦克风已开启", flush=True)
            self.status_changed.emit("麦克风已开启")

            while self._running and stream.active:
                time.sleep(0.1)

            stream.stop()
            stream.close()
        except Exception as e:
            _wprint(f"[Whisper] 麦克风错误: {e}", flush=True)
            self.error_occurred.emit(f"麦克风错误: {e}")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            return
        if self._listening:
            self._audio_queue.put(indata.copy())

    # ── VAD（语音活动检测） ──

    def _is_speech(self, audio: np.ndarray) -> bool:
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > VAD_THRESHOLD

    # ── 录音片段 ──

    def _record_segment(self, timeout: float, pre_buffer_sec: float = 0.3) -> np.ndarray:
        """录制一段语音，以静音 VAD_SILENCE_SEC 秒作为结束条件"""
        self._audio_queue.queue.clear()
        self._listening = True

        pre_blocks = int(pre_buffer_sec * SAMPLE_RATE / BLOCK_SIZE)
        pre_buffer = []

        frames = []
        silence_frames = 0
        silence_threshold = int(VAD_SILENCE_SEC * SAMPLE_RATE / BLOCK_SIZE)
        max_blocks = int(timeout * SAMPLE_RATE / BLOCK_SIZE)
        total = 0

        while total < max_blocks and self._running:
            try:
                block = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                silence_frames += 1
                if silence_frames > silence_threshold and frames:
                    break
                continue

            if len(pre_buffer) < pre_blocks:
                pre_buffer.append(block)
                total += 1
                continue

            frames.append(block)
            total += 1

            if self._is_speech(block):
                silence_frames = 0
            else:
                silence_frames += 1
                if silence_frames > silence_threshold and frames:
                    break

        self._listening = False

        if not frames:
            # 只有预缓冲 → 尝试识别预缓冲
            if pre_buffer:
                result = np.concatenate(pre_buffer, axis=0)
            else:
                result = np.zeros((0, 1), dtype=np.float32)
        else:
            all_frames = pre_buffer + frames
            result = np.concatenate(all_frames, axis=0)

        return result.flatten()

    # ── 语音转文字 ──

    def _transcribe(self, audio: np.ndarray) -> str:
        """使用 Whisper 转写"""
        self._ensure_model()

        if len(audio) < SAMPLE_RATE * 0.3:  # 少于 0.3 秒的音频跳过
            return ""

        segments, _ = self._model.transcribe(
            audio,
            language="zh",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250,
            ),
        )

        texts = [seg.text.strip() for seg in segments]
        return "".join(texts)

    # ── 唤醒模式循环 ──

    def _wake_loop(self):
        """持续监听唤醒词（纯唤醒检测，命令由外部触发）"""
        _wprint("[Whisper] 唤醒循环启动", flush=True)
        self.status_changed.emit("唤醒监听中...")

        loop_count = 0
        while self._running and self._wake_mode:
            # 正在处理命令时暂停唤醒检测
            if self._command_busy:
                time.sleep(0.2)
                continue

            try:
                audio = self._record_segment(timeout=4.0, pre_buffer_sec=0.2)
            except Exception as e:
                _wprint(f"[Whisper] 录音异常: {e}", flush=True)
                self.error_occurred.emit(f"录音异常: {e}")
                time.sleep(1)
                continue

            loop_count += 1
            if len(audio) < SAMPLE_RATE * 0.5:
                if loop_count % 5 == 0:
                    _wprint(f"[Whisper] 唤醒循环 #{loop_count}: 音频太短 ({len(audio)/SAMPLE_RATE:.1f}s)", flush=True)
                continue

            # 调试：输出音频能量
            rms = float(np.sqrt(np.mean(audio ** 2)))
            if loop_count % 10 == 0:
                _wprint(f"[Whisper] 循环 #{loop_count}: 音频 {len(audio)/SAMPLE_RATE:.1f}s, RMS={rms:.4f}", flush=True)

            text = self._transcribe(audio)
            if not text:
                if loop_count % 5 == 0:
                    _wprint(f"[Whisper] 唤醒循环 #{loop_count}: 无识别文本 (RMS={rms:.4f})", flush=True)
                continue

            _wprint(f"[Whisper] 识别到: '{text}'", flush=True)
            for ww in WAKE_WORDS:
                if ww in text:
                    _wprint(f"[Whisper] 命中唤醒词: {ww}", flush=True)
                    self.status_changed.emit(f"唤醒: {text}")
                    self._command_busy = True  # 暂停唤醒循环
                    self.wake_detected.emit()
                    break

    def listen_for_command(self):
        """唤醒后，由外部调用以录制命令（应在"在呢"语音播放完毕后调用）"""
        self.status_changed.emit("请说指令...")

        try:
            audio = self._record_segment(timeout=8.0, pre_buffer_sec=0.3)
        except Exception as e:
            self.error_occurred.emit(f"录音异常: {e}")
            self._command_busy = False  # 释放
            return

        if len(audio) < SAMPLE_RATE * 0.3:
            self._command_busy = False
            return

        text = self._transcribe(audio)
        if text:
            self.text_ready.emit(text)

    def resume_wake(self):
        """命令处理完毕，恢复唤醒监听"""
        self._command_busy = False
        self.status_changed.emit("唤醒监听中...")

    # ── 单次识别（兼容旧接口） ──

    def listen_once(self, timeout: float = 6.0) -> str:
        """单次录音+识别，兼容 AppleSpeechRecognizer 的调用方式"""
        self._ensure_model()
        try:
            audio = self._record_segment(timeout=timeout, pre_buffer_sec=0.2)
        except Exception as e:
            self.error_occurred.emit(f"录音: {e}")
            return ""

        if len(audio) < SAMPLE_RATE * 0.3:
            return ""

        return self._transcribe(audio)

    # ── 线程控制 ──

    def run(self):
        """主线程入口"""
        _wprint("[Whisper] 线程启动", flush=True)
        try:
            self._ensure_model()
        except Exception as e:
            import traceback
            _wprint(f"[Whisper] 模型加载失败: {e}", flush=True)
            try:
                traceback.print_exc()
            except OSError:
                pass
            self.error_occurred.emit(f"模型加载失败: {e}")
            return

        if self._wake_mode:
            # 启动后台录音 + 唤醒循环
            recorder_thread = threading.Thread(
                target=self._record_loop, daemon=True
            )
            recorder_thread.start()
            self._wake_loop()
        else:
            # 兼容模式：单次识别
            # 启动录音线程
            recorder_thread = threading.Thread(
                target=self._record_loop, daemon=True
            )
            recorder_thread.start()

            while self._running:
                text = self.listen_once(timeout=6.0)
                if text:
                    self.text_ready.emit(text)
                else:
                    self.error_occurred.emit("未能识别到语音")
                if not self._running:
                    break

    def set_wake_mode(self, enabled: bool):
        self._wake_mode = enabled

    def stop(self):
        self._running = False
        self._listening = False
        self._wake_mode = False
