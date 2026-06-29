# `planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_system_tools.py`

> 路径：`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_system_tools.py` | 行数：125


---


```python
"""系统工具 Mixin：execute_shell / desktop_control / git_operation"""

import os
import subprocess


class _SystemToolsMixin:
    """系统工具注册"""

    # ── 8. execute_shell ──
    def _reg_execute_shell(self):
        def handler(command: str, timeout: int = 60) -> dict:
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=timeout,
                    cwd=os.path.expanduser("~"),
                )
                return {
                    "stdout": result.stdout[:8000],
                    "stderr": result.stderr[:4000],
                    "returncode": result.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"error": f"命令超时 ({timeout}s)", "stdout": "", "stderr": ""}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="execute_shell",
            description="在 macOS 终端执行 shell 命令。适用：安装依赖、运行脚本、系统查询",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "shell 命令"},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 60},
                },
                "required": ["command"],
            },
            category="system",
        )(handler)

    # ── 9. desktop_control（AppleScript 桌面操控）──
    def _reg_desktop_control(self):
        def handler(action: str, target: str = "", text: str = "") -> dict:
            try:
                scripts = {
                    "open_app": f'tell application "{target}" to activate',
                    "close_app": f'tell application "{target}" to quit',
                    "type_text": f'tell application "System Events" to keystroke "{text}"',
                    "press_keys": f'tell application "System Events" to keystroke "{text}"',
                    "get_frontmost": 'tell application "System Events" to get name of first application process whose frontmost is true',
                    "switch_app": f'tell application "{target}" to activate',
                    "open_url": f'open location "{target}"',
                    "volume_up": "set volume output volume (output volume of (get volume settings) + 10)",
                    "volume_down": "set volume output volume (output volume of (get volume settings) - 10)",
                    "mute": "set volume with output muted",
                    "sleep": 'tell application "System Events" to sleep',
                    "screenshot": 'do shell script "screencapture -i ~/Desktop/screenshot.png"',
                }
                if action not in scripts:
                    return {"error": f"不支持的操作: {action}。可用: {list(scripts.keys())}"}
                script = scripts[action]
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
                if result.returncode != 0:
                    return {"error": result.stderr.strip()}
                return {"success": True, "action": action, "output": result.stdout.strip()}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="desktop_control",
            description="macOS 桌面操控：打开/关闭应用、模拟输入、系统控制",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: open_app/close_app/type_text/press_keys/switch_app/volume_up/volume_down/mute/sleep/screenshot"},
                    "target": {"type": "string", "description": "目标应用名/按键/URL", "default": ""},
                    "text": {"type": "string", "description": "要输入的文本（type_text/press_keys 时使用）", "default": ""},
                },
                "required": ["action"],
            },
            category="system",
        )(handler)

    # ── 10. git_operation ──
    def _reg_git_operation(self):
        def handler(operation: str, repo_path: str = ".", args: str = "") -> dict:
            try:
                valid_ops = ["status", "diff", "log", "branch", "add", "commit", "pull", "push", "stash", "checkout"]
                if operation not in valid_ops:
                    return {"error": f"不支持的 Git 操作: {operation}。可用: {valid_ops}"}

                cmd = ["git", "-C", repo_path, operation]
                if args:
                    cmd.extend(args.split())

                if operation == "commit":
                    cmd.append("-m")
                    cmd.append(args)

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return {
                    "operation": operation,
                    "repo": repo_path,
                    "returncode": result.returncode,
                    "stdout": result.stdout[:4000],
                    "stderr": result.stderr[:2000],
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="git_operation",
            description="Git 版本控制：查看状态、diff、log、提交等",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Git 操作: status/diff/log/branch/add/commit/pull/push/stash/checkout"},
                    "repo_path": {"type": "string", "description": "仓库路径", "default": "."},
                    "args": {"type": "string", "description": "额外参数（如文件路径、commit message）", "default": ""},
                },
                "required": ["operation"],
            },
            category="code",
        )(handler)

```
