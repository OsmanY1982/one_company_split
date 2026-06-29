# -*- coding: utf-8 -*-
"""
跨平台机器码生成
同一台电脑相同系统生成相同机器码
"""
import platform
import hashlib
import subprocess
import re
import os


def get_machine_code():
    """获取本机唯一机器码"""
    system = platform.system()
    if system == "Windows":
        return _win_machine_code()
    elif system == "Darwin":
        return _mac_machine_code()
    elif system == "Linux":
        return _linux_machine_code()
    else:
        # 降级方案：使用主机名 + CPU架构
        fallback = f"{platform.node()}-{platform.machine()}"
        return hashlib.md5(fallback.encode()).hexdigest()[:32]


def _win_machine_code():
    """Windows 机器码"""
    parts = []
    try:
        result = subprocess.run(["wmic", "csproduct", "get", "uuid"], capture_output=True, text=True, shell=True)
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                uuid = lines[1].strip()
                if uuid and uuid != "":
                    parts.append(uuid)
    except Exception:
        pass
    try:
        result = subprocess.run(["wmic", "diskdrive", "get", "serialnumber"], capture_output=True, text=True, shell=True)
        if result.stdout:
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            if len(lines) > 1:
                parts.append(lines[1])
    except Exception:
        pass
    parts.append(platform.node())
    return hashlib.md5("-".join(parts).encode()).hexdigest()[:32]


def _mac_machine_code():
    """macOS 机器码"""
    parts = []
    try:
        result = subprocess.run(
            ["ioreg", "-l", "-d", "1", "-r", "-c", "IOPlatformExpertDevice"],
            capture_output=True, text=True
        )
        if result.stdout:
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', result.stdout)
            if match:
                parts.append(match.group(1))
    except Exception:
        pass
    parts.append(platform.node())
    return hashlib.md5("-".join(parts).encode()).hexdigest()[:32]


def _linux_machine_code():
    """Linux 机器码"""
    parts = []
    try:
        if os.path.exists("/etc/machine-id"):
            with open("/etc/machine-id") as f:
                parts.append(f.read().strip())
    except Exception:
        pass
    parts.append(platform.node())
    return hashlib.md5("-".join(parts).encode()).hexdigest()[:32]


if __name__ == "__main__":
    print(f"系统: {platform.system()}")
    print(f"机器码: {get_machine_code()}")
