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
            description="执行 shell 命令。适用：安装依赖、运行脚本、系统查询",
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

    # ── 9. desktop_control（跨平台桌面操控，由 platform_commands 抽象）──
    def _reg_desktop_control(self):
        from iqra.core.platform_commands import (
            app_open, app_close, app_switch, get_frontmost_app,
            type_text, press_keys, volume_up, volume_down, volume_mute,
            system_sleep, screenshot, open_url,
        )

        ACTIONS = {
            "open_app":       (lambda t: app_open(t),              "target", "打开应用"),
            "close_app":      (lambda t: app_close(t),             "target", "关闭应用"),
            "switch_app":     (lambda t: app_switch(t),            "target", "切换到应用"),
            "get_frontmost":  (lambda t: get_frontmost_app(),       None,     "获取前台应用"),
            "type_text":      (lambda t: type_text(t),             "target", "输入文本"),
            "press_keys":     (lambda t: press_keys(t),            "target", "按键组合"),
            "volume_up":      (lambda t: volume_up(),              None,     "音量+10%"),
            "volume_down":    (lambda t: volume_down(),            None,     "音量-10%"),
            "mute":           (lambda t: volume_mute(),            None,     "静音切换"),
            "sleep":          (lambda t: system_sleep(),           None,     "系统休眠"),
            "screenshot":     (lambda t: screenshot(""),           None,     "截图存桌面"),
            "open_url":       (lambda t: open_url(t),              "target", "打开URL"),
        }

        def handler(action: str, target: str = "", text: str = "") -> dict:
            try:
                if action not in ACTIONS:
                    return {"error": f"不支持的操作: {action}。可用: {list(ACTIONS.keys())}"}
                fn, param_key, _desc = ACTIONS[action]
                param = target if param_key else ""
                result = fn(param)
                if result.get("error"):
                    return result
                return {"success": True, "action": action, **result}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="desktop_control",
            description="跨平台桌面操控：打开/关闭应用、模拟输入、系统控制（macOS/Windows/Linux）",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: open_app/close_app/type_text/press_keys/switch_app/volume_up/volume_down/mute/sleep/screenshot/open_url/get_frontmost"},
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
