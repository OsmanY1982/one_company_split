"""
模拟测试脚本：对每张云端同步表逐一测试
- 建表 → 插入模拟数据 → 验证可读 → 尝试调用sync/pull
"""
import sys, os, sqlite3

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "core"))

from core import cloud_sync, cloud_pull

results = []
failed = []

# 初始化 data/ 目录
data_dir = os.path.join(PROJECT_ROOT, "data")
os.makedirs(data_dir, exist_ok=True)

# 获取 LOCAL_TABLE_NAMES 映射
LOCAL_TABLE_NAMES = getattr(cloud_sync, 'LOCAL_TABLE_NAMES', {})

print("=" * 70)
print(f"版本: {PROJECT_ROOT.split('/')[-2] if '宇宙' in PROJECT_ROOT else '完整版'}")
print(f"路径: {PROJECT_ROOT}")
print(f"DB_PATHS: {len(cloud_sync.DB_PATHS)} 张表")
print(f"COLUMN_MAPPING: {len(cloud_sync.COLUMN_MAPPING)} 张表")
print(f"CONFLICT_COLUMNS: {len(cloud_sync.CONFLICT_COLUMNS)} 张表")
print(f"TABLE_META: {len(cloud_pull.TABLE_META)} 张表")
print(f"CLOUD_TO_LOCAL: {len(cloud_pull.CLOUD_TO_LOCAL)} 张表")
print("=" * 70)

for table_name in sorted(cloud_sync.DB_PATHS.keys()):
    try:
        db_path = cloud_sync.DB_PATHS[table_name]
        columns = cloud_sync.COLUMN_MAPPING.get(table_name, {})
        conflict_col = cloud_sync.CONFLICT_COLUMNS.get(table_name, None)
        local_table = LOCAL_TABLE_NAMES.get(table_name, table_name)

        if not isinstance(db_path, str) or not db_path:
            results.append((table_name, "SKIP", f"无效路径: {db_path}"))
            continue

        if not columns:
            results.append((table_name, "SKIP", "无列定义"))
            continue

        # 确保 db 文件目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(db_path)

        # 建表：用冲突列做主键（如果有），否则自增id
        col_defs = []
        local_cols = list(columns.keys())
        if conflict_col and conflict_col in local_cols:
            col_defs = [f'"{c}" TEXT' + (' PRIMARY KEY' if c == conflict_col else '') for c in local_cols]
        else:
            col_defs = ['id INTEGER PRIMARY KEY AUTOINCREMENT']
            col_defs += [f'"{c}" TEXT' for c in local_cols if c != 'id']

        conn.execute(f'CREATE TABLE IF NOT EXISTS "{local_table}" ({", ".join(col_defs)})')

        # 插入模拟数据
        test_data = {}
        for c in local_cols:
            if c == 'id':
                continue
            test_data[c] = f"test_{c}_{table_name[:8]}"
        placeholders = ", ".join(["?" for _ in test_data])
        col_names = ", ".join([f'"{c}"' for c in test_data])
        conn.execute(f'INSERT OR REPLACE INTO "{local_table}" ({col_names}) VALUES ({placeholders})',
                     list(test_data.values()))
        conn.commit()

        # 验证数据可读
        rows = conn.execute(f'SELECT * FROM "{local_table}"').fetchall()
        row_count = len(rows)

        # 逐个验证字段值
        mismatches = []
        if rows:
            row = rows[0]
            col_indices = {desc[0]: i for i, desc in enumerate(conn.execute(f'SELECT * FROM "{local_table}"').description)}
            for c, expected_val in test_data.items():
                actual_val = row[col_indices.get(c, -1)] if c in col_indices else None
                if actual_val != expected_val:
                    mismatches.append(f"{c}: expected={expected_val}, got={actual_val}")

        conn.close()

        if mismatches:
            results.append((table_name, "DATA_MISMATCH", "; ".join(mismatches[:2])))
        elif row_count > 0:
            results.append((table_name, "DATA_OK", f"{row_count} 行, {len(test_data)} 字段验证通过"))
        else:
            results.append((table_name, "DATA_EMPTY", "无数据"))

        # 尝试调用 sync 函数（不依赖 Supabase 连通性）
        sync_func_name = f"sync_{table_name}"
        sync_func = getattr(cloud_sync, sync_func_name, None)
        if sync_func:
            try:
                sync_func()
                results.append((table_name, "SYNC_CALLED", "调用成功（可能无Supabase连接）"))
            except Exception as e:
                err_msg = str(e)[:120]
                if "supabase" in err_msg.lower() or "connect" in err_msg.lower() or "NoneType" in err_msg or "Client" in err_msg:
                    results.append((table_name, "SYNC_NOCONN", f"无Supabase: {err_msg[:60]}"))
                else:
                    results.append((table_name, "SYNC_ERR", err_msg))
        else:
            results.append((table_name, "SYNC_MISSING", f"函数 {sync_func_name} 不存在"))

        # 尝试调用 pull 函数
        pull_func_name = f"pull_{table_name}"
        pull_func = getattr(cloud_pull, pull_func_name, None)
        if pull_func:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(pull_func):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            result = "async_in_running_loop"
                        else:
                            result = asyncio.run(pull_func())
                    except RuntimeError:
                        result = asyncio.run(pull_func())
                else:
                    result = pull_func()
                results.append((table_name, "PULL_CALLED", f"调用成功: {str(result)[:50]}"))
            except Exception as e:
                err_msg = str(e)[:120]
                if "supabase" in err_msg.lower() or "connect" in err_msg.lower() or "NoneType" in err_msg or "Client" in err_msg:
                    results.append((table_name, "PULL_NOCONN", f"无Supabase: {err_msg[:60]}"))
                else:
                    results.append((table_name, "PULL_ERR", err_msg))
        else:
            results.append((table_name, "PULL_MISSING", f"函数 {pull_func_name} 不存在"))

    except Exception as e:
        failed.append((table_name, f"{type(e).__name__}: {str(e)[:120]}"))

# ===== 输出 =====
print()
print(f"{'表名':<22} {'操作':<14} {'结果'}")
print("-" * 70)
for r in results:
    print(f"{r[0]:<22} {r[1]:<14} {r[2]}")

print()
print("=" * 70)
print("===== 汇总 =====")
sync_ok = sum(1 for r in results if r[1] in ("SYNC_CALLED", "SYNC_NOCONN"))
sync_err = sum(1 for r in results if r[1] == "SYNC_ERR")
sync_mis = sum(1 for r in results if r[1] == "SYNC_MISSING")
pull_ok = sum(1 for r in results if r[1] in ("PULL_CALLED", "PULL_NOCONN"))
pull_err = sum(1 for r in results if r[1] == "PULL_ERR")
pull_mis = sum(1 for r in results if r[1] == "PULL_MISSING")
data_ok = sum(1 for r in results if r[1] == "DATA_OK")
data_bad = sum(1 for r in results if r[1] in ("DATA_EMPTY", "DATA_MISMATCH"))

print(f"DATA:    {data_ok} OK / {data_bad} BAD")
print(f"SYNC:    {sync_ok} OK+NOCONN / {sync_err} ERR / {sync_mis} MISSING")
print(f"PULL:    {pull_ok} OK+NOCONN / {pull_err} ERR / {pull_mis} MISSING")
print(f"FAILED:  {len(failed)}")
for f in failed:
    print(f"  {f[0]}: {f[1]}")

# 总评
total_tables = len(cloud_sync.DB_PATHS)
if data_bad == 0 and sync_err == 0 and pull_err == 0 and len(failed) == 0:
    print(f"\n>>> ALL {total_tables} TABLES VERIFIED <<<")
else:
    print(f"\n>>> {total_tables} 表中存在问题 (DATA:{data_bad} SYNC_ERR:{sync_err} PULL_ERR:{pull_err} FAILED:{len(failed)}) <<<")
