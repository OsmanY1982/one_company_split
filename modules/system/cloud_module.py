# -*- coding: utf-8 -*-
import sys
import os
from core.paths import DATA_DIR
from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
"""
云端同步核心模块
负责激活码云端同步、用户注册/激活云端验证、设备绑定等
"""
# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from core.supabase_client import CloudActivation, CloudUser, CloudLog, test_connection
from core.data_sync import DataSync
import hashlib as _hashlib, uuid as _uuid, platform as _platform

def get_machine_code():
    raw = f"{_platform.node()}-{_uuid.getnode()}"
    return _hashlib.sha256(raw.encode()).hexdigest()[:16]


def sync_activation_to_cloud(code: str, username: str) -> tuple:
    """
    同步激活码到云端
    
    Args:
        code: 激活码
        username: 用户名
        
    Returns:
        (success: bool, message: str)
    """
    try:
        # 获取机器码
        machine_code = get_machine_code()
        
        # 调用云端激活接口
        result = CloudActivation.activate(
            code=code,
            username=username,
            machine_code=machine_code
        )
        
        if result.get("success"):
            # 记录同步日志
            CloudLog.log(
                action="activation_sync",
                username=username,
                code=code,
                machine_code=machine_code,
                status="success"
            )
            return True, "激活码已成功同步到云端"
        else:
            error_msg = result.get("message", "未知错误")
            CloudLog.log(
                action="activation_sync",
                username=username,
                code=code,
                machine_code=machine_code,
                status="failed",
                error=error_msg
            )
            return False, f"云端同步失败：{error_msg}"
            
    except Exception as e:
        print(f"[cloud_sync] 同步失败: {e}")
        return False, f"同步出错：{str(e)}"
