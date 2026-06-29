# -*- coding: utf-8 -*-
"""
数据对账引擎
本地数据与云端数据一致性校验
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from core.paths import DATA_DIR


class Reconciliation:
    """数据对账引擎"""
    
    CHECK_TABLES = {
        "customers": "customer.db",
        "products": "product.db",
        "orders": "order.db",
        "staff": "staff.db",
        "members": "member.db",
        "finance_records": "finance.db",
    }
    
    def __init__(self):
        self.report_path = os.path.join(DATA_DIR, "reconciliation_report.json")
    
    def check_table(self, table_name: str) -> Dict:
        """检查单表一致性"""
        db_file = self.CHECK_TABLES.get(table_name)
        if not db_file:
            return {"table": table_name, "error": "未知表"}
        
        db_path = os.path.join(DATA_DIR, db_file)
        if not os.path.exists(db_path):
            return {"table": table_name, "local_count": 0, "cloud_count": 0, 
                    "missing_in_cloud": [], "mismatched": []}
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            local_records = [dict(r) for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            local_records = []
        finally:
            conn.close()
        
        cloud_records = self._fetch_cloud_records(table_name)
        
        result = {
            "table": table_name,
            "local_count": len(local_records),
            "cloud_count": len(cloud_records),
            "missing_in_cloud": [],
            "missing_in_local": [],
            "mismatched": [],
        }
        
        local_map = {str(r.get("id")): r for r in local_records if r.get("id")}
        cloud_map = {str(r.get("id")): r for r in cloud_records if r.get("id")}
        
        for rid, rec in local_map.items():
            if rid not in cloud_map:
                result["missing_in_cloud"].append(rid)
            else:
                mismatches = self._compare_records(rec, cloud_map[rid])
                if mismatches:
                    result["mismatched"].append({"record_id": rid, "fields": mismatches})
        
        for rid in cloud_map:
            if rid not in local_map:
                result["missing_in_local"].append(rid)
        
        return result
    
    def _fetch_cloud_records(self, table_name: str) -> List[Dict]:
        """从云端获取数据（模拟）"""
        # 实际应通过 Supabase API 拉取
        return []
    
    def _compare_records(self, local: Dict, cloud: Dict) -> List[str]:
        """比对两条记录"""
        mismatched = []
        common_fields = set(local.keys()) & set(cloud.keys())
        for field in common_fields:
            if field in ("id", "updated_at", "sync_version"):
                continue
            if str(local.get(field)) != str(cloud.get(field)):
                mismatched.append(field)
        return mismatched
    
    @classmethod
    def run_full_reconciliation(cls) -> List[Dict]:
        """执行全量对账"""
        engine = cls()
        reports = []
        print("[Reconciliation] 开始全量对账...")
        for table_name in engine.CHECK_TABLES:
            report = engine.check_table(table_name)
            reports.append(report)
            print(f"  {table_name}: 本地 {report['local_count']} 条, 云端 {report['cloud_count']} 条")
        engine._save_report(reports)
        return reports
    
    def _save_report(self, reports: List[Dict]):
        """保存对账报告"""
        report_data = {
            "time": datetime.now().isoformat(),
            "reports": reports
        }
        try:
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Reconciliation] 保存报告失败: {e}")
    
    def get_last_report(self) -> Optional[Dict]:
        """获取上次对账报告"""
        if os.path.exists(self.report_path):
            with open(self.report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


def get_reconciliation_report(format_type: str = "json") -> Dict:
    """对外接口：获取对账报告"""
    engine = Reconciliation()
    if format_type == "full":
        return {"tables": engine.CHECK_TABLES, "reports": Reconciliation.run_full_reconciliation()}
    last_report = engine.get_last_report()
    if last_report:
        return last_report
    return engine.run_single_check("customers")


if __name__ == "__main__":
    print("=" * 50)
    print("数据对账测试")
    print("=" * 50)
    reports = Reconciliation.run_full_reconciliation()
    total_issues = sum(
        len(r.get("missing_in_cloud", [])) + len(r.get("mismatched", []))
        for r in reports
    )
    if total_issues > 0:
        print(f"\n发现 {total_issues} 个数据不一致问题")
    else:
        print("\n数据一致性检查通过")
