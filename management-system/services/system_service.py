"""
系统服务
获取系统信息、硬件信息
"""

import platform
import os
import socket
import psutil
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SystemService:
    """系统服务"""

    def __init__(self):
        pass

    def get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": socket.gethostname(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    def get_cpu_info(self) -> Dict:
        """获取CPU信息"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()

        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": round(cpu_freq.max, 2) if cpu_freq else None,
            "current_frequency": round(cpu_freq.current, 2) if cpu_freq else None,
            "cpu_percent": psutil.cpu_percent(),
            "per_cpu_percent": [round(p, 1) for p in cpu_percent],
            "cpu_times": psutil.cpu_times()._asdict(),
        }

    def get_memory_info(self) -> Dict:
        """获取内存信息"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": round(mem.total / (1024 ** 3), 2),
            "available": round(mem.available / (1024 ** 3), 2),
            "used": round(mem.used / (1024 ** 3), 2),
            "percent": mem.percent,
            "swap_total": round(swap.total / (1024 ** 3), 2),
            "swap_used": round(swap.used / (1024 ** 3), 2),
            "swap_percent": swap.percent,
        }

    def get_disk_info(self) -> Dict:
        """获取磁盘信息"""
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent,
                })
            except Exception:
                pass

        return {"disks": disks}

    def get_network_info(self) -> Dict:
        """获取网络信息"""
        net_io = psutil.net_io_counters()

        return {
            "hostname": socket.gethostname(),
            "ip_address": self._get_local_ip(),
            "bytes_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

    def _get_local_ip(self) -> str:
        """获取本机IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_process_info(self, top_n: int = 10) -> List[Dict]:
        """获取进程信息"""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                processes.append(proc.info)
            except Exception:
                pass

        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        return processes[:top_n]

    def get_battery_info(self) -> Optional[Dict]:
        """获取电池信息"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "charging": battery.power_plugged,
                    "time_remaining": str(timedelta(seconds=battery.secsleft)) if battery.secsleft != -1 else "未知",
                }
        except Exception:
            pass
        return None

    def get_uptime(self) -> Dict:
        """获取运行时间"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        up_duration = datetime.now() - boot_time

        days = up_duration.days
        hours = up_duration.seconds // 3600
        minutes = (up_duration.seconds % 3600) // 60

        return {
            "boot_time": boot_time.isoformat(),
            "uptime": f"{days}天{hours}小时{minutes}分钟",
            "uptime_seconds": up_duration.total_seconds(),
        }

    def get_full_report(self) -> Dict:
        """获取系统全面报告"""
        return {
            "generated_at": datetime.now().isoformat(),
            "system": self.get_system_info(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
            "uptime": self.get_uptime(),
            "battery": self.get_battery_info(),
        }

    def check_requirements(self, requirements: Dict) -> Dict:
        """检查系统要求"""
        results = {}

        cpu_info = self.get_cpu_info()
        mem_info = self.get_memory_info()

        if "min_memory_gb" in requirements:
            results["memory"] = {
                "required": requirements["min_memory_gb"],
                "actual": mem_info["total"],
                "met": mem_info["total"] >= requirements["min_memory_gb"],
            }

        if "min_cores" in requirements:
            results["cpu_cores"] = {
                "required": requirements["min_cores"],
                "actual": cpu_info["total_cores"],
                "met": cpu_info["total_cores"] >= requirements["min_cores"],
            }

        return {
            "all_met": all(r.get("met", True) for r in results.values()),
            "checks": results,
        }

