# -*- coding: utf-8 -*-
"""
RAG 注入器 — 统一上下文构建
所有对话入口通过本模块自动注入知识库 + 业务数据
"""

from typing import Tuple


# 业务数据关键词（触发 DB 查询）
DATA_KEYWORDS = [
    "经营", "销售", "订单", "库存", "财务", "客户", "会员",
    "营收", "利润", "产品", "进货", "补货", "日报", "分析",
    "统计", "报表", "汇总", "数据", "趋势", "预警", "盘点",
    "收入", "支出", "成本", "毛利", "净利",
]


def build_context(user_message: str) -> Tuple[str, int]:
    """
    构建增强上下文前缀。

    Returns:
        (enhanced_prefix, rag_hit_count)
    """
    blocks = []
    hit_count = 0

    # ① 知识库 RAG
    try:
        from core.modules.intelligence.knowledge_base import knowledge_base
        rag = knowledge_base.retrieve_context(user_message, top_k=3)
        if rag:
            blocks.append(
                "请参考以下知识库内容回答用户问题。如果知识库内容与问题无关，请忽略。\n\n" + rag
            )
            hit_count = rag.count("### [")
    except Exception:
        pass

    # ② 业务数据注入
    if any(kw in user_message for kw in DATA_KEYWORDS):
        try:
            from core.modules.intelligence.offline_analyzer import gather_context
            db_ctx = gather_context()
            if db_ctx:
                blocks.append(
                    "以下为当前系统实际业务数据，请据此精确回答。"
                    "如果某些数据为零或不存在，请如实说明。\n\n" + db_ctx
                )
        except Exception:
            pass

    if not blocks:
        return user_message, 0

    prefix = "\n\n---\n\n".join(blocks)
    enhanced = f"{prefix}\n\n---\n\n用户问题: {user_message}"
    return enhanced, hit_count


def has_data_intent(text: str) -> bool:
    """检测是否涉及业务数据查询"""
    return any(kw in text for kw in DATA_KEYWORDS)
