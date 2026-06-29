# `core/modules/supabase/_core.py`

> 路径：`core/modules/supabase/_core.py` | 行数：131


---


```python
# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 核心基础模块
HTTP 请求 / DNS 预检 / 连接测试 / 用户云端状态检查
"""
import sys, os
import json
import socket
import sqlite3
import hashlib
import threading
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
import ssl

from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
from config.supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

# ── 全局 SSL 上下文 ──
# 默认启用证书验证，仅在内网/测试环境禁用
SSL_VERIFY = os.environ.get("SUPABASE_SSL_VERIFY", "true").lower() == "true"
SSL_CTX = ssl.create_default_context()
if not SSL_VERIFY:
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE


# ── DNS 预检缓存 ──
_dns_reachable = None  # None=未检, True=可达, False=不可达


def _dns_precheck():
    """快速 DNS 预检：用独立线程 + 3秒 join 超时判断 SUPABASE_URL 主机名是否可达。
    结果缓存到 _dns_reachable，避免每次 _request 都重复解析。
    """
    global _dns_reachable
    if _dns_reachable is not None:
        return _dns_reachable
    try:
        hostname = urlparse(SUPABASE_URL).hostname
        if not hostname:
            _dns_reachable = False
            return False

        result = {"ok": False}

        def _resolve():
            try:
                socket.getaddrinfo(hostname, None)
                result["ok"] = True
            except Exception:
                pass

        t = threading.Thread(target=_resolve, daemon=True)
        t.start()
        t.join(timeout=3)
        _dns_reachable = result["ok"]
    except Exception:
        _dns_reachable = False
    return _dns_reachable


def _request(method, path, data=None, service_key=False, prefer="return=representation"):
    """统一 HTTP 请求
    
    prefer: Prefer header value. Use 'resolution=merge-duplicates' for upsert.
    """
    # 快速 DNS 预检：域名不可达时直接短路，避免 urlopen 漫长的 DNS 超时阻塞
    if not _dns_precheck():
        return False, {"error": "dns_unreachable"}

    url = f"{SUPABASE_URL}{path}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY if service_key else SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY if service_key else SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer
    }
    body = json.dumps(data, ensure_ascii=False).encode() if data else None
    try:
        req = Request(url, data=body, headers=headers, method=method)
        with urlopen(req, context=SSL_CTX, timeout=15) as resp:
            raw = resp.read()
            if not raw:
                return True, {}
            result = json.loads(raw.decode())
            # Supabase 返回格式：{"data": [...]} 或单个对象
            return True, result
    except HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
            return False, err_body
        except Exception:
            return False, {"message": f"HTTP {e.code}: {e.reason}"}
    except URLError as e:
        return False, {"message": f"网络错误：{e.reason}"}
    except Exception as e:
        return False, {"message": str(e)}


def test_connection() -> tuple:
    """测试 Supabase 连接是否正常"""
    ok, result = _request("GET", "/rest/v1/activation_codes?select=id&limit=1", service_key=True)
    if ok:
        return True, "✅ 云端连接正常"
    return False, f"❌ 云端连接失败：{result.get('message', result)}"


def check_user_cloud_status(username: str) -> tuple:
    """
    检查用户是否仍在云端存在（用户被管理员删除 → 云端查无此人）
    Returns: (ok, exists)
      - ok:      API 调用是否成功（网络通不通）
      - exists:  用户是否还存在云端 (True / False / None=未知)
    """
    # 1. 查 users 表
    ok1, result1 = _request("GET", f"/rest/v1/users?username=eq.{username}&select=id")
    if ok1 and isinstance(result1, list) and len(result1) > 0:
        return True, True

    # 2. 查 user_memberships 表（可能用户记录在这里）
    ok2, result2 = _request("GET", f"/rest/v1/user_memberships?username=eq.{username}&select=id")
    if ok2 and isinstance(result2, list) and len(result2) > 0:
        return True, True

    # 两个表都没找到此用户
    if ok1 or ok2:
        return True, False   # 至少一次查询成功 → 确认用户不存在
    return False, None      # 两次都失败（网络错误）

```
