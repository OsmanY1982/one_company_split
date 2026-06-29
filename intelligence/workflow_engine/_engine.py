# -*- coding: utf-8 -*-
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from ._models import WorkflowStatus, StepStatus, WorkflowStep, Workflow


class WorkflowEngine:
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._running = False

    def create_workflow(self, name: str, description: str, steps: List[Dict]) -> Workflow:
        workflow_id = str(uuid.uuid4())
        workflow_steps = []
        for i, step_data in enumerate(steps):
            step = WorkflowStep(
                id=step_data.get("id", f"step_{i}"),
                name=step_data["name"],
                description=step_data.get("description", ""),
                tool_name=step_data["tool_name"],
                params=step_data.get("params", {}),
                depends_on=step_data.get("depends_on", []),
            )
            workflow_steps.append(step)

        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
        )
        self.workflows[workflow_id] = workflow
        return workflow

    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        if workflow_id not in self.workflows:
            return {"success": False, "error": "工作流不存在"}

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        try:
            from core.modules.intelligence.enhanced.enhanced_tools import EnhancedAIAssistant
            assistant = EnhancedAIAssistant()

            completed_steps = set()
            step_results = {}

            while len(completed_steps) < len(workflow.steps):
                executable_steps = [
                    s for s in workflow.steps
                    if s.status == StepStatus.PENDING
                    and all(dep in completed_steps for dep in s.depends_on)
                ]

                if not executable_steps:
                    failed_steps = [s for s in workflow.steps if s.status == StepStatus.FAILED]
                    if failed_steps:
                        workflow.status = WorkflowStatus.FAILED
                        return {
                            "success": False,
                            "error": f"步骤 {failed_steps[0].name} 失败",
                            "workflow": workflow.to_dict(),
                        }
                    break

                for step in executable_steps:
                    step.status = StepStatus.RUNNING
                    step.start_time = datetime.now()

                    try:
                        params = self._resolve_params(step.params, workflow, step_results)
                        result = assistant.execute_tool(step.tool_name, params)

                        if result.get("success"):
                            step.status = StepStatus.COMPLETED
                            step.result = result
                            step_results[step.id] = result
                        else:
                            step.status = StepStatus.FAILED
                            step.error = result.get("error", "未知错误")
                            if not step.params.get("continue_on_error", False):
                                workflow.status = WorkflowStatus.FAILED
                                return {
                                    "success": False,
                                    "error": f"步骤 {step.name} 失败: {step.error}",
                                    "workflow": workflow.to_dict(),
                                }

                        step.end_time = datetime.now()
                        completed_steps.add(step.id)

                    except Exception as e:
                        step.status = StepStatus.FAILED
                        step.error = str(e)
                        step.end_time = datetime.now()
                        if not step.params.get("continue_on_error", False):
                            workflow.status = WorkflowStatus.FAILED
                            return {
                                "success": False,
                                "error": f"步骤 {step.name} 异常: {str(e)}",
                                "workflow": workflow.to_dict(),
                            }
                        completed_steps.add(step.id)

            all_completed = all(s.status == StepStatus.COMPLETED for s in workflow.steps)
            if all_completed:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.now()
                return {
                    "success": True,
                    "message": "工作流执行完成",
                    "workflow": workflow.to_dict(),
                    "step_results": step_results,
                }
            else:
                workflow.status = WorkflowStatus.FAILED
                return {
                    "success": False,
                    "error": "部分步骤未完成",
                    "workflow": workflow.to_dict(),
                    "step_results": step_results,
                }

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            return {
                "success": False,
                "error": f"工作流执行异常: {str(e)}",
                "workflow": workflow.to_dict(),
            }

    def _resolve_params(self, params: Dict, workflow: Workflow, step_results: Dict) -> Dict:
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                parts = value[1:].split(".")
                step_id = parts[0]
                if step_id in step_results:
                    result_value = step_results[step_id]
                    if len(parts) > 1:
                        for part in parts[1:]:
                            if isinstance(result_value, dict):
                                result_value = result_value.get(part, "")
                            else:
                                result_value = str(result_value)
                        resolved[key] = result_value
                    else:
                        resolved[key] = result_value
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[Workflow]:
        return list(self.workflows.values())

    def cancel_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.CANCELLED
                return True
        return False

    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False

    def create_preset_workflow(self, preset_name: str, **kwargs) -> Optional[Workflow]:
        presets = {
            "daily_report": {
                "name": "每日报告生成",
                "description": "自动生成每日业务报告",
                "steps": [
                    {"id": "query_sales", "name": "查询销售数据", "tool_name": "run_code",
                     "params": {"code": f"print('Querying sales data for {kwargs.get('period', 'today')}')", "language": "python"}},
                    {"id": "query_orders", "name": "查询订单数据", "tool_name": "run_code",
                     "params": {"code": "print('Querying orders data')", "language": "python"}},
                    {"id": "generate_report", "name": "生成报告", "tool_name": "run_code",
                     "params": {"code": "print('Generating report')", "language": "python"},
                     "depends_on": ["query_sales", "query_orders"]},
                ],
            },
            "data_backup": {
                "name": "数据备份",
                "description": "备份重要数据到指定位置",
                "steps": [
                    {"id": "list_files", "name": "列出文件", "tool_name": "dir_list",
                     "params": {"path": kwargs.get("source_path", "./data")}},
                    {"id": "backup", "name": "执行备份", "tool_name": "file_write",
                     "params": {"path": kwargs.get("backup_path", "./backup/data.json"), "content": "$list_files.result"},
                     "depends_on": ["list_files"]},
                ],
            },
            "web_scraper": {
                "name": "网页数据采集",
                "description": "自动采集网页数据并保存",
                "steps": [
                    {"id": "navigate", "name": "访问网页", "tool_name": "browser_navigate",
                     "params": {"url": kwargs.get("url", "https://example.com")}},
                    {"id": "extract", "name": "提取内容", "tool_name": "browser_extract", "params": {},
                     "depends_on": ["navigate"]},
                    {"id": "save", "name": "保存数据", "tool_name": "memory_save",
                     "params": {"key": kwargs.get("save_key", "scraped_data"), "value": "$extract.result"},
                     "depends_on": ["extract"]},
                ],
            },
            "system_check": {
                "name": "系统健康检查",
                "description": "检查系统状态并生成报告",
                "steps": [
                    {"id": "check_cpu", "name": "检查CPU使用率", "tool_name": "run_code",
                     "params": {"code": "import psutil; print(f'CPU: {psutil.cpu_percent()}%')", "language": "python"}},
                    {"id": "check_memory", "name": "检查内存使用", "tool_name": "run_code",
                     "params": {"code": "import psutil; mem = psutil.virtual_memory(); print(f'Memory: {mem.percent}%')", "language": "python"}},
                    {"id": "check_disk", "name": "检查磁盘空间", "tool_name": "run_code",
                     "params": {"code": "import psutil; disk = psutil.disk_usage('/'); print(f'Disk: {disk.percent}%')", "language": "python"}},
                    {"id": "generate_health_report", "name": "生成健康报告", "tool_name": "run_code",
                     "params": {"code": "print('System health check completed')", "language": "python"},
                     "depends_on": ["check_cpu", "check_memory", "check_disk"]},
                ],
            },
            "code_review": {
                "name": "代码审查",
                "description": "自动审查代码质量",
                "steps": [
                    {"id": "read_code", "name": "读取代码文件", "tool_name": "file_read",
                     "params": {"path": kwargs.get("file_path", "")}},
                    {"id": "analyze_code", "name": "分析代码", "tool_name": "run_code",
                     "params": {"code": "# Code analysis logic here\nprint('Analyzing code quality...')", "language": "python"},
                     "depends_on": ["read_code"]},
                    {"id": "save_review", "name": "保存审查结果", "tool_name": "memory_save",
                     "params": {"key": f"code_review_{kwargs.get('file_name', 'unknown')}", "value": "$analyze_code.result"},
                     "depends_on": ["analyze_code"]},
                ],
            },
            "batch_file_processing": {
                "name": "批量文件处理",
                "description": "批量处理目录中的文件",
                "steps": [
                    {"id": "list_files", "name": "列出文件", "tool_name": "dir_list",
                     "params": {"path": kwargs.get("source_dir", "./")}},
                    {"id": "process_files", "name": "处理文件", "tool_name": "run_code",
                     "params": {"code": f"# Process files in {kwargs.get('source_dir', './')}\nprint('Processing files...')", "language": "python"},
                     "depends_on": ["list_files"]},
                    {"id": "save_results", "name": "保存结果", "tool_name": "file_write",
                     "params": {"path": kwargs.get("output_file", "./results.json"), "content": "$process_files.result"},
                     "depends_on": ["process_files"]},
                ],
            },
            "sales_report": {
                "name": "销售报告",
                "description": "生成销售数据分析报告",
                "steps": [
                    {"id": "query_sales", "name": "查询销售数据", "tool_name": "run_code",
                     "params": {"code": "import json; print(json.dumps({'period': 'today', 'total_sales': 150000, 'order_count': 45}, ensure_ascii=False))", "language": "python"}},
                    {"id": "analyze_trends", "name": "分析趋势", "tool_name": "run_code",
                     "params": {"code": "import json; print(json.dumps({'trend': 'upward', 'growth': '12.5%'}, ensure_ascii=False))", "language": "python"},
                     "depends_on": ["query_sales"]},
                    {"id": "generate_report", "name": "生成报告", "tool_name": "run_code",
                     "params": {"code": "print('Sales report generated successfully')", "language": "python"},
                     "depends_on": ["analyze_trends"]},
                ],
            },
            "inventory_check": {
                "name": "库存检查",
                "description": "检查库存水平并生成警报",
                "steps": [
                    {"id": "scan_inventory", "name": "扫描库存", "tool_name": "run_code",
                     "params": {"code": "import json; print(json.dumps({'total_items': 1250, 'low_stock': ['Item A', 'Item B'], 'out_of_stock': ['Item C']}, ensure_ascii=False))", "language": "python"}},
                    {"id": "check_alerts", "name": "检查警报", "tool_name": "run_code",
                     "params": {"code": "import json; print(json.dumps({'reorder_needed': True, 'urgent_items': ['Item C']}, ensure_ascii=False))", "language": "python"},
                     "depends_on": ["scan_inventory"]},
                    {"id": "generate_alert_report", "name": "生成警报报告", "tool_name": "run_code",
                     "params": {"code": "print('Inventory alert report generated')", "language": "python"},
                     "depends_on": ["check_alerts"]},
                ],
            },
        }

        if preset_name not in presets:
            return None

        preset = presets[preset_name]
        return self.create_workflow(
            name=preset["name"],
            description=preset["description"],
            steps=preset["steps"],
        )


workflow_engine = WorkflowEngine()
