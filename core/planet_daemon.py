#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悬浮星球启动器 — 从宇宙版主程序切入悬浮球。
自身不创建任何 QApplication / FloatingPlanet 实例。
宇宙版已运行 → 发 IPC toggle 命令；
宇宙版未运行 → 启动宇宙版极简浮球模式（main.py --floating-only）。
"""
import sys
import os
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PlanetLauncher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PlanetLauncher")

PROJECT_ROOT = "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"
LOCK_FILE = "/tmp/iqra_floating_planet.pid"
CMD_FILE = "/tmp/iqra_floating_cmd"


def _floating_planet_exists() -> bool:
    """检查是否有宇宙版进程已持有悬浮球。"""
    if not os.path.exists(LOCK_FILE):
        return False
    try:
        with open(LOCK_FILE, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass
        return False


def _send_ipc_cmd(cmd: str):
    """向持有悬浮球的宇宙版进程发送 IPC 命令。"""
    try:
        with open(CMD_FILE, "w") as f:
            f.write(cmd)
        logger.info("已发送 IPC 命令: %s", cmd)
    except OSError as e:
        logger.error("发送 IPC 命令失败: %s", e)


def main():
    if _floating_planet_exists():
        logger.info("宇宙版已运行，发送 toggle 命令")
        _send_ipc_cmd("toggle")
        return 0

    # 宇宙版未运行 → 启动极简浮球模式
    logger.info("宇宙版未运行，启动极简浮球模式...")
    main_py = os.path.join(PROJECT_ROOT, "main.py")
    subprocess.Popen(
        [sys.executable, main_py, "--floating-only"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("已启动 main.py --floating-only")
    return 0


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("悬浮星球启动器（从宇宙版切入）")
    logger.info("=" * 60)
    exit_code = main()
    logger.info("启动器退出 (exit_code=%s)", exit_code)
    sys.exit(exit_code)
