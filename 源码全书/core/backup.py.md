# `core/backup.py`

> 路径：`core/backup.py` | 行数：415


---


```python
# -*- coding: utf-8 -*-


import os
import sys
import json
import time
import shutil
import hashlib
import zipfile
import secrets
import traceback
import struct
from pathlib import Path
from datetime import datetime

# 动态获取项目根目录（支持直接导入）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 配置 ──────────────────────────────────────────────
PROJECT_ROOT   = Path(BASE_DIR)
BACKUP_DIR     = PROJECT_ROOT / "backup"
BACKUP_DIR_NAME = BACKUP_DIR.name
HISTORY_FILE   = PROJECT_ROOT / "data" / "修改历史记录.json"
BACKUP_LOG     = PROJECT_ROOT / "backup" / "backup_log.txt"
MAX_BACKUP_COUNT = 30

# 加密标识头
ENC_MAGIC = b"OPCBAK_V2\x00"
# 备份加密密钥（固定密钥，只有系统知道）
_BACKUP_SECRET = "OPC_Backup_Master_Key_2026_OneCompany"

IGNORE_DIRS = {"__pycache__", ".git", ".idea", "node_modules", "venv", "env", ".vscode"}

# 需要备份的文件类型
BACKUP_EXTENSIONS = {
    # 数据
    ".db", ".csv",
    # 代码
    ".py", ".ui",
    # 配置 & 文档
    ".json", ".txt", ".md",
    # 加密文件（密码保险箱、加密笔记）
    ".enc", ".opc", ".opcbak",
    # 媒体（支付二维码、图标等）
    ".png", ".jpg", ".jpeg", ".ico", ".gif",
}
# 排除的文件（日志、临时文件）
EXCLUDE_FILES = {"backup_log.txt"}
# 这些目录内容不备份（录屏输出等大文件）
EXCLUDE_DIRS_CONTENT = {"recordings"}


# ══════════════════════════════════════════════════════
#  加密核心
# ══════════════════════════════════════════════════════
def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def _xor_bytes(data: bytes, key: bytes) -> bytes:
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

def encrypt_backup(data: bytes, password: str = _BACKUP_SECRET) -> bytes:
    
    salt    = os.urandom(16)
    key     = _derive_key(password, salt)
    enc     = _xor_bytes(data, key)
    # 格式：MAGIC(10) + SALT(16) + DATA_LEN(4) + ENC_DATA
    data_len = struct.pack('>I', len(enc))
    return ENC_MAGIC + salt + data_len + enc

def decrypt_backup(data: bytes, password: str = _BACKUP_SECRET) -> bytes:
    
    if not data.startswith(ENC_MAGIC):
        raise ValueError("不是有效的加密备份文件（格式不匹配）")
    offset   = len(ENC_MAGIC)
    salt     = data[offset:offset + 16]
    offset  += 16
    data_len = struct.unpack('>I', data[offset:offset + 4])[0]
    offset  += 4
    enc      = data[offset:offset + data_len]
    key      = _derive_key(password, salt)
    return _xor_bytes(enc, key)

def is_encrypted_backup(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as f:
            return f.read(len(ENC_MAGIC)) == ENC_MAGIC
    except Exception:
        return False


# ══════════════════════════════════════════════════════
#  日志
# ══════════════════════════════════════════════════════
def _log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode('gbk', errors='replace').decode('gbk'))
    try:
        BACKUP_DIR.mkdir(exist_ok=True, parents=True)
        with open(BACKUP_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  JSON 历史记录
# ══════════════════════════════════════════════════════
def init_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not HISTORY_FILE.exists():
            HISTORY_FILE.write_text(
                json.dumps({"修改历史": []}, ensure_ascii=False, indent=4),
                encoding="utf-8"
            )
    except Exception as e:
        _log(f"[警告] 无法创建历史记录文件：{e}")

def add_history(backup_name, desc="手动备份", encrypted=True, db_count=0, py_count=0):
    init_history()
    temp_file = HISTORY_FILE.with_suffix(".json.tmp")
    try:
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {"修改历史": []}
        data["修改历史"].append({
            "备份时间":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "备份文件名": backup_name,
            "修改说明":   desc,
            "加密":       encrypted,
            "数据库文件": db_count,
            "代码文件":   py_count,
        })
        temp_file.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        os.replace(temp_file, HISTORY_FILE)
    except Exception as e:
        if temp_file.exists():
            try: temp_file.unlink()
            except: pass
        _log(f"[错误] 历史记录写入失败：{e}")


# ══════════════════════════════════════════════════════
#  备份核心
# ══════════════════════════════════════════════════════
def auto_backup(desc="手动备份", encrypt=True):
    from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
    BACKUP_DIR.mkdir(exist_ok=True, parents=True)
    timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ms_suffix   = int(time.time() * 1000) % 1000
    backup_name = f"备份_{timestamp}_{ms_suffix}.opcbak" if encrypt else f"备份_{timestamp}_{ms_suffix}"
    backup_path = BACKUP_DIR / backup_name

    try:
        # ── 1. 收集文件 ──
        files_to_backup = []  # [(相对路径, 绝对路径)]
        db_count = py_count = 0

        for root, dirs, files in os.walk(PROJECT_ROOT):
            root_path = Path(root)
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS
                and d != BACKUP_DIR_NAME
                and d not in EXCLUDE_DIRS_CONTENT
                and not d.startswith(".")
            ]
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                ext = Path(file).suffix.lower()
                if ext not in BACKUP_EXTENSIONS:
                    continue
                file_path = root_path / file
                try:
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                except ValueError:
                    continue
                if BACKUP_DIR_NAME in rel_path.parts:
                    continue
                files_to_backup.append((str(rel_path), file_path))
                if ext == ".db":
                    db_count += 1
                elif ext == ".py":
                    py_count += 1

        _log(f"收集到 {len(files_to_backup)} 个文件（{db_count} 个数据库，{py_count} 个代码）")

        if not files_to_backup:
            return False, "没有找到需要备份的文件", None

        if encrypt:
            # ── 2a. 加密备份：先打 ZIP 到内存，再加密写文件 ──
            import io
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for rel_path, abs_path in files_to_backup:
                    try:
                        zf.write(abs_path, rel_path)
                    except Exception as e:
                        _log(f"[警告] 跳过 {rel_path}：{e}")
            zip_data = zip_buffer.getvalue()

            # 加密
            enc_data = encrypt_backup(zip_data)
            with open(backup_path, 'wb') as f:
                f.write(enc_data)

            size_mb = backup_path.stat().st_size / 1024 / 1024
            _log(f"✅ 加密备份完成：{backup_name}（{size_mb:.2f} MB）")

        else:
            # ── 2b. 明文备份：直接复制到文件夹 ──
            backup_path.mkdir(parents=True, exist_ok=True)
            for rel_path, abs_path in files_to_backup:
                dest = backup_path / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(abs_path, dest)
                except Exception as e:
                    _log(f"[警告] 复制失败 {rel_path}：{e}")

        # ── 3. 写历史记录 ──
        add_history(backup_name, desc, encrypted=encrypt, db_count=db_count, py_count=py_count)

        # ── 4. 清理旧备份 ──
        _cleanup_old_backups()

        msg = (f"备份成功！\n"
               f"• 数据库文件：{db_count} 个\n"
               f"• 代码文件：{py_count} 个\n"
               f"• 总计：{len(files_to_backup)} 个文件\n"
               f"• 加密：{'是（.opcbak）' if encrypt else '否'}\n"
               f"• 位置：{backup_path}")
        return True, msg, backup_path

    except Exception as e:
        _log(f"[错误] 备份失败：{e}\n{traceback.format_exc()}")
        # 清理残留
        if backup_path and backup_path.exists():
            try:
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            except Exception:
                pass
        return False, f"备份失败：{e}", None


# ══════════════════════════════════════════════════════
#  恢复
# ══════════════════════════════════════════════════════
def restore_backup(backup_path_str, desc=""):
    from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
    backup_path = Path(backup_path_str)
    if not backup_path.exists():
        return False, f"备份文件不存在：{backup_path}"

    try:
        if backup_path.suffix == ".opcbak" or backup_path.is_file():
            # ── 加密备份恢复 ──
            raw = backup_path.read_bytes()
            try:
                zip_data = decrypt_backup(raw)
            except Exception as e:
                return False, f"解密失败，备份文件可能已损坏：{e}"

            import io
            restored = 0
            with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zf:
                for member in zf.namelist():
                    dest = PROJECT_ROOT / member
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        dest.write_bytes(zf.read(member))
                        restored += 1
                    except Exception as e:
                        _log(f"[警告] 恢复失败 {member}：{e}")

            _log(f"✅ 加密备份恢复完成：{restored} 个文件")
            return True, f"恢复成功！{restored} 个文件已还原（含数据库）"

        elif backup_path.is_dir():
            # ── 旧版文件夹备份恢复 ──
            restored = 0
            for src in backup_path.rglob("*"):
                if not src.is_file():
                    continue
                try:
                    rel_path = src.relative_to(backup_path)
                    dest = PROJECT_ROOT / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    restored += 1
                except Exception as e:
                    _log(f"[警告] 恢复失败：{e}")
            return True, f"恢复成功！{restored} 个文件已还原"

        else:
            return False, "不支持的备份格式"

    except Exception as e:
        _log(f"[错误] 恢复失败：{e}\n{traceback.format_exc()}")
        return False, f"恢复失败：{e}"


# ══════════════════════════════════════════════════════
#  列表 & 清理
# ══════════════════════════════════════════════════════
def list_backups():
    from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
    try:
        if not BACKUP_DIR.exists():
            return []
        items = []
        for p in BACKUP_DIR.iterdir():
            if not p.name.startswith("备份_"):
                continue
            try:
                stat = p.stat()
                size_mb = stat.st_size / 1024 / 1024 if p.is_file() else \
                          sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1024 / 1024
                items.append({
                    "name":      p.name,
                    "path":      str(p),
                    "time":      datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "size":      size_mb,
                    "encrypted": p.suffix == ".opcbak",
                    "py_count":  len(list(p.rglob("*.py"))) if p.is_dir() else 0,
                })
            except Exception:
                continue
        return sorted(items, key=lambda x: x["time"], reverse=True)
    except Exception:
        return []

def _cleanup_old_backups():
    try:
        if not BACKUP_DIR.exists():
            return
        backups = sorted(
            [p for p in BACKUP_DIR.iterdir() if p.name.startswith("备份_")],
            key=lambda p: p.stat().st_mtime, reverse=True
        )
        for old in backups[MAX_BACKUP_COUNT:]:
            try:
                if old.is_dir():
                    shutil.rmtree(old)
                else:
                    old.unlink()
            except Exception as e:
                _log(f"[警告] 删除旧备份失败：{old.name}，{e}")
    except Exception as e:
        _log(f"[警告] 清理旧备份失败：{e}")

def list_backup_history():
    init_history()
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data.get("修改历史", [])
    except Exception:
        return []


# ══════════════════════════════════════════════════════
#  命令行入口
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="系统备份工具 v2")
    parser.add_argument("action", choices=["backup", "restore", "list"],
                        help="backup=备份 | restore=恢复 | list=列出备份")
    parser.add_argument("--path", help="restore 时传入备份文件路径")
    parser.add_argument("--no-encrypt", action="store_true", help="不加密（默认加密）")
    args = parser.parse_args()

    if args.action == "backup":
        ok, msg, _ = auto_backup("命令行手动备份", encrypt=not args.no_encrypt)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.action == "list":
        backups = list_backups()
        if not backups:
            print("暂无备份")
        for b in backups:
            enc = "🔐" if b["encrypted"] else "📁"
            print(f"{enc} {b['name']}  |  {b['time']}  |  {b['size']:.1f} MB")

    elif args.action == "restore":
        if not args.path:
            backups = list_backups()
            for i, b in enumerate(backups):
                enc = "🔐" if b["encrypted"] else "📁"
                print(f"[{i+1}] {enc} {b['name']}  {b['time']}  {b['size']:.1f} MB")
            choice = input("选择编号：").strip()
            try:
                path = backups[int(choice)-1]["path"]
            except Exception:
                print("无效选择")
                sys.exit(1)
        else:
            path = args.path
        ok, msg = restore_backup(path)
        print(msg)
        sys.exit(0 if ok else 1)

```
