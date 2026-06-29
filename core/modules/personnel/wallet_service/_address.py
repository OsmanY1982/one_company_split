# -*- coding: utf-8 -*-
"""
钱包地址簿管理
"""
from ._db import init_address_book_db, _connect


def add_address(owner_user: str, label: str, address: str,
                address_type: str = "user", note: str = "") -> dict:
    if not owner_user or not label or not address:
        return {"ok": False, "error": "owner_user, label, address required"}
    try:
        conn = _connect()
        conn.execute(
            "INSERT INTO address_book (owner_user, label, address, address_type, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (owner_user, label, address, address_type, note)
        )
        conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_addresses(owner_user: str = None) -> list[dict]:
    conn = _connect()
    if owner_user:
        rows = conn.execute(
            "SELECT * FROM address_book WHERE owner_user=? ORDER BY created_at DESC",
            (owner_user,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM address_book ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_address(addr_id: int, label: str = None,
                   address: str = None, note: str = None) -> dict:
    fields, vals = [], []
    if label:   fields.append("label=?");    vals.append(label)
    if address: fields.append("address=?"); vals.append(address)
    if note is not None: fields.append("note=?"); vals.append(note)
    if not fields:
        return {"ok": False, "error": "no fields to update"}
    vals.append(addr_id)
    try:
        conn = _connect()
        conn.execute(
            f"UPDATE address_book SET {', '.join(fields)} WHERE id=?",
            vals
        )
        conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_address(addr_id: int) -> dict:
    try:
        conn = _connect()
        conn.execute("DELETE FROM address_book WHERE id=?", (addr_id,))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
