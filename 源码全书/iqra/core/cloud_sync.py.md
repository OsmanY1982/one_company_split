# `iqra/core/cloud_sync.py`

> 路径：`iqra/core/cloud_sync.py` | 行数：483


---


```python
"""
云端同步服务 v3 — 2026-05-23
桌面端 Iqra ↔ Supabase 双向同步
与移动端 cloud_sync_service.dart 共享同一个 Supabase 项目
"""
import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
try:
    from .supabase_client import get_service_client
except ImportError:
    try:
        from iqra.core import get_service_client as _get_service_client
        get_service_client = _get_service_client
    except ImportError:
        get_service_client = lambda: None

# 列名映射：{本地SQLite表名: {本地字段: Supabase字段}}
COLUMN_MAPPINGS = {
    'products': {
        'name': 'name',
        'specs': 'specs',
        'category': 'category',
        'unit_price': 'unit_price',
        'stock': 'stock',
        'status': 'status',
        'note': 'note',
        'created_at': 'created_at',
    },
    'orders': {
        'order_no': 'order_no',
        'customer': 'customer',
        'product': 'product',
        'amount': 'amount',
        'quantity': 'quantity',
        'status': 'status',
        'created_at': 'created_at',
    },
    'customers': {
        'name': 'name',
        'phone': 'phone',
        'email': 'email',
        'address': 'address',
        'company': 'company',
        'note': 'note',
        'created_at': 'created_at',
    },
    'finance': {
        'type': 'type',
        'category': 'category',
        'amount': 'amount',
        'description': 'description',
        'order_no': 'order_no',
        'date': 'date',
        'created_at': 'created_at',
    },
    'staff': {
        'name': 'name',
        'phone': 'phone',
        'email': 'email',
        'position': 'position',
        'department': 'department',
        'salary': 'salary',
        'status': 'status',
        'created_at': 'created_at',
    },
    'wallet': {
        'user_id': 'user_id',
        'balance': 'balance',
        'frozen_amount': 'frozen_amount',
        'total_income': 'total_income',
        'total_withdraw': 'total_withdraw',
        'status': 'status',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    },
    'wallet_transactions': {
        'wallet_id': 'wallet_id',
        'type': 'type',
        'amount': 'amount',
        'balance_after': 'balance_after',
        'description': 'description',
        'related_id': 'related_id',
        'created_at': 'created_at',
    },
    'distribution_links': {
        'user_id': 'user_id',
        'code': 'code',
        'url': 'url',
        'click_count': 'click_count',
        'register_count': 'register_count',
        'total_commission': 'total_commission',
        'status': 'status',
        'created_at': 'created_at',
    },
    'commissions': {
        'user_id': 'user_id',
        'from_user_id': 'from_user_id',
        'amount': 'amount',
        'type': 'type',
        'status': 'status',
        'description': 'description',
        'created_at': 'created_at',
    },
    'team_members': {
        'user_id': 'user_id',
        'parent_id': 'parent_id',
        'username': 'username',
        'level': 'level',
        'total_contribution': 'total_contribution',
        'created_at': 'created_at',
    },
    'users': {
        'username': 'username',
        'user_id': 'user_id',
        'role': 'role',
        'license_type': 'license_type',
        'vip_type': 'vip_type',
        'device_quota': 'device_quota',
        'device_limit': 'device_limit',
        'phone': 'phone',
        'email': 'email',
        'activation_code': 'activation_code',
        'machine_code': 'machine_code',
        'bind_time': 'bind_time',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    },
    'activation_codes': {
        'code': 'code',
        'type': 'type',
        'status': 'status',
        'bound_account': 'bound_account',
        'bound_machine': 'bound_machine',
        'note': 'note',
        'created_at': 'created_at',
        'used_at': 'used_at',
        'expires_at': 'expires_at',
    },
    'activation_records': {
        'code': 'code',
        'user_id': 'user_id',
        'machine_id': 'machine_id',
        'status': 'status',
        'created_at': 'created_at',
        'activated_at': 'activated_at',
    },
    'activation_logs': {
        'code': 'code',
        'user_id': 'user_id',
        'action': 'action',
        'description': 'description',
        'created_at': 'created_at',
    },
    'admins': {
        'username': 'username',
        'password': 'password',
        'role': 'role',
        'created_at': 'created_at',
    },
    'audit_logs': {
        'user_id': 'user_id',
        'action': 'action',
        'target': 'target',
        'description': 'description',
        'created_at': 'created_at',
    },
    'members': {
        'name': 'name',
        'phone': 'phone',
        'email': 'email',
        'level': 'level',
        'points': 'points',
        'rights': 'rights',
        'vip_expire': 'vip_expire',
        'status': 'status',
        'created_at': 'created_at',
    },
    'operation_logs': {
        'user_id': 'user_id',
        'action': 'action',
        'module': 'module',
        'description': 'description',
        'created_at': 'created_at',
    },
    'orders_backup': {
        'order_no': 'order_no',
        'customer_name': 'customer_name',
        'product_name': 'product_name',
        'quantity': 'quantity',
        'unit_price': 'unit_price',
        'total_amount': 'total_amount',
        'status': 'status',
        'note': 'note',
        'created_at': 'created_at',
    },
    'personnel': {
        'name': 'name',
        'phone': 'phone',
        'email': 'email',
        'department': 'department',
        'position': 'position',
        'status': 'status',
        'created_at': 'created_at',
    },
    'schedules': {
        'name': 'name',
        'cron': 'cron',
        'task': 'task',
        'status': 'status',
        'last_run': 'last_run',
        'created_at': 'created_at',
    },
    'sessions': {
        'user_id': 'user_id',
        'token': 'token',
        'ip': 'ip',
        'expires_at': 'expires_at',
        'created_at': 'created_at',
    },
    'sync_logs': {
        'table_name': 'table_name',
        'action': 'action',
        'record_count': 'record_count',
        'status': 'status',
        'error': 'error',
        'created_at': 'created_at',
    },
    'system_logs': {
        'level': 'level',
        'module': 'module',
        'message': 'message',
        'created_at': 'created_at',
    },
    'todos': {
        'title': 'title',
        'description': 'description',
        'priority': 'priority',
        'status': 'status',
        'due_date': 'due_date',
        'created_at': 'created_at',
    },
    'app_config': {
        'key': 'key',
        'value': 'value',
        'description': 'description',
        'created_at': 'created_at',
    },
    'cache_data': {
        'key': 'key',
        'value': 'value',
        'expires_at': 'expires_at',
        'created_at': 'created_at',
    },
}

# 冲突键配置（用于 upsert）
CONFLICT_KEYS = {
    'products': 'name',
    'orders': 'order_no',
    'customers': 'name',
    'finance': None,
    'staff': 'name',
    'wallet': None,
    'wallet_transactions': None,
    'distribution_links': 'code',
    'commissions': None,
    'team_members': None,
    'users': 'username',
    'activation_codes': 'code',
}

class CloudSyncService:
    """云端同步服务"""
    
    def __init__(self, db_path: str = None):
        """
        初始化同步服务
        :param db_path: 本地 SQLite 数据库路径，默认使用桌面端数据目录
        """
        if db_path is None:
            # 默认数据目录
            # 基于项目根目录的相对路径，跨平台兼容
            import os as _os
            self.db_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "sync", "local.db")
        else:
            self.db_path = db_path
        self.supabase = get_service_client()
    
    def _get_db(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _map_to_supabase(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """将本地数据映射为 Supabase 格式"""
        mapping = COLUMN_MAPPINGS.get(table, {})
        result = {}
        for local_col, supabase_col in mapping.items():
            if local_col in row:
                result[supabase_col] = row[local_col]
        return result
    
    def _map_to_local(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """将 Supabase 数据映射为本地格式"""
        mapping = COLUMN_MAPPINGS.get(table, {})
        result = {}
        for local_col, supabase_col in mapping.items():
            if supabase_col in row:
                result[local_col] = row[supabase_col]
        return result
    
    def push_all(self) -> Dict[str, Any]:
        """
        上传全部数据（本地 → 云端）
        使用 service_role key 绕过 RLS
        """
        total = 0
        errors = []
        
        with self._get_db() as db:
            for table in COLUMN_MAPPINGS.keys():
                try:
                    cursor = db.execute(f'SELECT * FROM {table}')
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    
                    if not rows:
                        continue
                    
                    # 转换为字典列表
                    dict_rows = []
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        dict_rows.append(self._map_to_supabase(table, row_dict))
                    
                    conflict_key = CONFLICT_KEYS.get(table)
                    if conflict_key:
                        # 使用 upsert
                        for row in dict_rows:
                            try:
                                self.supabase.table(table).upsert(row).execute()
                                total += 1
                            except Exception as e:
                                errors.append(f'{table} upsert: {e}')
                    else:
                        # 先删除再插入
                        try:
                            self.supabase.table(table).delete().neq('id', 0).execute()
                        except:
                            pass
                        
                        if dict_rows:
                            try:
                                self.supabase.table(table).insert(dict_rows).execute()
                                total += len(dict_rows)
                            except Exception as e:
                                errors.append(f'{table} insert: {e}')
                    
                except Exception as e:
                    errors.append(f'{table}: {e}')
        
        return {
            'ok': len(errors) == 0,
            'msg': f'上传完成，共 {total} 条数据' if not errors else f'上传 {total} 条，{len(errors)} 个错误: {"; ".join(errors)}',
            'total': total,
            'errors': errors
        }
    
    def pull_all(self) -> Dict[str, Any]:
        """
        拉取全部数据（云端 → 本地，全量替换）
        """
        total = 0
        errors = []
        
        with self._get_db() as db:
            for table in COLUMN_MAPPINGS.keys():
                try:
                    # 从云端获取数据
                    response = self.supabase.table(table).select('*').limit(10000).execute()
                    cloud_rows = response.data if response.data else []
                    
                    if not cloud_rows:
                        continue
                    
                    # 转换为本地格式
                    local_rows = [self._map_to_local(table, row) for row in cloud_rows]
                    
                    # 清空本地表
                    db.execute(f'DELETE FROM {table}')
                    
                    # 插入数据
                    for row in local_rows:
                        try:
                            columns = ', '.join(row.keys())
                            placeholders = ', '.join(['?' for _ in row])
                            sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
                            db.execute(sql, list(row.values()))
                            total += 1
                        except Exception as e:
                            errors.append(f'{table} insert: {e}')
                    
                    db.commit()
                    
                except Exception as e:
                    errors.append(f'{table} fetch: {e}')
        
        return {
            'ok': len(errors) == 0,
            'msg': f'恢复完成，共 {total} 条数据' if not errors else f'恢复 {total} 条，{len(errors)} 个错误: {"; ".join(errors)}',
            'total': total,
            'errors': errors
        }
    
    def smart_sync(self) -> Dict[str, Any]:
        """
        智能同步：云端有数据 → 拉取；否则 → 推送
        """
        try:
            if self._has_cloud_data():
                return self.pull_all()
            else:
                return self.push_all()
        except Exception as e:
            return {'ok': False, 'msg': f'智能同步失败: {e}', 'errors': [str(e)]}
    
    def _has_cloud_data(self) -> bool:
        """检查云端是否有数据"""
        try:
            response = self.supabase.table('products').select('id').limit(1).execute()
            return len(response.data) > 0
        except:
            return False
    
    def get_cloud_summary(self) -> Dict[str, int]:
        """获取云端数据概览"""
        summary = {}
        for table in COLUMN_MAPPINGS.keys():
            try:
                response = self.supabase.table(table).select('id').limit(10001).execute()
                summary[table] = len(response.data) if response.data else 0
            except:
                summary[table] = -1
        return summary
    
    def get_local_sync_state(self) -> List[Dict[str, Any]]:
        """获取本地同步状态"""
        result = []
        
        with self._get_db() as db:
            for table in COLUMN_MAPPINGS.keys():
                try:
                    cursor = db.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    result.append({
                        'table': table,
                        'local_count': count,
                    })
                except Exception as e:
                    result.append({
                        'table': table,
                        'local_count': -1,
                        'error': str(e)
                    })
        
        return result

# 便捷函数
def push_all(db_path: str = None) -> Dict[str, Any]:
    """上传全部数据"""
    service = CloudSyncService(db_path)
    return service.push_all()

def pull_all(db_path: str = None) -> Dict[str, Any]:
    """拉取全部数据"""
    service = CloudSyncService(db_path)
    return service.pull_all()

def smart_sync(db_path: str = None) -> Dict[str, Any]:
    """智能同步"""
    service = CloudSyncService(db_path)
    return service.smart_sync()

```
