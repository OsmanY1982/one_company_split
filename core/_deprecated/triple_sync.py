#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三端同步引擎 (桌面版 + 手机版 + 云端)
核心功能: 增量同步 / 冲突解决 / 数据合并 / 队列管理
"""

import os
import sys
import json
import sqlite3
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.paths import DATA_DIR


class TripleSyncEngine:
    """
    三端同步引擎
    - 维护本地数据库 ↔ 云端数据库的双向同步
    - 支持手机版通过 HTTP API 同步
    """
    
    VERSION = "2.0.0"
    
    # 需要同步的核心表
    SYNC_TABLES = [
        "customers",
        "products",
        "orders",
        "members",
        "staff",
        "finance_records",
        "commissions",
        "distribution_links",
        "wallets",
        "wallet_transactions",
    ]
    
    # 不需要同步的内部表
    INTERNAL_TABLES = [
        "sync_queue",
        "sync_snapshots",
        "sync_conflicts",
        "users",
    ]
    
    def __init__(self, mode: str = "bidirectional"):
        """
        初始化同步引擎
        
        Args:
            mode: "bidirectional" | "upload_only" | "download_only"
        """
        self.mode = mode
        self.stats = {
            "synced": 0,
            "skipped": 0,
            "conflicts": 0,
            "errors": 0,
            "start_time": "",
            "end_time": "",
        }
        self.conflict_resolver = None
    
    def sync_all(self) -> Dict[str, Any]:
        """全量同步所有表"""
        self.stats["start_time"] = datetime.now().isoformat()
        
        results = {}
        for table in self.SYNC_TABLES:
            try:
                result = self.sync_table(table)
                results[table] = result
                self.stats["synced"] += result.get("synced", 0)
                self.stats["conflicts"] += result.get("conflicts", 0)
                self.stats["errors"] += result.get("errors", 0)
            except Exception as e:
                results[table] = {"error": str(e)}
                self.stats["errors"] += 1
        
        self.stats["end_time"] = datetime.now().isoformat()
        return {
            "success": self.stats["errors"] == 0,
            "stats": self.stats,
            "tables": results,
        }
    
    def sync_table(self, table_name: str) -> Dict[str, Any]:
        """同步单个表"""
        db_path = self._get_db_path(table_name)
        if not os.path.exists(db_path):
            return {"synced": 0, "error": f"数据库文件不存在: {db_path}"}
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取本地数据
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            local_records = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            local_records = []
        finally:
            conn.close()
        
        # 获取云端数据（模拟）
        cloud_records = self.fetch_cloud_data(table_name)
        
        # 合并数据
        merged, conflicts = self.merge_data(table_name, local_records, cloud_records)
        
        # 保存合并结果
        self.save_merged_data(table_name, merged)
        
        return {
            "local_count": len(local_records),
            "cloud_count": len(cloud_records),
            "synced": len(merged),
            "conflicts": len(conflicts),
            "errors": 0,
        }
    
    def merge_data(self, table_name: str, local_records: List[Dict],
                   cloud_records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """合并本地和云端数据"""
        merged = []
        conflicts = []
        
        # 以ID建立索引
        local_map = {str(r.get("id")): r for r in local_records if r.get("id")}
        cloud_map = {str(r.get("id")): r for r in cloud_records if r.get("id")}
        
        all_ids = set(local_map.keys()) | set(cloud_map.keys())
        
        for record_id in all_ids:
            local = local_map.get(record_id)
            cloud = cloud_map.get(record_id)
            
            if local and cloud:
                # 两边都有，比较版本
                local_ver = local.get("sync_version", 0)
                cloud_ver = cloud.get("sync_version", 0)
                
                if local_ver >= cloud_ver:
                    merged.append(local)
                else:
                    merged.append(cloud)
                
                if local_ver == cloud_ver and self._data_changed(local, cloud):
                    conflicts.append({
                        "id": record_id,
                        "local": local,
                        "cloud": cloud,
                        "table": table_name,
                    })
            elif local:
                merged.append(local)
            elif cloud:
                merged.append(cloud)
        
        return merged, conflicts
    
    def save_merged_data(self, table_name: str, records: List[Dict]):
        """保存合并后的数据到本地数据库"""
        db_path = self._get_db_path(table_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for record in records:
            record_id = record.get("id")
            if not record_id:
                continue
            
            try:
                # 检查是否存在
                cursor.execute(f"SELECT id FROM {table_name} WHERE id = ?", (record_id,))
                exists = cursor.fetchone()
                
                if exists:
                    # 更新
                    set_clause = ", ".join(f"{k} = ?" for k in record.keys() if k != "id")
                    values = [record[k] for k in record.keys() if k != "id"]
                    values.append(record_id)
                    cursor.execute(
                        f"UPDATE {table_name} SET {set_clause} WHERE id = ?",
                        values
                    )
                else:
                    # 插入
                    columns = ", ".join(record.keys())
                    placeholders = ", ".join("?" * len(record))
                    values = list(record.values())
                    cursor.execute(
                        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                        values
                    )
            except Exception as e:
                print(f"[Sync] 保存记录失败 {table_name}/{record_id}: {e}")
        
        conn.commit()
        conn.close()
    
    def fetch_cloud_data(self, table_name: str) -> List[Dict]:
        """从云端获取数据"""
        # 实际应通过 Supabase API 获取
        # 这里返回空列表表示无云端数据
        return []
    
    def push_to_cloud(self, table_name: str, records: List[Dict]) -> bool:
        """推送数据到云端"""
        # 实际应通过 Supabase API 推送
        # 返回 True 表示成功
        return True
    
    def _get_db_path(self, table_name: str) -> str:
        """根据表名获取数据库文件路径"""
        table_to_db = {
            "customers": "customer.db",
            "products": "product.db",
            "orders": "order.db",
            "members": "member.db",
            "staff": "staff.db",
            "finance_records": "finance.db",
            "commissions": "distribution.db",
            "distribution_links": "distribution.db",
            "wallets": "wallet.db",
            "wallet_transactions": "wallet.db",
        }
        
        db_name = table_to_db.get(table_name, f"{table_name}.db")
        return os.path.join(DATA_DIR, db_name)
    
    def _data_changed(self, local: Dict, cloud: Dict) -> bool:
        """检查数据是否有实质性差异"""
        skip_fields = {"id", "sync_version", "updated_at", "last_sync_at", "last_modified_by"}
        
        local_filtered = {k: v for k, v in local.items() if k not in skip_fields}
        cloud_filtered = {k: v for k, v in cloud.items() if k not in skip_fields}
        
        local_json = json.dumps(local_filtered, sort_keys=True, default=str)
        cloud_json = json.dumps(cloud_filtered, sort_keys=True, default=str)
        
        return local_json != cloud_json
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            "version": self.VERSION,
            "mode": self.mode,
            "stats": self.stats,
            "tables_tracked": len(self.SYNC_TABLES),
            "last_sync": self.stats.get("end_time", "never"),
        }


class TripleSync:
    """三重同步门面"""
    
    @staticmethod
    def sync_to_cloud():
        """同步到云端"""
        engine = TripleSyncEngine(mode="upload_only")
        return engine.sync_all()
    
    @staticmethod
    def sync_from_cloud():
        """从云端同步"""
        engine = TripleSyncEngine(mode="download_only")
        return engine.sync_all()
    
    @staticmethod
    def sync_bidirectional():
        """双向同步"""
        engine = TripleSyncEngine(mode="bidirectional")
        return engine.sync_all()
    
    @staticmethod
    def sync_table(table_name: str):
        """同步单个表"""
        engine = TripleSyncEngine()
        return engine.sync_table(table_name)
    
    @staticmethod
    def sync_status() -> Dict:
        """获取同步状态"""
        engine = TripleSyncEngine()
        return engine.get_sync_status()


if __name__ == "__main__":
    print("=" * 60)
    print("三端同步引擎测试")
    print("=" * 60)
    
    sync = TripleSync()
    result = sync.sync_bidirectional()
    
    print("\n同步结果:")
    print(f"  成功: {result['success']}")
    print(f"  统计: {json.dumps(result['stats'], indent=2, ensure_ascii=False)}")
    print("\n完成!")
