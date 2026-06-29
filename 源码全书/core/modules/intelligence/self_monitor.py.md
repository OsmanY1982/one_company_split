# `core/modules/intelligence/self_monitor.py`

> 路径：`core/modules/intelligence/self_monitor.py` | 行数：115


---


```python
"""AI助手自检 — 监控工具健康、技能覆盖率、Token优化建议"""

import os, json, shutil
from core.database import get_conn, close_conn
from pathlib import Path
from datetime import datetime

# 项目根目录自动检测（modules/intelligence/self_monitor.py → modules/ → one_company_cosmic/）
_PROJECT_ROOT = Path(__file__).parent.parent  # modules/


class SelfMonitor:
    def __init__(self, data_dir: str = None, skills_dir: str = None):
        self.data_dir = data_dir or str(_PROJECT_ROOT.parent / "data")
        self.skills_dir = skills_dir or str(_PROJECT_ROOT / "skills")
    
    def health_check(self) -> dict:
        """全面健康检查"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {},
            "recommendations": []
        }
        
        # 1. 数据库检查
        dbs = ["order.db","product.db","customer.db","staff.db","finance.db"]
        for db in dbs:
            path = os.path.join(self.data_dir, db)
            registry_name = db.replace(".db", "")
            if os.path.exists(path):
                try:
                    con = get_conn(registry_name)
                    tables = [t[0] for t in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                    records = sum(con.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0] for t in tables)
                    report["checks"][db] = {"exists": True, "tables": len(tables), "records": records}
                    close_conn(registry_name)
                except Exception as e:
                    report["checks"][db] = {"error": str(e)}
            else:
                report["checks"][db] = {"exists": False}
        
        # 2. 配置文件检查
        config_files = ["config.yaml","model_config.py","key_manager.py"]
        project_root = str(_PROJECT_ROOT.parent)
        for cf in config_files:
            path = os.path.join(project_root, cf)
            report["checks"]["config_"+cf] = {"exists": os.path.exists(path)}
        
        # 3. 磁盘空间（使用跨平台 shutil.disk_usage）
        disk_free = self._get_disk_space(project_root)
        report["checks"]["disk_space"] = disk_free
        
        # 4. 技能加载检查
        skills_path = os.path.join(self.skills_dir, "builtin")
        if os.path.exists(skills_path):
            skill_dirs = [d.name for d in os.scandir(skills_path) if d.is_dir()]
            report["checks"]["skills_loaded"] = len(skill_dirs)
        else:
            report["checks"]["skills_loaded"] = 0
        
        # 汇总状态
        critical_failures = sum(1 for v in report["checks"].values() 
                               if isinstance(v, dict) and (v.get("exists") == False or "error" in v))
        if critical_failures > 2:
            report["status"] = "warning"
            report["recommendations"].append("多个组件异常，请检查配置")
        
        return report
    
    def _get_disk_space(self, path: str) -> dict:
        """使用 shutil.disk_usage 获取磁盘空间（跨平台）"""
        try:
            usage = shutil.disk_usage(path)
            total = usage.total / (1024**3)
            free = usage.free / (1024**3)
            return {
                "total_gb": round(total, 1),
                "free_gb": round(free, 1),
                "usage_pct": round((total - free) / total * 100, 1)
            }
        except Exception:
            return {"message": "无法获取磁盘信息"}
    
    def token_optimization_suggestions(self) -> dict:
        """Token使用优化建议"""
        return {
            "suggestions": [
                "高频操作创建快捷函数，减少重复Prompt",
                "批量处理多条目而非逐条查询",
                "定期清理对话历史，保留关键上下文",
                "明确指定需要的工具，避免全量加载",
                "缓存结果避免重复计算相同数据",
                f"当前已有{self._tool_count()}个可用工具，按需调用即可",
                "复杂任务用后台线程执行，不阻塞主对话"
            ]
        }
    
    def _tool_count(self):
        try:
            from business_tools import register_business_tools as _register_all
            r = ToolRegistry()
            _register_all(r, self.data_dir)
            return r.count()
        except Exception:
            return "?"


def register_monitor_tools(registry, data_dir):
    # ToolDefinition stub - not available in cosmic
    ToolDefinition = type('ToolDefinition', (), {})
    m = SelfMonitor(data_dir=data_dir)
    registry.add_tool(ToolDefinition(name="health_check", description="AI助手健康检查：数据库/配置/磁盘/技能覆盖状态检测", parameters={"type":"object","properties":{}}, handler=lambda: m.health_check()))
    registry.add_tool(ToolDefinition(name="token_optimization_suggestions", description="Token使用优化建议列表", parameters={"type":"object","properties":{}}, handler=lambda: m.token_optimization_suggestions()))


```
