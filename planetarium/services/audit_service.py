"""
Audit Service - 操作日志审计服务
完整的操作追踪、用户行为分析、异常检测
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum


class AuditAction(Enum):
    """审计操作类型"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    PRINT = "PRINT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    TRANSFER = "TRANSFER"


class AuditLevel(Enum):
    """审计级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditService:
    """审计服务"""
    
    def __init__(self, db_path: str = "data/audit.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化审计数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 主审计日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT NOT NULL,
                user_name TEXT,
                action TEXT NOT NULL,
                level TEXT DEFAULT 'INFO',
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                resource_name TEXT,
                old_values TEXT,
                new_values TEXT,
                changes TEXT,
                ip_address TEXT,
                user_agent TEXT,
                session_id TEXT,
                status TEXT DEFAULT 'SUCCESS',
                error_message TEXT,
                duration_ms INTEGER,
                checksum TEXT,
                metadata TEXT
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_action ON audit_logs(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource ON audit_logs(resource_type, resource_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON audit_logs(level)")
        
        # 数据变更历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_log_id INTEGER,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by TEXT,
                FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id)
            )
        """)
        
        # 异常检测规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rule_type TEXT NOT NULL,
                condition TEXT NOT NULL,
                level TEXT DEFAULT 'WARNING',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 插入默认规则
        self._init_default_rules(cursor)
        
        conn.commit()
        conn.close()
    
    def _init_default_rules(self, cursor):
        """初始化默认审计规则"""
        rules = [
            ("批量删除", "单次删除超过10条记录", "BATCH_DELETE", "action='DELETE' AND batch_size>10", "WARNING"),
            ("异常时间操作", "非工作时间（22:00-06:00）的操作", "OFF_HOURS", "strftime('%H', timestamp) NOT BETWEEN '06' AND '22'", "WARNING"),
            ("频繁登录失败", "5分钟内登录失败超过3次", "LOGIN_FAIL", "action='LOGIN' AND status='FAILED'", "ERROR"),
            ("敏感数据访问", "访问敏感字段（密码、身份证等）", "SENSITIVE", "resource_type IN ('user_password', 'id_card', 'bank_card')", "CRITICAL"),
            ("数据导出", "大量数据导出（超过1000条）", "EXPORT", "action='EXPORT' AND batch_size>1000", "WARNING"),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO audit_rules (name, description, rule_type, condition, level)
            VALUES (?, ?, ?, ?, ?)
        """, rules)
    
    def log(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        level: AuditLevel = AuditLevel.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """记录审计日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算变更内容
        changes = None
        if old_values and new_values:
            changes = self._calculate_changes(old_values, new_values)
        
        # 生成校验和
        data_string = f"{user_id}:{action.value}:{resource_type}:{resource_id}:{datetime.now().isoformat()}"
        checksum = hashlib.sha256(data_string.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO audit_logs 
            (user_id, action, level, resource_type, resource_id, resource_name,
             old_values, new_values, changes, ip_address, user_agent, session_id,
             status, error_message, duration_ms, checksum, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, action.value, level.value, resource_type, resource_id, resource_name,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            json.dumps(changes) if changes else None,
            ip_address, user_agent, session_id,
            status, error_message, duration_ms,
            checksum,
            json.dumps(metadata) if metadata else None
        ))
        
        audit_id = cursor.lastrowid
        
        # 记录详细变更历史
        if changes:
            for field_name, change in changes.items():
                cursor.execute("""
                    INSERT INTO data_history 
                    (audit_log_id, table_name, record_id, field_name, old_value, new_value, changed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit_id, resource_type, resource_id or 'N/A',
                    field_name, str(change.get('old')), str(change.get('new')),
                    user_id
                ))
        
        conn.commit()
        conn.close()
        
        # 检查异常
        self._check_anomalies(audit_id, user_id, action, resource_type)
        
        return audit_id
    
    def _calculate_changes(self, old_values: Dict, new_values: Dict) -> Dict:
        """计算变更内容"""
        changes = {}
        all_keys = set(old_values.keys()) | set(new_values.keys())
        
        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val
                }
        
        return changes
    
    def _check_anomalies(self, audit_id: int, user_id: str, action: AuditAction, resource_type: str):
        """检查异常操作"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取活跃规则
        cursor.execute("""
            SELECT id, name, condition, level 
            FROM audit_rules 
            WHERE is_active = 1
        """)
        
        rules = cursor.fetchall()
        
        for rule_id, rule_name, condition, level in rules:
            # 简单的规则匹配（实际项目中可以使用更复杂的规则引擎）
            if self._match_condition(condition, action, resource_type):
                # 更新日志级别
                cursor.execute("""
                    UPDATE audit_logs 
                    SET level = ? 
                    WHERE id = ?
                """, (level, audit_id))
                
                conn.commit()
        
        conn.close()
    
    def _match_condition(self, condition: str, action: AuditAction, resource_type: str) -> bool:
        """匹配条件（简化版）"""
        # 这里可以实现更复杂的条件匹配逻辑
        if "action='DELETE'" in condition and action == AuditAction.DELETE:
            return True
        if "action='LOGIN'" in condition and action == AuditAction.LOGIN:
            return True
        if "action='EXPORT'" in condition and action == AuditAction.EXPORT:
            return True
        return False
    
    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """获取审计日志"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if action:
            query += " AND action = ?"
            params.append(action.value)
        
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        
        if level:
            query += " AND level = ?"
            params.append(level.value)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            log = dict(row)
            # 解析JSON字段
            for field in ['old_values', 'new_values', 'changes', 'metadata']:
                if log.get(field):
                    try:
                        log[field] = json.loads(log[field])
                    except:
                        pass
            logs.append(log)
        
        conn.close()
        return logs
    
    def get_statistics(self, days: int = 30) -> Dict:
        """获取审计统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 操作统计
        cursor.execute("""
            SELECT action, COUNT(*) as count
            FROM audit_logs
            WHERE timestamp >= ?
            GROUP BY action
        """, (start_date.isoformat(),))
        
        action_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 用户活跃度
        cursor.execute("""
            SELECT user_id, COUNT(*) as count
            FROM audit_logs
            WHERE timestamp >= ?
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        """, (start_date.isoformat(),))
        
        user_stats = [{"user_id": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # 异常统计
        cursor.execute("""
            SELECT level, COUNT(*) as count
            FROM audit_logs
            WHERE timestamp >= ? AND level IN ('WARNING', 'ERROR', 'CRITICAL')
            GROUP BY level
        """, (start_date.isoformat(),))
        
        anomaly_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 每日趋势
        cursor.execute("""
            SELECT date(timestamp) as day, COUNT(*) as count
            FROM audit_logs
            WHERE timestamp >= ?
            GROUP BY day
            ORDER BY day
        """, (start_date.isoformat(),))
        
        daily_trend = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "period_days": days,
            "total_operations": sum(action_stats.values()),
            "action_breakdown": action_stats,
            "top_users": user_stats,
            "anomalies": anomaly_stats,
            "daily_trend": daily_trend
        }
    
    def get_data_history(self, resource_type: str, resource_id: str) -> List[Dict]:
        """获取数据变更历史"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT h.*, a.timestamp, a.user_name
            FROM data_history h
            JOIN audit_logs a ON h.audit_log_id = a.id
            WHERE h.table_name = ? AND h.record_id = ?
            ORDER BY h.changed_at DESC
        """, (resource_type, resource_id))
        
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
        
        conn.close()
        return history
    
    def export_logs(self, start_date: datetime, end_date: datetime, format: str = "json") -> str:
        """导出审计日志"""
        logs = self.get_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if format == "json":
            return json.dumps(logs, ensure_ascii=False, indent=2)
        elif format == "csv":
            # 简化的CSV导出
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return output.getvalue()
        
        return ""
    
    def cleanup_old_logs(self, days: int = 365) -> int:
        """清理旧日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 先删除关联的历史记录
        cursor.execute("""
            DELETE FROM data_history 
            WHERE changed_at < ?
        """, (cutoff_date.isoformat(),))
        
        # 再删除审计日志
        cursor.execute("""
            DELETE FROM audit_logs 
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count


# 装饰器：自动记录审计日志
def audit_log(
    action: AuditAction,
    resource_type: str,
    get_resource_id=None,
    get_old_values=None,
    get_new_values=None
):
    """审计日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取旧值（如果是更新操作）
            old_values = None
            if get_old_values:
                try:
                    old_values = get_old_values(*args, **kwargs)
                except:
                    pass
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 获取新值
            new_values = None
            if get_new_values:
                try:
                    new_values = get_new_values(result)
                except:
                    pass
            
            # 获取资源ID
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(result)
                except:
                    pass
            
            # 记录审计日志
            service = AuditService()
            service.log(
                user_id="system",  # 应该从上下文获取当前用户
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values
            )
            
            return result
        
        return wrapper
    return decorator


# 便捷函数
def log_login(user_id: str, ip_address: str = None, success: bool = True):
    """记录登录日志"""
    service = AuditService()
    service.log(
        user_id=user_id,
        action=AuditAction.LOGIN,
        resource_type="session",
        ip_address=ip_address,
        status="SUCCESS" if success else "FAILED",
        error_message=None if success else "登录失败"
    )


def log_data_change(user_id: str, table: str, record_id: str, 
                    old_data: dict, new_data: dict):
    """记录数据变更"""
    service = AuditService()
    service.log(
        user_id=user_id,
        action=AuditAction.UPDATE,
        resource_type=table,
        resource_id=record_id,
        old_values=old_data,
        new_values=new_data
    )
