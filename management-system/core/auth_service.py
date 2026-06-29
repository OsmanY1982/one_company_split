# -*- coding: utf-8 -*-
"""
认证服务
用户名密码验证
"""


def authenticate(username: str, password: str) -> bool:
    """简单的认证函数，返回 True/False"""
    # 此处可替换为实际的密码验证逻辑
    return username == "admin" and password == "admin"


def get_user_role(username: str) -> str:
    """获取用户角色"""
    if username == "admin":
        return "admin"
    return "user"
