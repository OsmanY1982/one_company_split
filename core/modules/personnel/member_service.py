# -*- coding: utf-8 -*-
"""
会员服务层
提供会员的增删改查、积分管理、等级管理、导入导出、云端同步
"""
import csv
from datetime import datetime
from pathlib import Path
from core.paths import DATA_DIR
from core.database import get_conn

DB_FILE = Path(DATA_DIR) / "member.db"


def _get_conn():
    """获取数据库连接"""
    return get_conn("member.db")


def init_db():
    """初始化数据库表"""
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS member (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            level TEXT DEFAULT '体验',
            points INTEGER DEFAULT 0,
            rights TEXT,
            vip_expire TEXT,
            status TEXT DEFAULT '正常',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_member_name ON member(name)
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_member_level ON member(level)
    ''')
    conn.commit()
    conn.close()


def add_member(name: str, phone: str = "", email: str = "",
               level: str = "体验", points: int = 0,
               rights: str = "", vip_expire: str = "",
               status: str = "正常") -> dict:
    """创建会员"""
    if not name:
        return {"ok": False, "msg": "会员姓名不能为空"}

    try:
        conn = _get_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO member 
               (name, phone, email, level, points, rights, vip_expire, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, phone, email, level, points, rights, vip_expire, status, now, now)
        )
        member_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 同步到用户系统
        _sync_to_user_system(name, level)

        # 云端同步
        _sync_to_cloud("upsert", {
            "id": member_id,
            "name": name,
            "phone": phone,
            "email": email,
            "level": level,
            "points": points,
            "rights": rights,
            "vip_expire": vip_expire,
            "status": status,
            "created_at": now,
            "updated_at": now
        })

        return {"ok": True, "msg": "会员创建成功", "id": member_id}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_members(keyword: str = "", level: str = "", status: str = "",
                limit: int = 1000) -> list:
    """查询会员列表"""
    conn = _get_conn()
    sql = """SELECT id, name, phone, email, level, points, rights, vip_expire, status, created_at
             FROM member"""
    params = []
    conditions = []

    if keyword:
        conditions.append("(name LIKE ? OR phone LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if level:
        conditions.append("level = ?")
        params.append(level)
    if status:
        conditions.append("status = ?")
        params.append(status)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_member_by_id(member_id: int) -> dict:
    """根据ID查询会员"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM member WHERE id = ?",
        (member_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_member(member_id: int, name: str = None, phone: str = None,
                  email: str = None, level: str = None, points: int = None,
                  rights: str = None, vip_expire: str = None,
                  status: str = None) -> dict:
    """更新会员"""
    try:
        conn = _get_conn()
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if level is not None:
            updates.append("level = ?")
            params.append(level)
        if points is not None:
            updates.append("points = ?")
            params.append(points)
        if rights is not None:
            updates.append("rights = ?")
            params.append(rights)
        if vip_expire is not None:
            updates.append("vip_expire = ?")
            params.append(vip_expire)
        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if not updates:
            return {"ok": False, "msg": "没有要更新的字段"}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates.append("updated_at = ?")
        params.append(now)
        params.append(member_id)

        sql = f"UPDATE member SET {', '.join(updates)} WHERE id = ?"
        conn.execute(sql, params)
        conn.commit()
        conn.close()

        # 云端同步
        _sync_to_cloud("upsert", {"id": member_id, "updated_at": now})

        return {"ok": True, "msg": "会员更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_member(member_id: int) -> dict:
    """删除会员"""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM member WHERE id = ?", (member_id,))
        conn.commit()
        conn.close()

        # 云端同步
        _sync_to_cloud("delete", {"id": member_id})

        return {"ok": True, "msg": "会员删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def add_points(member_id: int, delta: int) -> dict:
    """增减积分"""
    try:
        conn = _get_conn()
        conn.execute(
            "UPDATE member SET points = points + ?, updated_at = ? WHERE id = ?",
            (delta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), member_id)
        )
        conn.commit()
        conn.close()
        return {"ok": True, "msg": f"积分更新成功 ({delta:+d})"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_member_stats() -> dict:
    """获取会员统计"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM member").fetchone()[0]
    total_points = conn.execute("SELECT COALESCE(SUM(points), 0) FROM member").fetchone()[0]
    level_counts = conn.execute(
        "SELECT level, COUNT(*) as count FROM member GROUP BY level"
    ).fetchall()
    status_counts = conn.execute(
        "SELECT status, COUNT(*) as count FROM member GROUP BY status"
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "total_points": total_points,
        "by_level": {r[0]: r[1] for r in level_counts},
        "by_status": {r[0]: r[1] for r in status_counts}
    }


def export_members() -> tuple:
    """导出所有会员 (headers, rows)"""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, name, phone, email, level, points, rights, vip_expire, status, created_at
           FROM member ORDER BY id DESC"""
    ).fetchall()
    conn.close()

    headers = ["ID", "姓名", "电话", "邮箱", "等级", "积分", "权益", "VIP有效期", "状态", "注册时间"]
    return headers, rows


def import_members(data_list: list) -> dict:
    """批量导入会员"""
    try:
        conn = _get_conn()
        count = 0
        errors = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, item in enumerate(data_list, 1):
            try:
                name = item.get("name", "").strip()
                if not name:
                    errors.append(f"第{idx}行: 会员姓名不能为空")
                    continue

                phone = item.get("phone", "").strip()
                email = item.get("email", "").strip()
                level = item.get("level", "体验").strip() or "体验"
                points = int(item.get("points", 0) or 0)
                rights = item.get("rights", "").strip()
                vip_expire = item.get("vip_expire", "").strip()
                status = item.get("status", "正常").strip() or "正常"

                conn.execute(
                    """INSERT INTO member 
                       (name, phone, email, level, points, rights, vip_expire, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, phone, email, level, points, rights, vip_expire, status, now, now)
                )
                count += 1
            except Exception as e:
                errors.append(f"第{idx}行: {e}")

        conn.commit()
        conn.close()

        return {
            "ok": True,
            "msg": f"成功导入 {count} 条会员" + (f"，{len(errors)} 条失败" if errors else ""),
            "count": count,
            "errors": errors
        }
    except Exception as e:
        return {"ok": False, "msg": f"导入失败: {e}"}


# ══════════════════════════════════════════════════════
#  用户系统同步
# ══════════════════════════════════════════════════════

def _sync_to_user_system(name: str, level: str):
    """同步到用户系统（非阻塞）"""
    try:
        from core.data_sync import DataSync
        membership_type = "trial" if level == "体验" else ("pro" if level == "VIP" else "vip")
        DataSync.record_user_login(name, "user", membership_type)
        DataSync.record_membership(name, membership_type)
    except Exception as e:
        print(f"[MemberService] 用户系统同步失败 (non-blocking): {e}")


# ══════════════════════════════════════════════════════
#  云端同步
# ══════════════════════════════════════════════════════

def _sync_to_cloud(action: str, payload: dict):
    """同步到云端（非阻塞）"""
    try:
        from core.supabase_client import CloudMember
        if action == "upsert":
            CloudMember.upsert(**payload)
        elif action == "delete":
            CloudMember.delete(payload.get("id"))
    except Exception as e:
        print(f"[MemberService] 云端同步失败 (non-blocking): {e}")


if __name__ == "__main__":
    init_db()
    print("会员服务测试")
    stats = get_member_stats()
    print(f"会员统计: {stats}")
