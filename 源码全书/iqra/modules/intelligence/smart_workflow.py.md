# `iqra/modules/intelligence/smart_workflow.py`

> 路径：`iqra/modules/intelligence/smart_workflow.py` | 行数：320


---


```python
# -*- coding: utf-8 -*-
"""
智能工作流模块 - 自动化业务流程
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.intelligence.workflow_engine import WorkflowEngine, workflow_engine
from modules.intelligence._stubs import EnhancedAIAssistant
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta


class SmartWorkflowManager:
    """智能工作流管理器"""
    
    def __init__(self):
        self.engine = workflow_engine
        self.assistant = EnhancedAIAssistant()
        self._setup_presets()
    
    def _setup_presets(self):
        """设置业务预设工作流"""
        # 每日销售报告
        if not any(w.name == "Daily Sales Report" for w in self.engine.list_workflows()):
            self.engine.create_preset_workflow('daily_report')
        
        # 数据备份
        if not any(w.name == "Data Backup" for w in self.engine.list_workflows()):
            self.engine.create_preset_workflow('data_backup')
    
    def create_sales_report_workflow(self, period: str = "today") -> Dict[str, Any]:
        """创建销售报告工作流"""
        workflow = self.engine.create_workflow(
            name="Sales Data Analysis Report",
            description=f"Generate sales data analysis report for {period}",
            steps=[
                {
                    "id": "query_sales",
                    "name": "Query Sales Data",
                    "tool_name": "run_code",
                    "params": {
                        "code": f"""
import json
# Simulate sales data query
sales_data = {{
    "period": "{period}",
    "total_sales": 150000,
    "order_count": 45,
    "top_products": ["Product A", "Product B", "Product C"],
    "growth_rate": 12.5
}}
print(json.dumps(sales_data, ensure_ascii=False))
""",
                        "language": "python"
                    },
                },
                {
                    "id": "analyze_trends",
                    "name": "Analyze Sales Trends",
                    "tool_name": "run_code",
                    "params": {
                        "code": f"""
import json
# Simulate trend analysis
trends = {{
    "trend": "upward",
    "growth_areas": ["Online Sales", "New Customers"],
    "recommendations": ["Increase marketing spend", "Expand product line"]
}}
print(json.dumps(trends, ensure_ascii=False))
""",
                        "language": "python"
                    },
                    "depends_on": ["query_sales"],
                },
                {
                    "id": "generate_report",
                    "name": "Generate Report",
                    "tool_name": "run_code",
                    "params": {
                        "code": f"""
import json
from datetime import datetime

report = {{
    "title": "Sales Report - {period}",
    "generated_at": datetime.now().isoformat(),
    "summary": "Sales performance shows positive growth",
    "key_metrics": {{
        "total_sales": "150,000",
        "orders": 45,
        "growth": "12.5%"
    }},
    "recommendations": [
        "Focus on top-performing products",
        "Invest in customer retention",
        "Explore new market segments"
    ]
}}
print(json.dumps(report, ensure_ascii=False, indent=2))
""",
                        "language": "python"
                    },
                    "depends_on": ["analyze_trends"],
                },
            ],
        )
        
        return {
            "success": True,
            "workflow_id": workflow.id,
            "name": workflow.name,
            "steps": len(workflow.steps),
        }
    
    def create_inventory_check_workflow(self) -> Dict[str, Any]:
        """创建库存检查工作流"""
        workflow = self.engine.create_workflow(
            name="Inventory Status Check",
            description="Check inventory levels and generate alerts",
            steps=[
                {
                    "id": "scan_inventory",
                    "name": "Scan Inventory",
                    "tool_name": "run_code",
                    "params": {
                        "code": """
import json
inventory = {
    "total_items": 1250,
    "low_stock": ["Item A", "Item B"],
    "out_of_stock": ["Item C"],
    "last_updated": "2026-06-04"
}
print(json.dumps(inventory, ensure_ascii=False))
""",
                        "language": "python"
                    },
                },
                {
                    "id": "check_alerts",
                    "name": "Check Alerts",
                    "tool_name": "run_code",
                    "params": {
                        "code": """
import json
alerts = {
    "low_stock_count": 2,
    "out_of_stock_count": 1,
    "reorder_needed": True,
    "urgent_items": ["Item C"]
}
print(json.dumps(alerts, ensure_ascii=False))
""",
                        "language": "python"
                    },
                    "depends_on": ["scan_inventory"],
                },
                {
                    "id": "generate_alert_report",
                    "name": "Generate Alert Report",
                    "tool_name": "run_code",
                    "params": {
                        "code": """
import json
from datetime import datetime

report = {
    "title": "Inventory Alert Report",
    "generated_at": datetime.now().isoformat(),
    "status": "Attention Required",
    "alerts": [
        {"level": "high", "item": "Item C", "message": "Out of stock"},
        {"level": "medium", "item": "Item A", "message": "Low stock"},
        {"level": "medium", "item": "Item B", "message": "Low stock"}
    ],
    "actions": [
        "Reorder Item C immediately",
        "Schedule restock for Item A and B",
        "Review inventory thresholds"
    ]
}
print(json.dumps(report, ensure_ascii=False, indent=2))
""",
                        "language": "python"
                    },
                    "depends_on": ["check_alerts"],
                },
            ],
        )
        
        return {
            "success": True,
            "workflow_id": workflow.id,
            "name": workflow.name,
            "steps": len(workflow.steps),
        }
    
    def create_customer_followup_workflow(self) -> Dict[str, Any]:
        """创建客户跟进工作流"""
        workflow = self.engine.create_workflow(
            name="Customer Follow-up",
            description="Follow up with customers and track responses",
            steps=[
                {
                    "id": "get_customers",
                    "name": "Get Customer List",
                    "tool_name": "run_code",
                    "params": {
                        "code": """
import json
customers = [
    {"id": 1, "name": "Customer A", "last_contact": "2026-05-28", "status": "pending"},
    {"id": 2, "name": "Customer B", "last_contact": "2026-06-01", "status": "pending"},
    {"id": 3, "name": "Customer C", "last_contact": "2026-05-30", "status": "completed"}
]
print(json.dumps(customers, ensure_ascii=False))
""",
                        "language": "python"
                    },
                },
                {
                    "id": "generate_messages",
                    "name": "Generate Follow-up Messages",
                    "tool_name": "run_code",
                    "params": {
                        "code": """
import json
messages = [
    {"customer_id": 1, "message": "Hi, just checking in on your recent order."},
    {"customer_id": 2, "message": "We have new products you might be interested in."}
]
print(json.dumps(messages, ensure_ascii=False))
""",
                        "language": "python"
                    },
                    "depends_on": ["get_customers"],
                },
                {
                    "id": "track_responses",
                    "name": "Track Responses",
                    "tool_name": "run_code",
                    "params": {
                        "code": """
import json
from datetime import datetime

report = {
    "title": "Customer Follow-up Report",
    "generated_at": datetime.now().isoformat(),
    "customers_contacted": 2,
    "pending_responses": 2,
    "follow_up_date": (datetime.now() + timedelta(days=3)).isoformat()
}
print(json.dumps(report, ensure_ascii=False, indent=2))
""",
                        "language": "python"
                    },
                    "depends_on": ["generate_messages"],
                },
            ],
        )
        
        return {
            "success": True,
            "workflow_id": workflow.id,
            "name": workflow.name,
            "steps": len(workflow.steps),
        }
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """列出所有可用工作流"""
        workflows = self.engine.list_workflows()
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status.value,
                "steps": len(w.steps),
                "created_at": w.created_at.isoformat(),
            }
            for w in workflows
        ]
    
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """执行工作流"""
        return self.engine.execute_workflow(workflow_id)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        workflow = self.engine.get_workflow(workflow_id)
        if not workflow:
            return {"success": False, "error": "工作流不存在"}
        
        return {
            "success": True,
            "workflow": workflow.to_dict(),
        }


# 全局实例
smart_workflow_manager = SmartWorkflowManager()


if __name__ == "__main__":
    # 测试智能工作流
    manager = SmartWorkflowManager()
    
    # 创建销售报告工作流
    result = manager.create_sales_report_workflow("today")
    print(f"Created: {result}")
    
    # 列出工作流
    workflows = manager.list_available_workflows()
    print(f"\nAvailable workflows: {len(workflows)}")
    for wf in workflows:
        print(f"  - {wf['name']} ({wf['status']})")

```
