# -*- coding: utf-8 -*-
"""pytest 配置与共享 fixtures"""
import os
import sys
import tempfile
import shutil
import pytest

# 确保 core 包可导入
CORE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CORE_ROOT not in sys.path:
    sys.path.insert(0, CORE_ROOT)


@pytest.fixture
def temp_users_json():
    """创建临时 users.json，自动清理"""
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, "users.json")
    yield tmpfile
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_data_dir():
    """创建临时 data 目录"""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_db(tmp_path):
    """返回一个临时 SQLite 数据库路径"""
    db_path = str(tmp_path / "test.db")
    return db_path
