# -*- coding: utf-8 -*-
"""
行业垂直配置系统
支持零售、餐饮、批发三大行业的差异化配置
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class IndustryType(Enum):
    """行业类型"""
    RETAIL = "retail"      # 零售
    CATERING = "catering"  # 餐饮
    WHOLESALE = "wholesale" # 批发


@dataclass
class IndustryConfig:
    """行业配置"""
    name: str                          # 行业名称
    type: IndustryType                 # 类型
    icon: str                          # 图标
    
    # 业务字段映射
    product_fields: Dict[str, str] = field(default_factory=dict)
    order_fields: Dict[str, str] = field(default_factory=dict)
    customer_fields: Dict[str, str] = field(default_factory=dict)
    
    # 报表指标
    kpi_metrics: List[str] = field(default_factory=list)
    
    # 预警规则
    alert_rules: Dict[str, dict] = field(default_factory=dict)
    
    # 数字员工角色
    employee_roles: List[Dict] = field(default_factory=list)
    
    # 工作流模板
    workflow_templates: List[Dict] = field(default_factory=list)
    
    # 术语表
    terminology: Dict[str, str] = field(default_factory=dict)


# ========== 零售行业配置 ==========
RETAIL_CONFIG = IndustryConfig(
    name="零售行业",
    type=IndustryType.RETAIL,
    icon="🛍️",
    
    product_fields={
        "name": "商品名称",
        "category": "品类",
        "price": "零售价",
        "cost": "成本价",
        "stock": "库存",
        "barcode": "条码",
        "sku": "SKU",
        "supplier": "供应商",
        "shelf_life": "保质期",
        "season": "季节"
    },
    
    order_fields={
        "order_no": "订单号",
        "items": "商品明细",
        "total": "总金额",
        "discount": "折扣",
        "payment": "支付方式",
        "member_id": "会员ID",
        "cashier": "收银员",
        "pos_id": "POS机号"
    },
    
    customer_fields={
        "name": "顾客姓名",
        "phone": "手机号",
        "member_level": "会员等级",
        "points": "积分",
        "last_visit": "最近消费",
        "preference": "偏好品类"
    },
    
    kpi_metrics=[
        "销售额",
        "客单价",
        "客流量",
        "转化率",
        "库存周转率",
        "会员复购率",
        "坪效",
        "连带率"
    ],
    
    alert_rules={
        "low_stock": {
            "threshold": 10,
            "message": "商品库存低于安全库存"
        },
        "expiring": {
            "days": 7,
            "message": "商品即将过期"
        },
        "high_return": {
            "rate": 0.05,
            "message": "退货率异常升高"
        }
    },
    
    employee_roles=[
        {
            "id": "retail_sales",
            "name": "零售销售助手",
            "description": "分析销售数据，优化商品陈列",
            "skills": ["销售分析", "库存管理", "会员营销"]
        },
        {
            "id": "retail_buyer",
            "name": "智能采购员",
            "description": "预测需求，优化采购计划",
            "skills": ["需求预测", "供应商管理", "成本控制"]
        },
        {
            "id": "retail_cashier",
            "name": "收银助手",
            "description": "处理收银异常，对账",
            "skills": ["对账", "异常处理", "日结"]
        }
    ],
    
    workflow_templates=[
        {
            "name": "每日开店流程",
            "steps": ["检查库存", "核对价格", "检查设备", "确认促销"]
        },
        {
            "name": "促销活动执行",
            "steps": ["设置促销价", "更新标签", "通知会员", "监控效果"]
        }
    ],
    
    terminology={
        "product": "商品",
        "sale": "销售",
        "inventory": "库存",
        "member": "会员",
        "pos": "收银台",
        "sku": "SKU",
        "category": "品类",
        "promotion": "促销"
    }
)


# ========== 餐饮行业配置 ==========
CATERING_CONFIG = IndustryConfig(
    name="餐饮行业",
    type=IndustryType.CATERING,
    icon="🍽️",
    
    product_fields={
        "name": "菜品名称",
        "category": "菜系",
        "price": "售价",
        "cost": "成本",
        "ingredients": "原料",
        "cooking_time": "制作时间",
        "spiciness": "辣度",
        "is_recommend": "推荐菜",
        "image": "图片"
    },
    
    order_fields={
        "order_no": "订单号",
        "table_no": "桌号",
        "items": "菜品明细",
        "total": "总金额",
        "guests": "人数",
        "waiter": "服务员",
        "kitchen_status": "后厨状态",
        "dining_type": "用餐类型"  # 堂食/外卖/自提
    },
    
    customer_fields={
        "name": "顾客",
        "phone": "电话",
        "visit_count": "到店次数",
        "favorite_dish": "最爱菜品",
        "dietary_restrictions": "忌口",
        "avg_spend": "人均消费"
    },
    
    kpi_metrics=[
        "营业额",
        "翻台率",
        "客单价",
        "上菜速度",
        "食材成本率",
        "差评率",
        "外卖占比",
        "会员消费占比"
    ],
    
    alert_rules={
        "slow_kitchen": {
            "minutes": 20,
            "message": "菜品制作超时"
        },
        "low_ingredient": {
            "threshold": 5,
            "message": "原料库存不足"
        },
        "bad_review": {
            "rating": 3,
            "message": "收到差评需要处理"
        }
    },
    
    employee_roles=[
        {
            "id": "chef_assistant",
            "name": "后厨助手",
            "description": "管理食材库存，优化出菜顺序",
            "skills": ["库存管理", "菜品分析", "成本控制"]
        },
        {
            "id": "service_manager",
            "name": "服务管家",
            "description": "优化服务流程，处理客诉",
            "skills": ["客诉处理", "服务优化", "会员维护"]
        },
        {
            "id": "purchase_assistant",
            "name": "采购助手",
            "description": "预测食材需求，管理供应商",
            "skills": ["需求预测", "供应商管理", "成本控制"]
        }
    ],
    
    workflow_templates=[
        {
            "name": "每日备餐流程",
            "steps": ["检查食材", "预处理", "准备调料", "检查设备"]
        },
        {
            "name": "客诉处理流程",
            "steps": ["道歉安抚", "了解问题", "提出方案", "跟进反馈"]
        }
    ],
    
    terminology={
        "product": "菜品",
        "sale": "点餐",
        "inventory": "食材",
        "member": "会员",
        "table": "餐桌",
        "kitchen": "后厨",
        "dish": "菜品",
        "chef": "厨师"
    }
)


# ========== 批发行业配置 ==========
WHOLESALE_CONFIG = IndustryConfig(
    name="批发行业",
    type=IndustryType.WHOLESALE,
    icon="📦",
    
    product_fields={
        "name": "商品名称",
        "category": "品类",
        "wholesale_price": "批发价",
        "retail_price": "零售价",
        "min_order": "起订量",
        "unit": "单位",
        "supplier": "供应商",
        "warehouse": "仓库",
        "batch_no": "批次号"
    },
    
    order_fields={
        "order_no": "订单号",
        "customer": "客户",
        "items": "商品明细",
        "total": "总金额",
        "payment_terms": "账期",
        "delivery_date": "交货日期",
        "sales_rep": "业务员",
        "status": "订单状态"
    },
    
    customer_fields={
        "name": "客户名称",
        "contact": "联系人",
        "phone": "电话",
        "credit_limit": "信用额度",
        "outstanding": "欠款金额",
        "tier": "客户等级",
        "region": "区域"
    },
    
    kpi_metrics=[
        "销售额",
        "回款率",
        "客单价",
        "订单履约率",
        "库存周转天数",
        "客户流失率",
        "毛利率",
        "新客户开发数"
    ],
    
    alert_rules={
        "overdue_payment": {
            "days": 30,
            "message": "客户欠款超期"
        },
        "low_margin": {
            "rate": 0.10,
            "message": "订单毛利率过低"
        },
        "delivery_delay": {
            "days": 1,
            "message": "交货延迟"
        }
    },
    
    employee_roles=[
        {
            "id": "sales_rep",
            "name": "销售代表",
            "description": "管理客户关系，跟进订单",
            "skills": ["客户管理", "订单跟进", "回款催收"]
        },
        {
            "id": "warehouse_manager",
            "name": "仓库管家",
            "description": "管理库存，优化仓储",
            "skills": ["库存管理", "出入库", "盘点"]
        },
        {
            "id": "credit_controller",
            "name": "风控专员",
            "description": "监控信用风险，催收欠款",
            "skills": ["信用评估", "风险预警", "账款催收"]
        }
    ],
    
    workflow_templates=[
        {
            "name": "新客户开户",
            "steps": ["资质审核", "信用评估", "签订合同", "建立档案"]
        },
        {
            "name": "订单履约流程",
            "steps": ["确认库存", "安排发货", "物流跟踪", "确认收货"]
        }
    ],
    
    terminology={
        "product": "商品",
        "sale": "销售",
        "inventory": "库存",
        "member": "客户",
        "warehouse": "仓库",
        "batch": "批次",
        "credit": "信用",
        "delivery": "发货"
    }
)


# 配置映射
INDUSTRY_CONFIGS = {
    IndustryType.RETAIL: RETAIL_CONFIG,
    IndustryType.CATERING: CATERING_CONFIG,
    IndustryType.WHOLESALE: WHOLESALE_CONFIG
}


def get_industry_config(industry_type: str) -> IndustryConfig:
    """获取行业配置"""
    type_map = {
        "retail": IndustryType.RETAIL,
        "catering": IndustryType.CATERING,
        "wholesale": IndustryType.WHOLESALE,
        "零售": IndustryType.RETAIL,
        "餐饮": IndustryType.CATERING,
        "批发": IndustryType.WHOLESALE
    }
    
    industry = type_map.get(industry_type.lower(), IndustryType.RETAIL)
    return INDUSTRY_CONFIGS[industry]


def get_all_industries() -> List[Dict]:
    """获取所有行业列表"""
    return [
        {"type": "retail", "name": "零售行业", "icon": "🛍️"},
        {"type": "catering", "name": "餐饮行业", "icon": "🍽️"},
        {"type": "wholesale", "name": "批发行业", "icon": "📦"}
    ]


# 全局配置实例
_current_config: Optional[IndustryConfig] = None


def set_industry(industry_type: str):
    """设置当前行业"""
    global _current_config
    _current_config = get_industry_config(industry_type)


def get_current_config() -> IndustryConfig:
    """获取当前行业配置"""
    global _current_config
    if _current_config is None:
        _current_config = RETAIL_CONFIG  # 默认零售
    return _current_config


if __name__ == "__main__":
    # 测试
    config = get_industry_config("catering")
    print("行业:", config.name)
    print("KPI:", config.kpi_metrics)
    print("角色:", [r["name"] for r in config.employee_roles])
