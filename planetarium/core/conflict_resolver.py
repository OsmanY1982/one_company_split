# -*- coding: utf-8 -*-
"""
冲突解决策略优化
实现字段级合并、冲突日志记录、自动备份
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class ConflictStrategy(Enum):
    """冲突解决策略"""
    LAST_WRITE_WINS = "last_write_wins"
    FIELD_LEVEL_MERGE = "field_level_merge"
    VERSION_COMPARE = "version_compare"
    MANUAL_REVIEW = "manual_review"


@dataclass
class ConflictRecord:
    """冲突记录"""
    id: str
    table_name: str
    record_id: str
    local_data: Dict
    cloud_data: Dict
    strategy: str
    resolution: Dict
    resolved_at: str
    status: str  # pending, resolved, failed


class ConflictResolver:
    """冲突解决器"""
    
    def __init__(self):
        self.conflicts_db = os.path.join(DATA_DIR, 'sync_conflicts.db')
        self._init_conflicts_db()
    
    def _init_conflicts_db(self):
        """初始化冲突数据库"""
        conn = sqlite3.connect(self.conflicts_db)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conflicts (
                id TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                local_data TEXT,
                cloud_data TEXT,
                strategy TEXT,
                resolution TEXT,
                resolved_at TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def detect_conflict(self, table_name: str, local_record: Dict, cloud_record: Dict) -> Tuple[bool, List[str]]:
        """检测冲突字段"""
        conflict_fields = []
        common_fields = set(local_record.keys()) & set(cloud_record.keys())
        
        for field in common_fields:
            if field in ['id', 'created_at', 'sync_version', 'last_modified_by', 'last_sync_at']:
                continue
            local_val = local_record.get(field)
            cloud_val = cloud_record.get(field)
            if local_val != cloud_val:
                conflict_fields.append(field)
        
        return len(conflict_fields) > 0, conflict_fields
    
    def resolve_conflict(self, table_name: str, local_record: Dict, cloud_record: Dict,
                        strategy: ConflictStrategy = ConflictStrategy.FIELD_LEVEL_MERGE) -> Dict:
        """解决冲突"""
        has_conflict, conflict_fields = self.detect_conflict(table_name, local_record, cloud_record)
        
        if not has_conflict:
            return {**cloud_record, **local_record}
        
        conflict_id = f"{table_name}_{local_record.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if strategy == ConflictStrategy.LAST_WRITE_WINS:
            local_version = local_record.get('sync_version', 0)
            cloud_version = cloud_record.get('sync_version', 0)
            if local_version >= cloud_version:
                resolution = local_record.copy()
                resolution['sync_version'] = local_version + 1
            else:
                resolution = cloud_record.copy()
                resolution['sync_version'] = cloud_version + 1
                
        elif strategy == ConflictStrategy.FIELD_LEVEL_MERGE:
            resolution = {}
            all_fields = set(local_record.keys()) | set(cloud_record.keys())
            for field in all_fields:
                if field in conflict_fields:
                    local_version = local_record.get('sync_version', 0)
                    cloud_version = cloud_record.get('sync_version', 0)
                    if local_version >= cloud_version:
                        resolution[field] = local_record.get(field)
                    else:
                        resolution[field] = cloud_record.get(field)
                else:
                    resolution[field] = local_record.get(field) if field in local_record else cloud_record.get(field)
            resolution['sync_version'] = max(
                local_record.get('sync_version', 0),
                cloud_record.get('sync_version', 0)
            ) + 1
            
        elif strategy == ConflictStrategy.VERSION_COMPARE:
            local_version = local_record.get('sync_version', 0)
            cloud_version = cloud_record.get('sync_version', 0)
            if local_version > cloud_version:
                resolution = local_record.copy()
            elif cloud_version > local_version:
                resolution = cloud_record.copy()
            else:
                resolution = cloud_record.copy()
                
        elif strategy == ConflictStrategy.MANUAL_REVIEW:
            self._save_conflict(conflict_id, table_name, local_record, cloud_record, strategy)
            return None
        
        self._save_conflict(conflict_id, table_name, local_record, cloud_record, strategy, resolution)
        return resolution
    
    def _save_conflict(self, conflict_id: str, table_name: str, local_data: Dict, 
                      cloud_data: Dict, strategy: ConflictStrategy, resolution: Dict = None):
        """保存冲突记录"""
        conn = sqlite3.connect(self.conflicts_db)
        conn.execute('''
            INSERT OR REPLACE INTO conflicts 
            (id, table_name, record_id, local_data, cloud_data, strategy, resolution, resolved_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            conflict_id, table_name, str(local_data.get('id', 'unknown')),
            json.dumps(local_data, ensure_ascii=False),
            json.dumps(cloud_data, ensure_ascii=False),
            strategy.value,
            json.dumps(resolution, ensure_ascii=False) if resolution else None,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'resolved' if resolution else 'pending'
        ))
        conn.commit()
        conn.close()
    
    def get_pending_conflicts(self, table_name: str = None) -> List[ConflictRecord]:
        """获取待处理的冲突"""
        conn = sqlite3.connect(self.conflicts_db)
        if table_name:
            cursor = conn.execute(
                'SELECT * FROM conflicts WHERE status = ? AND table_name = ? ORDER BY created_at DESC',
                ('pending', table_name)
            )
        else:
            cursor = conn.execute(
                'SELECT * FROM conflicts WHERE status = ? ORDER BY created_at DESC',
                ('pending',)
            )
        conflicts = []
        for row in cursor.fetchall():
            conflicts.append(ConflictRecord(
                id=row[0], table_name=row[1], record_id=row[2],
                local_data=json.loads(row[3]) if row[3] else {},
                cloud_data=json.loads(row[4]) if row[4] else {},
                strategy=row[5],
                resolution=json.loads(row[6]) if row[6] else {},
                resolved_at=row[7], status=row[8]
            ))
        conn.close()
        return conflicts
    
    def resolve_manual_conflict(self, conflict_id: str, chosen_data: Dict, resolution_note: str = '') -> bool:
        """人工解决冲突"""
        try:
            conn = sqlite3.connect(self.conflicts_db)
            conn.execute('''
                UPDATE conflicts 
                SET resolution = ?, status = 'resolved', resolved_at = ?, 
                    resolution_note = ?
                WHERE id = ?
            ''', (
                json.dumps(chosen_data, ensure_ascii=False),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                resolution_note, conflict_id
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Error] 解决冲突失败: {e}")
            return False


def resolve_conflict(table_name: str, local_record: Dict, cloud_record: Dict,
                    strategy: str = 'field_level_merge') -> Dict:
    resolver = ConflictResolver()
    strategy_enum = ConflictStrategy(strategy)
    return resolver.resolve_conflict(table_name, local_record, cloud_record, strategy_enum)


if __name__ == '__main__':
    print("=" * 60)
    print("冲突解决策略测试")
    print("=" * 60)
    resolver = ConflictResolver()
    local = {
        'id': 1, 'name': '产品A', 'price': 100, 'stock': 50,
        'sync_version': 5, 'last_modified_by': 'desktop'
    }
    cloud = {
        'id': 1, 'name': '产品A-更新', 'price': 120, 'stock': 45,
        'sync_version': 3, 'last_modified_by': 'mobile'
    }
    print("\n本地数据:", local)
    print("云端数据:", cloud)
    has_conflict, fields = resolver.detect_conflict('products', local, cloud)
    print(f"\n冲突字段: {fields}")
    for strategy in ConflictStrategy:
        if strategy == ConflictStrategy.MANUAL_REVIEW:
            continue
        result = resolver.resolve_conflict('products', local, cloud, strategy)
        print(f"\n[{strategy.value}] 解决结果:")
        print(f"  {result}")
    print("\n测试完成!")
