#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
星球守护 Siri 语音命令处理器
用法: python3 siri_command_handler.py "语音识别文本"
"""

import sys
import os
import subprocess
import logging
from datetime import datetime

LOG_PATH = "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic/siri_commands.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

def log_and_say(msg):
    """记录日志并语音播报"""
    logging.info(msg)
    subprocess.run(["say", msg], check=False)

def run_osascript(script):
    """执行 AppleScript"""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, check=False
    )
    return result.stdout.strip(), result.stderr.strip()

def execute_command(text):
    text_lower = text.strip().lower()
    logging.info(f"收到语音指令: {text}")

    # ── 关键词匹配 ──
    if any(kw in text_lower for kw in ["打开终端", "启动终端", "终端"]):
        subprocess.Popen(["open", "-a", "Terminal"])
        log_and_say("终端已打开")

    elif any(kw in text_lower for kw in ["打开浏览器", "启动浏览器", "浏览器"]):
        subprocess.Popen(["open", "-a", "Safari"])
        log_and_say("浏览器已打开")

    elif any(kw in text_lower for kw in ["打开访达", "启动访达", "访达"]):
        subprocess.Popen(["open", "-a", "Finder"])
        log_and_say("访达已打开")

    elif "锁屏" in text_lower or "锁定屏幕" in text_lower:
        stdout, stderr = run_osascript('tell application "System Events" to keystroke "q" using {command down, control down}')
        if stderr:
            log_and_say(f"锁屏失败: {stderr}")
        else:
            log_and_say("屏幕已锁定")

    elif any(kw in text_lower for kw in ["静音", "关闭声音", "取消静音", "打开声音", "恢复声音"]):
        if "取消" in text_lower or "打开" in text_lower or "恢复" in text_lower:
            subprocess.run(["osascript", "-e", "set volume output muted false"], check=False)
            log_and_say("声音已恢复")
        else:
            subprocess.run(["osascript", "-e", "set volume output muted true"], check=False)
            log_and_say("已静音")

    elif any(kw in text_lower for kw in ["截图", "截屏"]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.expanduser("~/Desktop")
        filename = f"星球截图_{timestamp}.png"
        filepath = os.path.join(desktop, filename)
        result = subprocess.run(
            ["screencapture", "-i", filepath],
            capture_output=True, text=True, check=False
        )
        if os.path.exists(filepath):
            log_and_say(f"截图已保存到桌面: {filename}")
        else:
            log_and_say("截图已取消或失败")

    elif any(kw in text_lower for kw in ["刷新", "刷新桌面", "刷新屏幕"]):
        subprocess.run(["killall", "Dock"], check=False)
        log_and_say("桌面已刷新")

    elif any(kw in text_lower for kw in ["打开设置", "系统设置", "系统偏好"]):
        subprocess.Popen(["open", "-a", "System Settings"])
        log_and_say("系统设置已打开")

    elif any(kw in text_lower for kw in ["打开活动监视器", "活动监视器"]):
        subprocess.Popen(["open", "-a", "Activity Monitor"])
        log_and_say("活动监视器已打开")

    elif any(kw in text_lower for kw in ["打开文件夹", "打开目录"]):
        target = "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"
        subprocess.Popen(["open", target])
        log_and_say("工作目录已打开")

    elif any(kw in text_lower for kw in ["星球守护", "星球", "悬浮球"]):
        log_and_say("星球守护悬浮球正在运行")

    elif any(kw in text_lower for kw in ["关闭窗口", "关掉窗口"]):
        stdout, stderr = run_osascript('tell application "System Events" to keystroke "w" using {command down}')
        if stderr:
            log_and_say(f"关闭窗口失败: {stderr}")
        else:
            log_and_say("窗口已关闭")

    elif any(kw in text_lower for kw in ["隐藏窗口", "最小化"]):
        stdout, stderr = run_osascript('tell application "System Events" to keystroke "m" using {command down}')
        if stderr:
            log_and_say(f"最小化失败: {stderr}")
        else:
            log_and_say("窗口已最小化")

    else:
        log_and_say(f"未识别指令: {text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 siri_command_handler.py \"语音识别文本\"")
        sys.exit(1)

    command_text = sys.argv[1]
    execute_command(command_text)
