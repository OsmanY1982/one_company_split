# `planetarium/core/modules/intelligence/marketing_tools/_registration.py`

> 路径：`planetarium/core/modules/intelligence/marketing_tools/_registration.py` | 行数：58


---


```python
# -*- coding: utf-8 -*-
from ._core import MarketingTools


def register_marketing_tools(registry, data_dir: str):
    from core.modules.intelligence.tool_registry import ToolDefinition

    marketer = MarketingTools(data_dir)

    registry.add_tool(ToolDefinition(
        name="create_campaign_plan",
        description="创建营销活动策划方案：包含目标受众、渠道选择、预算分配、时间线、KPI 等",
        parameters={
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string", "description": "活动名称"},
                "target_audience": {"type": "string", "description": "目标受众：all(全部)|vip|new(新客户)|potential(潜在)", "enum": ["all", "vip", "new", "potential"]},
                "budget": {"type": "number", "description": "预算金额（可选）"},
                "duration_days": {"type": "integer", "description": "活动天数", "default": 30},
                "channels": {"type": "array", "items": {"type": "string"}, "description": "推广渠道列表（可选）"}
            },
            "required": ["campaign_name"]
        },
        handler=lambda campaign_name, target_audience="all", budget=None, duration_days=30, channels=None:
            marketer.create_campaign_plan(campaign_name, target_audience, budget, duration_days, channels),
    ))

    registry.add_tool(ToolDefinition(
        name="analyze_channel_performance",
        description="分析推广渠道效果：各渠道的订单、收入、ROI 对比",
        parameters={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "分析天数", "default": 30}
            }
        },
        handler=lambda days=30: marketer.analyze_channel_performance(days),
    ))

    registry.add_tool(ToolDefinition(
        name="calculate_conversion_funnel",
        description="计算转化漏斗：分析各阶段转化率和流失点",
        parameters={
            "type": "object",
            "properties": {}
        },
        handler=lambda: marketer.calculate_conversion_funnel(),
    ))

    registry.add_tool(ToolDefinition(
        name="customer_segmentation",
        description="客户分群分析：RFM 模型分群，高价值/成长/普通/沉睡客户",
        parameters={
            "type": "object",
            "properties": {}
        },
        handler=lambda: marketer.customer_segmentation(),
    ))

```
