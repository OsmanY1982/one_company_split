"""AgentBridge 后台 Worker 类（从 agent_bridge.py 拆出）"""

from PyQt5.QtCore import QObject, pyqtSignal

# ── iqra 引擎 ──
from iqra.core.agent_loop import AgentLoop, AgentResult
from iqra.core.chat_engine import ChatEngine


class _TaskWorker(QObject):
    """在 QThread 中执行 AgentLoop.run()"""

    finished = pyqtSignal(object)  # AgentResult

    def __init__(self, agent_loop: AgentLoop, message: str):
        super().__init__()
        self._agent_loop = agent_loop
        self._message = message

    def run(self):
        try:
            result = self._agent_loop.run(self._message)
            self.finished.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(AgentResult(
                success=False,
                summary=f"AgentLoop 执行异常: {e}",
                steps_taken=0,
                tools_called=[],
                errors=[str(e)],
                events=[],
                duration_seconds=0,
            ))


class _StreamWorker(QObject):
    """在 QThread 中执行 ChatEngine.chat_stream()，通过信号逐块回调到主线程"""

    chunk_ready = pyqtSignal(str)      # 文本块
    tool_event = pyqtSignal(str, str)  # (tool_name, status: running/OK/Failed)
    stream_done = pyqtSignal(str)      # (full_text)
    stream_error = pyqtSignal(str)     # (error_message)
    finished = pyqtSignal()

    def __init__(self, engine: ChatEngine, message: str, bridge: 'AgentBridge' = None):
        super().__init__()
        self._engine = engine
        self._message = message
        self._bridge = bridge

    def run(self):
        accumulated = ""
        import sys, datetime
        print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] StreamWorker.run() START — engine={type(self._engine).__name__}, msg={self._message[:50]}", flush=True)
        try:
            for chunk in self._engine.chat_stream(self._message):
                # 用户取消检查
                if self._bridge and self._bridge._stream_cancelled:
                    accumulated += "\n[用户取消]"
                    self.stream_done.emit(accumulated)
                    self.finished.emit()
                    return

                # 工具调用标记
                if "Calling tool:" in chunk:
                    name = chunk.split("Calling tool:")[1].split("...")[0].strip()
                    self.tool_event.emit(name, "running")
                elif ": OK]" in chunk and not chunk.startswith('{"'):
                    name = chunk[1:].split(":")[0].strip()
                    self.tool_event.emit(name, "OK")
                elif ": Failed]" in chunk and not chunk.startswith('{"'):
                    name = chunk[1:].split(":")[0].strip()
                    self.tool_event.emit(name, "Failed")

                # 跳过 usage JSON
                if chunk.startswith('{"usage"'):
                    continue

                accumulated += chunk
                self.chunk_ready.emit(chunk)

            self.stream_done.emit(accumulated)

        except Exception as e:
            import traceback
            traceback.print_exc()
            err = f"\n[流式传输中断: {e}]"
            accumulated += err
            self.stream_error.emit(err)
            self.stream_done.emit(accumulated)

        self.finished.emit()
