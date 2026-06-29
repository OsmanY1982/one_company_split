"""HR管理工具 — 员工考核、招聘、薪酬计算"""

import os
from core.database import get_conn, close_conn
from datetime import datetime

class HRTTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    def _connect(self, db_name):
        # registry_name extraction no longer needed — get_conn accepts .db names
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path): return None
        return get_conn(db_name)

    def employee_performance_review(self, department=None, quarter=None) -> dict:
        """员工绩效考核汇总"""
        db = self._connect("staff.db")
        if not db: return {"error": "员工数据库不存在"}
        try:
            sql = "SELECT * FROM staff" + (" WHERE department=?" if department else "")
            staff = [dict(r) for r in db.execute(sql, (department,) if department else ()).fetchall()]
            
            # 按部门统计
            by_dept = {}
            for s in staff:
                dept = s.get("department","未分配")
                if dept not in by_dept: by_dept[dept] = []
                by_dept[dept].append(s)
            
            # 薪资分析
            salaries = [float(s.get("salary",0)) for s in staff if s.get("salary")]
            avg_salary = round(sum(salaries)/len(salaries),2) if salaries else 0
            
            # 状态分布
            status_dist = {}
            for s in staff:
                st = s.get("status","在职") or "在职"
                status_dist[st] = status_dist.get(st,0)+1
            
            return {
                "total_employees": len(staff),
                "by_department": {k: len(v) for k,v in by_dept.items()},
                "avg_salary": avg_salary,
                "max_salary": max(salaries) if salaries else 0,
                "min_salary": min(salaries) if salaries else 0,
                "status_distribution": status_dist,
                "recommendations": self._hr_recommendations(len(staff), avg_salary, status_dist)
            }
        finally: close_conn('staff.db')

    def _hr_recommendations(self, count, avg_sal, status) -> list:
        recs = []
        if "离职" in status:
            recs.append(f"⚠️ {status['离职']}人离职，建议调查原因并改善留存措施")
        if count > 50 and avg_sal < 5000:
            recs.append("💡 平均薪资偏低，可能影响人才吸引力")
        recs.append(f"📊 {count}名员工，建议每季度进行一次绩效评估")
        return recs

    def recruitment_report(self) -> dict:
        """招聘需求分析报告"""
        db = self._connect("staff.db")
        if not db: return {"error": "无数据"}
        try:
            staff = [dict(r) for r in db.execute("SELECT * FROM staff").fetchall()]
            by_dept = {}
            for s in staff:
                dept = s.get("department","未分配")
                by_dept[dept] = by_dept.get(dept,0) + 1
            
            positions = [s.get("position","") for s in staff if s.get("position")]
            from collections import Counter
            top_positions = Counter(positions).most_common(5)
            
            return {
                "departments": by_dept,
                "top_positions": [{"pos":p,"cnt":c} for p,c in top_positions],
                "recommendations": ["📋 建议根据各部门人数制定年度招聘计划",
                    "📝 关键岗位建议设置AB角备份"]
            }
        finally: close_conn('staff.db')


def register_hr_tools(registry, data_dir):
    from core.modules.intelligence.tool_registry import ToolDefinition
    hr = HRTTools(data_dir)
    registry.add_tool(ToolDefinition(name="employee_performance_review", description="员工绩效考核：部门人数/薪资分析/状态统计/优化建议", parameters={"type":"object","properties":{"department":{"type":"string"},"quarter":{"type":"string"}}}, handler=lambda department="", quarter="": hr.employee_performance_review(department)))
    registry.add_tool(ToolDefinition(name="recruitment_report", description="招聘分析报告：各部门人员结构/热门职位/招聘建议", parameters={"type":"object","properties":{}}, handler=lambda: hr.recruitment_report()))

