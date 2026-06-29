# `intelligence/ai_chat_window/_misc.py`

> 路径：`intelligence/ai_chat_window/_misc.py` | 行数：66


---


```python
# ── 杂项 Mixin（清屏 / 右键菜单 / 消息操作按钮行 / 锚点点击）──
from PyQt5.QtWidgets import QMenu, QAction, QApplication


class _MiscMixin:
    """清屏 / 右键菜单 / 消息操作按钮行 / 锚点点击"""

    def _on_clear_chat(self):
        """清屏（仅清视图，保留消息历史以便回溯/重新生成）"""
        self.ai_chat.clear()

    def _msg_action_row(self, mid: int, text: str) -> str:
        """生成消息操作行 HTML：复制 | 👍 | 👎"""
        self._msg_copy_map[mid] = text
        return (
            f'<p style="font-size:10px;color:#666;margin:2px 0;">'
            f'<a href="cmd:copy:{mid}" style="color:#888;text-decoration:none;">复制</a>'
            f' &nbsp;|&nbsp; '
            f'<a href="cmd:like:{mid}" style="color:#888;text-decoration:none;">👍</a>'
            f' &nbsp;|&nbsp; '
            f'<a href="cmd:dislike:{mid}" style="color:#888;text-decoration:none;">👎</a>'
            f'</p>'
        )

    def _on_anchor_clicked(self, url):
        """消息按钮点击处理：cmd:copy:MID / cmd:like:MID / cmd:dislike:MID"""
        scheme = url.toString()
        if not scheme.startswith("cmd:"):
            return
        _, action, mid_str = scheme.split(":", 2)
        mid = int(mid_str)
        text = self._msg_copy_map.get(mid, "")

        if action == "copy":
            QApplication.clipboard().setText(text)
            self.ai_chat.append(
                f'<p style="color:#44cc88;font-size:10px;">已复制到剪贴板 ✓</p>'
            )
        elif action == "like":
            self.ai_chat.append(
                f'<p style="color:#88ccff;font-size:10px;">已记录：这条回答有帮助 ✓</p>'
            )
        elif action == "dislike":
            self.ai_chat.append(
                f'<p style="color:#ff8866;font-size:10px;">已记录：这条回答不满意 ✗</p>'
            )

    def _on_chat_context_menu(self, pos):
        menu = QMenu(self)
        copy_action = QAction("复制选中文本", self)
        copy_action.triggered.connect(self.ai_chat.copy)
        menu.addAction(copy_action)

        copy_all_action = QAction("复制全部对话", self)
        copy_all_action.triggered.connect(lambda: QApplication.clipboard().setText(
            self.ai_chat.toPlainText()
        ))
        menu.addAction(copy_all_action)

        menu.addSeparator()

        regen_action = QAction("重新生成", self)
        regen_action.triggered.connect(self._on_regenerate)
        menu.addAction(regen_action)

        menu.exec_(self.ai_chat.mapToGlobal(pos))

```
