# ── 对话流式 Mixin ──
import sys
import traceback
from datetime import datetime

from core.modules.intelligence.offline_analyzer import offline_analysis


class _ChatStreamMixin:
    """发送 / 流式 / 重新生成 / 外部消息"""

    def _build_prompt_with_attachments(self, text: str) -> str:
        if not self._attached_files:
            return text
        file_contexts = []
        for fp, bn in self._attached_files:
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(4000)
                file_contexts.append(f"[文件: {bn}]\n{content}")
            except Exception:
                file_contexts.append(f"[文件: {bn}] (二进制/不可读)")
        if file_contexts:
            return text + "\n\n--- 附件内容 ---\n" + "\n\n".join(file_contexts)
        return text

    def _ai_send(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        if self._streaming:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 请等待当前回复完成</p>'
            )
            return

        self.ai_input.clear()
        self._append_user_msg(text)
        self._messages.append({"role": "user", "content": text})
        if self._bridge:
            try:
                self._bridge.append_message("user", text, self._current_session_id)
                self._suppress_self_notify = True
                self._bridge.notify_message_added()
                self._suppress_self_notify = False
            except Exception:
                traceback.print_exc()

        prompt = self._build_prompt_with_attachments(text)
        self._clear_file_pills()

        # ── 优先级 1: AgentBridge 流式输出 ──
        if self._bridge is not None and hasattr(self._bridge, "chat_stream"):
            try:
                print(f"[DIAG][{datetime.now().strftime('%H:%M:%S')}] AIChatWindow._ai_send — calling bridge.chat_stream()...", flush=True)
                self._stream_begin()
                self._bridge.chat_stream(
                    prompt,
                    on_chunk=self._stream_chunk,
                    on_done=self._stream_done,
                    on_tool=self._stream_tool,
                    on_error=self._stream_error,
                )
                print(f"[DIAG][{datetime.now().strftime('%H:%M:%S')}] AIChatWindow._ai_send — bridge.chat_stream() returned (thread started)", flush=True)
                return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 流式启动失败 ({e})，回退同步模式</p>'
                )

        # ── 优先级 2: AgentBridge 同步 chat ──
        if self._bridge is not None:
            try:
                reply = ""
                if hasattr(self._bridge, "chat"):
                    reply = self._bridge.chat(prompt)
                if reply:
                    self._append_ai_msg(reply)
                    self._messages.append({"role": "assistant", "content": reply})
                    if self._bridge:
                        try:
                            self._bridge.append_message("assistant", reply, self._current_session_id)
                            self._suppress_self_notify = True
                            self._bridge.notify_message_added()
                            self._suppress_self_notify = False
                        except Exception:
                            pass
                    return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] AgentBridge 调用失败 ({e})，回退离线分析</p>'
                )

        # ── 优先级 3: 离线分析兜底 ──
        try:
            offline_resp = offline_analysis(prompt)
            self._append_ai_msg(offline_resp, offline=True)
            self._messages.append({"role": "assistant", "content": offline_resp})
        except Exception as e:
            self.ai_chat.append(f'<p style="color:#ff6666;">错误: {e}</p>')
            traceback.print_exc()

    def _append_user_msg(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        mid = self._next_msg_id
        self._next_msg_id += 1
        self.ai_chat.append(
            f'<p style="color:#ffaa44;font-weight:700;">[{now}] 你:</p>'
            f'<p style="color:#ddccff;">{text}</p>'
            f'{self._msg_action_row(mid, text)}'
        )

    def _append_ai_msg(self, text, offline=False):
        now = datetime.now().strftime("%H:%M:%S")
        tag = "AI(离线)" if offline else "AI"
        mid = self._next_msg_id
        self._next_msg_id += 1
        self.ai_chat.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] {tag}:</p>'
            f'<p style="color:#ccaaff;">{text}</p>'
            f'{self._msg_action_row(mid, text)}'
        )

    # ─── 流式输出方法 ───
    def _stream_begin(self):
        self._streaming = True
        self._stream_buffer = ""
        self._stream_finalized = False
        self._enter_streaming_ui()
        now = datetime.now().strftime("%H:%M:%S")
        self.ai_chat.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
        )
        self.ai_chat.append(
            f'<p style="color:#ccaaff;">▌</p>'
        )
        cursor = self.ai_chat.textCursor()
        cursor.movePosition(cursor.End)
        self._stream_block = cursor.blockNumber()

    def _stream_chunk(self, chunk: str):
        print(f"[DIAG][{datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_chunk len={len(chunk)}", flush=True)
        if self._bridge and getattr(self._bridge, '_stream_aborted', False):
            return
        if self._stream_block <= 0:
            return
        self._stream_buffer += chunk
        doc = self.ai_chat.document()
        block = doc.findBlockByNumber(self._stream_block)
        if not block.isValid():
            return
        cursor = self.ai_chat.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        cursor.removeSelectedText()
        escaped = self._stream_buffer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        cursor.insertHtml(f'<p style="color:#ccaaff;">{escaped}▌</p>')
        sb = self.ai_chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _stream_tool(self, tool_name: str, status: str):
        color = {"running": "#99bbee", "OK": "#44cc88", "Failed": "#ff6644"}.get(status, "#888")
        icon = {"running": "⚙", "OK": "✓", "Failed": "✗"}.get(status, "?")
        if tool_name in ("web_scrape", "batch_scrape"):
            icon = {"running": "🕷", "OK": "🌐", "Failed": "⚠"}.get(status, "🕸")
        self.ai_chat.append(
            f'<p style="color:{color};font-size:10px;margin:0;">{icon} 工具: {tool_name} [{status}]</p>'
        )
        self._messages.append({"role": "tool", "content": f"{icon} 工具: {tool_name} [{status}]"})

    def _stream_done(self, full_text: str):
        print(f"[DIAG][{datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_done len={len(full_text)}", flush=True)
        if getattr(self, '_stream_finalized', False):
            return
        self._stream_finalized = True
        self._streaming = False
        self._exit_streaming_ui()
        if self._stream_block <= 0:
            return
        doc = self.ai_chat.document()
        block = doc.findBlockByNumber(self._stream_block)
        if not block.isValid():
            return
        cursor = self.ai_chat.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        cursor.removeSelectedText()
        escaped = full_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        cancelled = "[用户取消]" in full_text
        if not cancelled:
            mid = self._next_msg_id
            self._next_msg_id += 1
            cursor.insertHtml(f'<p style="color:#ccaaff;">{escaped}</p>{self._msg_action_row(mid, full_text)}')
        else:
            cursor.insertHtml(f'<p style="color:#ffaa44;">{escaped}</p>')
        self._stream_buffer = ""
        if not cancelled:
            self._messages.append({"role": "assistant", "content": full_text})
            if self._bridge:
                try:
                    self._bridge.append_message("assistant", full_text, self._current_session_id)
                    self._suppress_self_notify = True
                    self._bridge.notify_message_added()
                    self._suppress_self_notify = False
                except Exception:
                    traceback.print_exc()

    def _stream_error(self, err_msg: str):
        print(f"[DIAG][{datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_error: {err_msg}", flush=True)
        self._streaming = False
        self._exit_streaming_ui()
        self.ai_chat.append(f'<p style="color:#ff6644;font-size:10px;">{err_msg}</p>')
        self._stream_buffer = ""

    def _on_stop_generation(self):
        self._streaming = False
        if self._bridge:
            self._bridge.cancel()
        self._exit_streaming_ui()

    def _enter_streaming_ui(self):
        self.btn_send.setVisible(False)
        self.btn_stop.setVisible(True)
        self.lbl_status.setStyleSheet("color: #ffaa44; font-size: 11px; background: transparent;")

    def _exit_streaming_ui(self):
        self.btn_stop.setVisible(False)
        self.btn_send.setVisible(True)
        status_color = "#44cc88" if self._bridge is not None else "#ff6644"
        self.lbl_status.setStyleSheet(f"color: {status_color}; font-size: 11px; background: transparent;")

    def _on_regenerate(self):
        if not self._messages:
            return
        last_user_msg = None
        cut_idx = 0
        for i in range(len(self._messages) - 1, -1, -1):
            if self._messages[i]["role"] == "user":
                last_user_msg = self._messages[i]["content"]
                cut_idx = i
                break
        if last_user_msg is None:
            return
        self._messages = self._messages[:cut_idx]
        self.ai_chat.clear()
        for msg in self._messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                self._append_user_msg(content)
            elif role == "assistant":
                self._append_ai_msg(content)
            elif role == "tool":
                self.ai_chat.append(
                    f'<p style="color:#888;font-size:10px;margin:0;">{content}</p>'
                )
        self.ai_input.setText(last_user_msg)
        self._ai_send()

    def _on_external_message(self, session_id: str, role: str, content: str):
        if self._suppress_self_notify:
            return
        if session_id != self._current_session_id:
            return
        if role == "user":
            self._messages.append({"role": "user", "content": content})
            self._append_user_msg(content)
        elif role == "assistant":
            self._messages.append({"role": "assistant", "content": content})
            self._append_ai_msg(content)
