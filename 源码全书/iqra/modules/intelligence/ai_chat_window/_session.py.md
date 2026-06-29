# `iqra/modules/intelligence/ai_chat_window/_session.py`

> 路径：`iqra/modules/intelligence/ai_chat_window/_session.py` | 行数：90


---


```python
# ── 会话切换 Mixin ──
import copy
from datetime import datetime

from modules.intelligence.session_context import session_ctx


class _SessionMixin:
    """会话选择 / 新建 / 复制 / 切换"""

    # ─── 会话切换 ───
    def _on_session_selected(self, session_id: str, title: str):
        self._switch_to_session(session_id, title)

    def _on_new_session(self):
        new_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._switch_to_session(new_id, "新对话")
        if self._bridge:
            try:
                self._bridge.save_session([], new_id)
            except Exception:
                import traceback; traceback.print_exc()
        self._session_manager._load_sessions()

    def _on_session_copy(self, session_id: str):
        if not self._bridge:
            return
        try:
            msgs = self._bridge.load_session(session_id)
            if not msgs:
                self.ai_chat.append(
                    '<p style="color:#ffaa44;font-size:10px;">[系统] 源会话为空，无法复制</p>'
                )
                return
            new_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_copy"
            copied_msgs = copy.deepcopy(msgs)
            self._bridge.save_session(copied_msgs, new_id)
            self._session_manager._load_sessions()
            self.ai_chat.append(
                f'<p style="color:#44cc88;font-size:10px;">[系统] 已复制会话 → {new_id}</p>'
            )
        except Exception as e:
            self.ai_chat.append(
                f'<p style="color:#ff6644;font-size:10px;">[系统] 复制会话失败: {e}</p>'
            )

    def _switch_to_session(self, session_id: str, title: str):
        if self._messages and self._bridge:
            try:
                self._bridge.save_session(self._messages, self._current_session_id)
            except Exception as e:
                print(f"[AIChatWindow] 保存会话失败: {e}")

        self._current_session_id = session_id
        self._current_title = title

        session_ctx.switch_session(session_id, title)

        self.ai_chat.clear()
        self._messages = []
        self._clear_file_pills()

        if self._bridge:
            try:
                msgs = self._bridge.load_session(session_id)
                if msgs:
                    self._messages = msgs
                    for msg in msgs:
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
            except Exception as e:
                print(f"[AIChatWindow] 加载会话失败: {e}")

        self.setWindowTitle(f"AI助手 · {title}")
        self._session_manager._load_sessions()

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024**3):.1f} GB"
        if size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024**2):.0f} MB"
        return f"{size_bytes / 1024:.0f} KB"

```
