import sqlite3
import logging
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from core.paths import DATA_DIR
from core.cloud_sync import sync_staff
from core.operation_log import log_action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(DATA_DIR, "staff.db")

def add_staff(name, position="", department="", phone="", email="", salary=0, hire_date="", status="active"):
    """添加员工，自动触发同步"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO staff (name, position, department, phone, email, salary, hire_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (name, position, department, phone, email, salary, hire_date, status))
        conn.commit()
        conn.close()
        logger.info(f"员工 {name} 添加成功，触发同步...")
        try:
            log_action("system", "添加员工", "employee", name)
        except Exception:
            pass
        sync_staff()
        return True
    except Exception as e:
        logger.error(f"添加员工失败：{str(e)}")
        return False

def update_staff(staff_id, **kwargs):
    """更新员工信息，自动触发同步"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k}=?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [staff_id]
        cursor.execute(f"""
            UPDATE staff SET {set_clause}, updated_at=datetime('now') WHERE id=?
        """, values)
        conn.commit()
        conn.close()
        logger.info(f"员工 ID {staff_id} 更新成功，触发同步...")
        try:
            log_action("system", "更新员工", "employee", f"ID={staff_id}")
        except Exception:
            pass
        sync_staff()
        return True
    except Exception as e:
        logger.error(f"更新员工失败：{str(e)}")
        return False

def delete_staff(staff_id):
    """删除员工，自动触发同步"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM staff WHERE id=?", (staff_id,))
        conn.commit()
        conn.close()
        logger.info(f"员工 ID {staff_id} 删除成功，触发同步...")
        try:
            log_action("system", "删除员工", "employee", f"ID={staff_id}")
        except Exception:
            pass
        sync_staff()
        return True
    except Exception as e:
        logger.error(f"删除员工失败：{str(e)}")
        return False

def list_staff():
    """列出所有员工"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')  # 防止 GBK 解码失败
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM staff ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"列出员工失败：{str(e)}")
        return []
