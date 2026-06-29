#!/usr/bin/env python3
r"""
分销服务模块 - 从手机端 Flutter 移植
参考: D:/one_company_mobile/lib/modules/distribution/services/distribution_service.dart

提供: 分销链接管理、佣金管理、团队管理
数据库: data/distribution.db (distribution_links + commissions + team_members)
"""
import random, time, sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import os, sys

# ── 路径兼容：支持直接运行和模块导入 ──────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.paths import DATA_DIR
from core.database import get_conn

DB_PATH = os.path.join(DATA_DIR, "distribution.db")

def _connect():
    return get_conn("distribution.db")

# ============================================================
# 分销链接管理
# ============================================================

def _generate_code() -> str:
    """生成唯一推荐码"""
    now = str(int(time.time() * 1000))
    rand = str(random.randint(1000, 9999))
    return f"REF{now[-8:]}{rand}"

def create_link(user_id: int, code: str = None, url: str = None) -> dict:
    """创建分销链接"""
    conn = _connect()
    if not code:
        code = _generate_code()
    if not url:
        url = f"https://one.company/register?ref={code}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO distribution_links (user_name, code, url, status, created_at) VALUES (?, ?, ?, 'active', ?)",
            (user_id, code, url, now)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM distribution_links WHERE code = ?", (code,)).fetchone()
        conn.close()
        result = {"ok": True, **dict(row)} if row else {"ok": False, "error": "创建失败"}
        
        # ── 同步到云端 ──────────────────────
        if result and "id" in result:
            try:
                from core.supabase_client import CloudDistribution
                CloudDistribution.upsert(
                    user_id=user_id,
                    code=code,
                    url=url,
                    click_count=0,
                    register_count=0,
                    total_commission=0,
                    status="active"
                )
            except Exception as e:
                print(f"[Distribution] 云端同步失败 (非阻塞): {e}")
        
        return result
    except sqlite3.IntegrityError:
        conn.close()
        return create_link(user_id)  # 递归重试

def get_user_links(user_id: int) -> list[dict]:
    """获取用户的所有分销链接"""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM distribution_links WHERE user_name = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def increment_click(code: str) -> dict:
    """点击计数 +1"""
    conn = _connect()
    conn.execute("UPDATE distribution_links SET click_count = click_count + 1 WHERE code = ?", (code,))
    conn.commit()
    row = conn.execute("SELECT click_count FROM distribution_links WHERE code = ?", (code,)).fetchone()
    conn.close()
    if row:
        return {"ok": True, "click_count": dict(row)["click_count"]}
    return {"ok": False, "error": "链接不存在"}

def increment_register(code: str) -> dict:
    """注册计数 +1"""
    conn = _connect()
    conn.execute("UPDATE distribution_links SET register_count = register_count + 1 WHERE code = ?", (code,))
    conn.commit()
    row = conn.execute("SELECT register_count FROM distribution_links WHERE code = ?", (code,)).fetchone()
    conn.close()
    if row:
        return {"ok": True, "register_count": dict(row)["register_count"]}
    return {"ok": False, "error": "链接不存在"}

# ============================================================
# 佣金管理
# ============================================================

def add_commission(user_id: int, amount: float, from_user_id: int = None,
                   comm_type: str = "referral", description: str = None) -> dict:
    """添加佣金记录（自动同步到钱包 + 云端）"""
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO commissions (user_id, from_user_id, amount, type, status, description, created_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?, ?)",
            (user_id, from_user_id, amount, comm_type, description, now)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        return {"ok": False, "error": str(e)}

    # ── 同步佣金到云端 ──────────────────────
    try:
        from core.supabase_client import CloudCommission
        CloudCommission.upsert(
            user_id=user_id,
            amount=amount,
            from_user_id=from_user_id,
            type_=comm_type,
            status="pending",
            description=description
        )
    except Exception as e:
        print(f"[Distribution] 佣金云端同步失败 (非阻塞): {e}")

    # ── 佣金自动入钱包（P0 核心闭环）──────────────────────
    desc = description or f"推荐佣金 ({comm_type})"
    from core.modules.personnel.wallet_service import add_commission as wallet_add_commission
    w_result = wallet_add_commission(str(user_id), amount, desc)
    if not w_result["ok"]:
        return {"ok": True, "wallet_error": w_result.get("error")}
    return {"ok": True, "balance": w_result.get("balance")}

def get_user_commissions(user_id: int) -> list[dict]:
    """获取用户佣金记录"""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM commissions WHERE user_name = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_total_commission(user_id: int) -> float:
    """获取用户总佣金"""
    conn = _connect()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM commissions WHERE user_name = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return row["total"] if row else 0

# ============================================================
# 团队管理
# ============================================================

def add_team_member(user_id: int, parent_id: int, username: str = None, level: int = 1) -> dict:
    """添加团队成员"""
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO team_members (user_id, parent_id, level, created_at) VALUES (?, ?, ?, ?)",
            (user_id, parent_id, level, now)
        )
        conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()

def get_team_members(parent_id: int) -> list[dict]:
    """获取团队成员列表"""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM team_members WHERE parent_name = ? ORDER BY created_at DESC",
        (parent_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_team_size(parent_id: int) -> int:
    """获取团队人数"""
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM team_members WHERE parent_name = ?",
        (parent_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0

def get_team_stats(parent_id: int) -> dict:
    """获取团队统计: 总人数、总贡献、层级分布"""
    conn = _connect()
    members = conn.execute(
        "SELECT * FROM team_members WHERE parent_name = ? ORDER BY created_at DESC",
        (parent_id,)
    ).fetchall()
    members_list = [dict(r) for r in members]
    total_contribution = sum(m.get("total_contribution", 0) for m in members_list)
    levels = {}
    for m in members_list:
        lv = m.get("level", 1)
        levels[lv] = levels.get(lv, 0) + 1
    conn.close()
    return {
        "team_size": len(members_list),
        "total_contribution": total_contribution,
        "level_distribution": levels,
        "members": members_list
    }


# ============================================================
# Admin 级别函数（窗口全量加载）
# ============================================================

def get_all_links() -> list[dict]:
    """获取所有分销链接"""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM distribution_links ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_commissions(status: str = None) -> list[dict]:
    """获取所有佣金记录（可选按状态过滤）"""
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM commissions WHERE status=? ORDER BY id DESC LIMIT 200",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM commissions ORDER BY id DESC LIMIT 200"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_team_members() -> list[dict]:
    """获取所有团队成员"""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM team_members ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_distribution_stats() -> dict:
    """获取分销全局统计"""
    conn = _connect()
    links = conn.execute("SELECT COUNT(*) FROM distribution_links").fetchone()[0]
    clicks = conn.execute("SELECT COALESCE(SUM(click_count),0) FROM distribution_links").fetchone()[0]
    comms = conn.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM commissions").fetchone()
    team = conn.execute("SELECT COUNT(*) FROM team_members").fetchone()[0]
    conn.close()
    return {
        "links": links,
        "clicks": int(clicks),
        "commissions_count": comms[0],
        "commissions_amount": comms[1],
        "team_size": team
    }


def update_commission_status(comm_id: int, status: str) -> dict:
    """更新佣金状态（approved/rejected/paid/pending）"""
    conn = _connect()
    conn.execute("UPDATE commissions SET status=? WHERE id=?", (status, comm_id))
    conn.commit()
    row = conn.execute("SELECT * FROM commissions WHERE id=?", (comm_id,)).fetchone()
    conn.close()
    if not row:
        return {"ok": False, "error": "记录不存在"}
    r = dict(row)
    # ── 审批通过 → 同步到云端 ──────────────────────
    try:
        from core.supabase_client import CloudCommission
        CloudCommission.upsert(
            user_id=r["user_id"], amount=r["amount"],
            from_user_id=r.get("from_user_id"), type_=r.get("type", "direct"),
            status=status, description=r.get("description")
        )
    except Exception as e:
        print(f"[Distribution] 云端同步失败 (非阻塞): {e}")
    return {"ok": True, "status": status}

def delete_commission(comm_id: int) -> dict:
    """删除佣金记录"""
    conn = _connect()
    conn.execute("DELETE FROM commissions WHERE id=?", (comm_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

def update_link_status(link_id: int, status: str) -> dict:
    """更新链接状态（active/inactive）"""
    conn = _connect()
    conn.execute("UPDATE distribution_links SET status=? WHERE id=?", (status, link_id))
    conn.commit()
    conn.close()
    try:
        from core.supabase_client import CloudDistribution
        row = _connect().execute("SELECT * FROM distribution_links WHERE id=?", (link_id,)).fetchone()
        if row:
            r = dict(row)
            CloudDistribution.upsert(user_id=r["user_id"], code=r["code"], url=r["url"],
                click_count=r["click_count"], register_count=r["register_count"],
                total_commission=0, status=status)
    except Exception as e:
        print(f"[Distribution] 云端同步失败 (非阻塞): {e}")
    return {"ok": True, "status": status}

def delete_link(link_id: int) -> dict:
    """删除分销链接"""
    conn = _connect()
    conn.execute("DELETE FROM distribution_links WHERE id=?", (link_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

def remove_team_member(member_id: int) -> dict:
    """移除团队成员"""
    conn = _connect()
    conn.execute("DELETE FROM team_members WHERE id=?", (member_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

def search_commissions(user_id: int = None, date_from: str = None, date_to: str = None,
                       comm_type: str = None, status: str = None) -> list[dict]:
    """高级搜索佣金记录"""
    conn = _connect()
    conditions = []
    params = []
    if user_id is not None:
        conditions.append("user_name = ?")
        params.append(user_id)
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to + " 23:59:59")
    if comm_type:
        conditions.append("type = ?")
        params.append(comm_type)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"SELECT * FROM commissions WHERE {where} ORDER BY id DESC LIMIT 500"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def export_commissions_csv(filepath: str = None) -> dict:
    """导出佣金记录为 CSV"""
    import csv
    if not filepath:
        filepath = os.path.join(DATA_DIR, f"commissions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    rows = search_commissions()
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["ID", "用户ID", "来源用户", "金额", "类型", "状态", "备注", "时间"])
        for r in rows:
            w.writerow([r["id"], r["user_id"], r.get("from_user_id", ""),
                        r["amount"], r.get("type", ""), r.get("status", ""),
                        r.get("description", ""), r.get("created_at", "")])
    return {"ok": True, "filepath": filepath, "count": len(rows)}

def export_team_csv(filepath: str = None) -> dict:
    """导出团队数据为 CSV"""
    import csv
    if not filepath:
        filepath = os.path.join(DATA_DIR, f"team_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    rows = get_all_team_members()
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["ID", "用户ID", "上级ID", "层级", "加入时间"])
        for r in rows:
            w.writerow([r["id"], r["user_id"], r["parent_id"], r.get("level", 1), r.get("created_at", "")])
    return {"ok": True, "filepath": filepath, "count": len(rows)}


if __name__ == "__main__":
    print("分销服务测试")
    link = create_link(user_id=1)
    print(f"  创建链接: {link.get('code', 'error')}")
    links = get_user_links(1)
    print(f"  用户链接数: {len(links)}")
    comm = add_commission(user_id=1, amount=50, from_user_id=2, description="推荐奖励")
    print(f"  添加佣金: {comm}")
    total = get_total_commission(1)
    print(f"  总佣金: {total}")
