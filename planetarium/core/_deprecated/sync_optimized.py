#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步优化器
减少不必要的数据传输，支持增量同步、字段级同步
"""

import json
import hashlib
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@dataclass
class SyncSnapshot:
    """同步快照"""
    table_name: str
    record_id: str
    field_hash: str
    full_hash: str
    updated_at: str


class SyncOptimizer:
    """同步优化器"""
    
    def __init__(self):
        self.snapshot_dir = os.path.join(DATA_DIR, ".sync_snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)
        self._ensure_snapshot_db()
    
    def _ensure_snapshot_db(self):
        """确保快照数据库存在"""
        db_path = os.path.join(self.snapshot_dir, "snapshots.db")
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                field_hash TEXT NOT NULL,
                full_hash TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (table_name, record_id)
            )
        """)
        conn.commit()
        conn.close()
    
    def compute_hash(self, data: Dict) -> str:
        """计算数据哈希"""
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(serialized.encode()).hexdigest()
    
    def compute_field_hash(self, data: Dict, fields: List[str] = None) -> str:
        """计算指定字段的哈希"""
        if fields:
            subset = {k: data.get(k) for k in fields if k in data}
        else:
            subset = data
        return self.compute_hash(subset)
    
    def get_changed_fields(self, table_name: str, record_id: str,
                          new_data: Dict, track_fields: List[str] = None) -> Set[str]:
        """获取变更的字段"""
        if not track_fields:
            track_fields = list(new_data.keys())
        
        snapshot = self.get_snapshot(table_name, record_id)
        if not snapshot:
            # 没有快照，所有字段都算变更
            return set(track_fields)
        
        changed = set()
        for field in track_fields:
            old_val = ""  # 无法从快照恢复原值，仅比对字段
            new_val = str(new_data.get(field, ""))
            old_hash = snapshot.field_hash
            
            # 简单比对：重新计算子集哈希与快照哈希比较
            partial_hash = self.compute_field_hash(new_data, [field])
            if partial_hash != old_hash[:8]:  # 简化比对
                changed.add(field)
        
        return changed
    
    def save_snapshot(self, table_name: str, record_id: str, data: Dict):
        """保存快照"""
        db_path = os.path.join(self.snapshot_dir, "snapshots.db")
        field_hash = self.compute_hash(data)
        full_hash = self.compute_hash(data)
        
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT OR REPLACE INTO snapshots (table_name, record_id, field_hash, full_hash, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (table_name, str(record_id), field_hash, full_hash, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_snapshot(self, table_name: str, record_id: str) -> Optional[SyncSnapshot]:
        """获取快照"""
        db_path = os.path.join(self.snapshot_dir, "snapshots.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("""
            SELECT * FROM snapshots WHERE table_name = ? AND record_id = ?
        """, (table_name, str(record_id)))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SyncSnapshot(
                table_name=row[0], record_id=row[1],
                field_hash=row[2], full_hash=row[3],
                updated_at=row[4]
            )
        return None
    
    def is_changed(self, table_name: str, record_id: str, new_data: Dict) -> bool:
        """检查数据是否变更"""
        snapshot = self.get_snapshot(table_name, record_id)
        if not snapshot:
            return True  # 无快照，视为变更
        
        current_hash = self.compute_hash(new_data)
        return current_hash != snapshot.full_hash
    
    def batch_compare(self, table_name: str, records: List[Dict]) -> List[Dict]:
        """批量比对，返回有变更的记录"""
        changed_records = []
        for record in records:
            record_id = str(record.get("id", ""))
            if not record_id:
                changed_records.append(record)
                continue
            
            if self.is_changed(table_name, record_id, record):
                changed_records.append(record)
                self.save_snapshot(table_name, record_id, record)
        
        return changed_records
    
    def get_incremental_data(self, table_name: str, 
                            last_sync_time: str = None) -> List[Dict]:
        """获取增量数据"""
        db_path = os.path.join(DATA_DIR, f"{table_name}.db")
        if not os.path.exists(db_path):
            return []
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        if last_sync_time:
            cursor = conn.execute("""
                SELECT * FROM {table_name} 
                WHERE updated_at > ?
                ORDER BY updated_at ASC
            """.format(table_name=table_name), (last_sync_time,))
        else:
            cursor = conn.execute("""
                SELECT * FROM {table_name} 
                ORDER BY updated_at ASC
            """.format(table_name=table_name))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    
    def optimize_sync_data(self, table_name: str, data: List[Dict],
                          track_fields: List[str] = None) -> List[Dict]:
        """优化同步数据：仅传输变更的字段"""
        optimized = []
        for record in data:
            record_id = str(record.get("id", ""))
            if not record_id:
                continue
            
            if not self.is_changed(table_name, record_id, record):
                continue
            
            if track_fields:
                changed_fields = self.get_changed_fields(table_name, record_id, record, track_fields)
                optimized_record = {"id": record_id}
                for field in changed_fields:
                    if field in record:
                        optimized_record[field] = record[field]
                optimized.append(optimized_record)
            else:
                optimized.append(record)
            
            self.save_snapshot(table_name, record_id, record)
        
        return optimized
    
    def cleanup_old_snapshots(self, days: int = 30):
        """清理旧快照"""
        db_path = os.path.join(self.snapshot_dir, "snapshots.db")
        conn = sqlite3.connect(db_path)
        conn.execute("""
            DELETE FROM snapshots 
            WHERE updated_at < datetime('now', ?)
        """, (f'-{days} days',))
        count = conn.total_changes
        conn.commit()
        conn.close()
        return count
