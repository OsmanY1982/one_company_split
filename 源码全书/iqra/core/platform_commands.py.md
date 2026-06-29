# `iqra/core/platform_commands.py`

> 路径：`iqra/core/platform_commands.py` | 行数：322


---


```python
# -*- coding: utf-8 -*-
"""
跨平台桌面命令抽象层

将原先散落在各处的 osascript/say/screencapture 硬编码统一到此模块，
对外提供平台无关的 API，内部按操作系统分发到具体实现。

架构：
  ┌───────────── PlatformCommands ─────────────┐
  │  app_open / app_close / volume / screenshot │
  │  type_text / press_keys / speech / ...      │
  └──────────────┬──────────────────────────────┘
          ┌──────┴──────┬──────────┐
    ┌─────┴─────┐ ┌─────┴─────┐ ┌─┴──────────┐
    │  macOS    │ │  Windows  │ │   Linux     │
    │ (原生)    │ │  (stub)   │ │   (stub)    │
    └───────────┘ └───────────┘ └─────────────┘

新增平台只需实现对应方法即可。
"""

import os
import sys
import subprocess
import shutil
from typing import Optional, Dict

# ── 平台检测 ──
PLATFORM = sys.platform  # "darwin" / "win32" / "linux"
IS_MACOS = PLATFORM == "darwin"
IS_WINDOWS = PLATFORM == "win32"
IS_LINUX = PLATFORM == "linux"


# ══════════════════════════════════════════
# 公共 API
# ══════════════════════════════════════════

class PlatformCommands:
    """跨平台桌面命令（单例模式）"""

    def app_open(self, app_name: str) -> Dict:
        """打开/激活应用"""
        if IS_MACOS:
            return self._macos_app_open(app_name)
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_app_open
            return windows_app_open(app_name)
        else:
            from iqra.core.platform_implementations import linux_app_open
            return linux_app_open(app_name)

    def app_close(self, app_name: str) -> Dict:
        """关闭应用"""
        if IS_MACOS:
            return self._macos_app_close(app_name)
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_app_close
            return windows_app_close(app_name)
        else:
            from iqra.core.platform_implementations import linux_app_close
            return linux_app_close(app_name)

    def app_switch(self, app_name: str) -> Dict:
        """切换到指定应用（同 app_open）"""
        return self.app_open(app_name)

    def get_frontmost_app(self) -> Dict:
        """获取当前前台应用名"""
        if IS_MACOS:
            return self._macos_get_frontmost()
        elif IS_WINDOWS:
            return self._error("Windows 暂不支持 get_frontmost")
        else:
            return self._error("Linux 暂不支持 get_frontmost")

    def type_text(self, text: str) -> Dict:
        """模拟键盘输入文本"""
        if IS_MACOS:
            return self._macos_type_text(text)
        elif IS_WINDOWS:
            return self._error("Windows 暂不支持 type_text")
        else:
            return self._error("Linux 暂不支持 type_text")

    def press_keys(self, keys: str) -> Dict:
        """模拟按键组合"""
        return self.type_text(keys)

    def volume_up(self) -> Dict:
        """音量 +10%"""
        if IS_MACOS:
            return self._macos_volume("up")
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_volume
            return windows_volume("up")
        else:
            from iqra.core.platform_implementations import linux_volume
            return linux_volume("up")

    def volume_down(self) -> Dict:
        """音量 -10%"""
        if IS_MACOS:
            return self._macos_volume("down")
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_volume
            return windows_volume("down")
        else:
            from iqra.core.platform_implementations import linux_volume
            return linux_volume("down")

    def volume_mute(self) -> Dict:
        """静音切换"""
        if IS_MACOS:
            return self._macos_volume("mute")
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_volume
            return windows_volume("mute")
        else:
            from iqra.core.platform_implementations import linux_volume
            return linux_volume("mute")

    def sleep(self) -> Dict:
        """系统休眠"""
        if IS_MACOS:
            return self._macos_sleep()
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_sleep
            return windows_sleep()
        else:
            from iqra.core.platform_implementations import linux_sleep
            return linux_sleep()

    def screenshot(self, output_path: str = "") -> Dict:
        """截图"""
        if not output_path:
            output_path = os.path.expanduser("~/Desktop/screenshot.png")
        if IS_MACOS:
            return self._macos_screenshot(output_path)
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_screenshot
            return windows_screenshot(output_path)
        else:
            from iqra.core.platform_implementations import linux_screenshot
            return linux_screenshot(output_path)

    def open_url(self, url: str) -> Dict:
        """打开 URL（在默认浏览器中）"""
        if IS_MACOS:
            return self._run_native(["open", url])
        elif IS_WINDOWS:
            return self._run_native(["start", "", url], shell_needed=True)
        else:
            return self._run_native(["xdg-open", url])

    def text_to_speech(self, text: str, voice: str = "") -> Dict:
        """文本转语音"""
        if IS_MACOS:
            cmd = ["say", text]
            if voice:
                cmd.extend(["-v", voice])
            return self._run_native(cmd)
        elif IS_WINDOWS:
            from iqra.core.platform_implementations import windows_text_to_speech
            return windows_text_to_speech(text, voice)
        else:
            from iqra.core.platform_implementations import linux_text_to_speech
            return linux_text_to_speech(text, voice)

    # ── macOS 原生实现 ──

    def _macos_app_open(self, name: str) -> Dict:
        """macOS: 使用 open -a 启动/激活应用"""
        return self._run_native(["open", "-a", name])

    def _macos_app_close(self, name: str) -> Dict:
        """macOS: 通过 AppleScript 退出应用"""
        script = f'tell application "{name}" to quit'
        return self._run_osascript(script)

    def _macos_get_frontmost(self) -> Dict:
        """macOS: 获取前台应用名"""
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        return self._run_osascript(script)

    def _macos_type_text(self, text: str) -> Dict:
        """macOS: 通过 AppleScript 模拟键盘输入"""
        script = f'tell application "System Events" to keystroke "{text}"'
        return self._run_osascript(script)

    def _macos_volume(self, direction: str) -> Dict:
        """macOS: 音量控制"""
        if direction == "up":
            script = "set volume output volume (output volume of (get volume settings) + 10)"
        elif direction == "down":
            script = "set volume output volume (output volume of (get volume settings) - 10)"
        elif direction == "mute":
            script = "set volume with output muted"
        else:
            return {"error": f"未知音量操作: {direction}"}
        return self._run_osascript(script)

    def _macos_sleep(self) -> Dict:
        """macOS: 系统休眠"""
        # pmset sleepnow 比 AppleScript 更可靠
        try:
            return self._run_native(["pmset", "sleepnow"])
        except Exception:
            # 回退到 AppleScript
            script = 'tell application "System Events" to sleep'
            return self._run_osascript(script)

    def _macos_screenshot(self, output_path: str) -> Dict:
        """macOS: 截图"""
        return self._run_native(["screencapture", "-i", output_path])

    # ── 底层工具 ──

    def _run_osascript(self, script: str, timeout: int = 15) -> Dict:
        """执行 AppleScript 并返回统一下载格式"""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=timeout,
            )
            if result.returncode != 0:
                return {"error": result.stderr.strip()}
            return {"success": True, "output": result.stdout.strip()}
        except subprocess.TimeoutExpired:
            return {"error": "AppleScript 超时"}
        except FileNotFoundError:
            return {"error": "osascript 不可用（非 macOS 系统？）"}
        except Exception as exc:
            return {"error": str(exc)}

    def _run_native(self, cmd: list, timeout: int = 15, shell_needed: bool = False) -> Dict:
        """执行原生命令并返回统一下载格式"""
        try:
            if shell_needed:
                result = subprocess.run(
                    " ".join(cmd), shell=True,
                    capture_output=True, text=True, timeout=timeout,
                )
            else:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout,
                )
            if result.returncode != 0:
                return {"error": result.stderr.strip() or result.stdout.strip()}
            return {"success": True, "output": result.stdout.strip()}
        except subprocess.TimeoutExpired:
            return {"error": f"命令超时 ({timeout}s)"}
        except FileNotFoundError:
            return {"error": f"命令不可用: {cmd[0]}"}
        except Exception as exc:
            return {"error": str(exc)}

    def _error(self, msg: str) -> Dict:
        return {"error": msg, "platform": PLATFORM}


# ── 全局单例 ──
_platform = PlatformCommands()


# ── 便捷函数 ──

def platform() -> str:
    """返回当前平台标识: darwin / win32 / linux"""
    return PLATFORM


def app_open(app_name: str) -> Dict:
    return _platform.app_open(app_name)


def app_close(app_name: str) -> Dict:
    return _platform.app_close(app_name)


def app_switch(app_name: str) -> Dict:
    return _platform.app_switch(app_name)


def get_frontmost_app() -> Dict:
    return _platform.get_frontmost_app()


def type_text(text: str) -> Dict:
    return _platform.type_text(text)


def press_keys(keys: str) -> Dict:
    return _platform.press_keys(keys)


def volume_up() -> Dict:
    return _platform.volume_up()


def volume_down() -> Dict:
    return _platform.volume_down()


def volume_mute() -> Dict:
    return _platform.volume_mute()


def system_sleep() -> Dict:
    return _platform.sleep()


def screenshot(output_path: str = "") -> Dict:
    return _platform.screenshot(output_path)


def open_url(url: str) -> Dict:
    return _platform.open_url(url)


def text_to_speech(text: str, voice: str = "") -> Dict:
    return _platform.text_to_speech(text)

```
