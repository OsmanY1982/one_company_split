# `core/auth_service.py`

> 路径：`core/auth_service.py` | 行数：28


---


```python
# -*- coding: utf-8 -*-
"""
认证服务适配层 — P0 改造后委托到 core.modules.auth.auth_service.AuthService
（2026-06-28 第十三档）
"""

def authenticate(username: str, password: str) -> bool:
    """认证函数，委托到统一 AuthService（bcrypt 密码验证）"""
    try:
        from core.modules.auth.auth_service import AuthService
        auth = AuthService()
        result = auth.login(username, password)
        return result.get("ok", False)
    except Exception:
        return False


def get_user_role(username: str) -> str:
    """获取用户角色，委托到统一 AuthService"""
    try:
        from core.modules.auth.auth_service import AuthService
        auth = AuthService()
        user = auth.get_user_info(username)
        if user:
            return user.get("role", "user")
        return "user"
    except Exception:
        return "user"

```
