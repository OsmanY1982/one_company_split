import sys, os, inspect, re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "core"))

errors = []

# ===== 1. cloud_sync.py =====
try:
    from core import cloud_sync
    db = getattr(cloud_sync, 'DB_PATHS', {})
    cm = getattr(cloud_sync, 'COLUMN_MAPPING', {})
    cc = getattr(cloud_sync, 'CONFLICT_COLUMNS', {})
    
    db_keys = set(db.keys())
    cm_keys = set(cm.keys())
    cc_keys = set(cc.keys())
    
    print(f"cloud_sync DB_PATHS: {len(db)}")
    print(f"cloud_sync COLUMN_MAPPING: {len(cm)}")
    print(f"cloud_sync CONFLICT_COLUMNS: {len(cc)}")
    
    missing_in_cm = db_keys - cm_keys
    missing_in_cc = db_keys - cc_keys
    if missing_in_cm:
        errors.append(f"DB_PATHS中有但COLUMN_MAPPING中无: {missing_in_cm}")
    if missing_in_cc:
        errors.append(f"DB_PATHS中有但CONFLICT_COLUMNS中无: {missing_in_cc}")
    
    # 统计 sync_xxx 函数
    funcs = [n for n in dir(cloud_sync) if n.startswith('sync_')]
    print(f"sync_xxx 函数数: {len(funcs)}")
    
    # 获取 sync_all 源码统计注册
    src = inspect.getsource(cloud_sync.sync_all)
    calls = re.findall(r'sync_\w+\(', src)
    print(f"sync_all() 注册数: {len(calls)}")
    
    # 检查是否有本地DB文件存在
    for k, v in db.items():
        local_path = os.path.join(PROJECT_ROOT, v.get('local_file', '')) if isinstance(v, dict) else ''
        if isinstance(v, dict):
            local_path = os.path.join(PROJECT_ROOT, 'data', v.get('local_file', ''))
        exists = os.path.exists(local_path) if local_path else False
        if not exists:
            errors.append(f"本地DB不存在: {k} -> {local_path}")
except Exception as e:
    errors.append(f"cloud_sync导入失败: {e}")

# ===== 2. cloud_pull.py =====
try:
    from core import cloud_pull
    tm = getattr(cloud_pull, 'TABLE_META', {})
    cl = getattr(cloud_pull, 'CLOUD_TO_LOCAL', {})
    
    tm_keys = set(tm.keys())
    cl_keys = set(cl.keys())
    
    print(f"cloud_pull TABLE_META: {len(tm)}")
    print(f"cloud_pull CLOUD_TO_LOCAL: {len(cl)}")
    
    missing = tm_keys - cl_keys
    if missing:
        errors.append(f"TABLE_META中有但CLOUD_TO_LOCAL中无: {missing}")
except Exception as e:
    errors.append(f"cloud_pull导入失败: {e}")

# ===== 3. auth 模块 =====
auth_modules = [
    'modules.auth.auth_service',
    'modules.auth.login_window',
    'modules.auth.dao.user_dao',
    'modules.auth.dao.session_dao',
    'modules.supabase.auth',
]
for mod in auth_modules:
    try:
        __import__(mod)
        print(f"导入 {mod}: OK")
    except Exception as e:
        errors.append(f"导入失败 {mod}: {e}")

# ===== 4. main.py sys.path =====
main_path = os.path.join(PROJECT_ROOT, 'main.py')
if not os.path.exists(main_path):
    main_path = os.path.join(PROJECT_ROOT, 'core', 'main.py')
if os.path.exists(main_path):
    with open(main_path) as f:
        content = f.read()
    inserts = len(re.findall(r'sys\.path\.insert\(0', content))
    appends = len(re.findall(r'sys\.path\.append\(', content))
    print(f"main.py sys.path: {inserts} insert + {appends} append")
else:
    errors.append("main.py 不存在")

# ===== 汇总 =====
print("\n===== 结果 =====")
if errors:
    print(f"FAIL: {len(errors)} 项未通过")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL PASS: 全部通过")
