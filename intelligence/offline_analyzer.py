"""
离线分析引擎 — 基于本地数据库的业务数据查询与分析
"""
import os
from core.database import get_conn
import traceback
from datetime import datetime

from core.modules.intelligence.ai_chat_styles import DATA_DIR

# ═══════ 数据库文件定义 ═══════
DB_FILES = {
    "order.db": ("orders", "SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders"),
    "product.db": ("product", "SELECT COUNT(*) as c FROM product"),
    "customer.db": ("customer", "SELECT COUNT(*) as c FROM customer"),
    "finance.db": ("finance",
                   "SELECT COALESCE(SUM(CASE WHEN type='收入' THEN amount ELSE 0 END),0) as inc, "
                   "COALESCE(SUM(CASE WHEN type='支出' THEN amount ELSE 0 END),0) as out FROM finance"),
    "member.db": ("member", "SELECT COUNT(*) as c FROM member"),
}


def gather_context(data_dir: str = DATA_DIR) -> str:
    """收集当前业务数据作为 LLM 上下文"""
    parts = []
    for db_name, (label, sql) in DB_FILES.items():
        path = os.path.join(data_dir, db_name)
        if os.path.exists(path):
            try:
                conn = get_conn(db_name)
                row = conn.execute(sql).fetchone()
                if row:
                    d = dict(row)
                    vals = ", ".join(f"{k}={v}" for k, v in d.items())
                    parts.append(f"{label}: {vals}")
            except Exception:
                traceback.print_exc()

    if parts:
        return "当前业务数据：\n" + "\n".join(parts)
    return ""


def offline_analysis(text: str, data_dir: str = DATA_DIR) -> str:
    """增强离线分析：关键词触发不同业务维度的数据库查询与分析"""
    text_lower = text.lower()
    lines = []
    has_data = False

    order_db = os.path.join(data_dir, "order.db")
    product_db = os.path.join(data_dir, "product.db")
    customer_db = os.path.join(data_dir, "customer.db")
    finance_db = os.path.join(data_dir, "finance.db")
    member_db = os.path.join(data_dir, "member.db")

    total_orders = total_revenue = total_customers = total_products = 0
    total_finance_in = total_finance_out = 0.0
    total_members = 0
    low_stock = []

    if os.path.exists(order_db):
        try:
            conn = get_conn('order.db')
            r = conn.execute(
                "SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders"
            ).fetchone()
            total_orders = r["c"]
            total_revenue = r["s"] or 0
            has_data = True
        except Exception:
            traceback.print_exc()

    if os.path.exists(product_db):
        try:
            conn = get_conn('product.db')
            total_products = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]
            low_stock = conn.execute(
                "SELECT name, stock, price FROM product WHERE stock < 10 AND status='在售' "
                "ORDER BY stock ASC LIMIT 5"
            ).fetchall()
        except Exception:
            traceback.print_exc()

    if os.path.exists(customer_db):
        try:
            conn = get_conn('customer.db')
            total_customers = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
        except Exception:
            traceback.print_exc()

    if os.path.exists(finance_db):
        try:
            conn = get_conn('finance.db')
            r_in = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='收入'"
            ).fetchone()[0]
            r_out = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='支出'"
            ).fetchone()[0]
            total_finance_in = r_in or 0
            total_finance_out = r_out or 0
        except Exception:
            traceback.print_exc()

    if os.path.exists(member_db):
        try:
            conn = get_conn('member.db')
            total_members = conn.execute("SELECT COUNT(*) FROM member").fetchone()[0]
        except Exception:
            traceback.print_exc()

    if not has_data:
        return "离线模式：当前无业务数据。请先在业务管理中添加订单/产品/客户等数据。"

    avg_order = total_revenue / total_orders if total_orders > 0 else 0

    finance_keywords = ["财务", "收入", "支出", "利润", "账", "流水", "成本", "盈亏", "赚钱"]
    sales_keywords = ["销售", "订单", "卖", "营业额", "业绩", "营收", "增长", "趋势"]
    product_keywords = ["产品", "商品", "库存", "存货", "缺货", "补货", "热销", "滞销"]
    customer_keywords = ["客户", "顾客", "消费", "价值", "流失", "回购"]
    report_keywords = ["日报", "周报", "月报", "报告", "总结", "分析", "报表", "概括"]
    member_kw = ["会员", "等级", "积分", "vip"]

    triggered = []
    if any(kw in text_lower for kw in finance_keywords):
        triggered.append("finance")
    if any(kw in text_lower for kw in sales_keywords):
        triggered.append("sales")
    if any(kw in text_lower for kw in product_keywords):
        triggered.append("product")
    if any(kw in text_lower for kw in customer_keywords):
        triggered.append("customer")
    if any(kw in text_lower for kw in report_keywords):
        triggered.append("report")
    if any(kw in text_lower for kw in member_kw):
        triggered.append("member")

    if not triggered:
        triggered = ["overview"]

    for tag in triggered:
        if tag == "finance":
            profit = total_finance_in - total_finance_out
            margin = (profit / total_finance_in * 100) if total_finance_in > 0 else 0
            lines.append("<b>【财务分析】</b>")
            lines.append(
                f"  总收入: ¥{total_finance_in:,.2f} | 总支出: ¥{total_finance_out:,.2f}"
            )
            lines.append(f"  净利润: ¥{profit:,.2f} (利润率 {margin:.1f}%)")
            if os.path.exists(finance_db):
                try:
                    conn = get_conn('finance.db')
                    cat_rows = conn.execute(
                        "SELECT category, COALESCE(SUM(amount),0) as amt FROM finance "
                        "WHERE type='支出' GROUP BY category ORDER BY amt DESC LIMIT 5"
                    ).fetchall()
                    if cat_rows:
                        lines.append("  支出分类 TOP5:")
                        for cr in cat_rows:
                            lines.append(f"    - {cr['category']}: ¥{cr['amt']:,.2f}")
                except Exception:
                    traceback.print_exc()
            lines.append("")

        elif tag == "sales":
            lines.append("<b>【销售分析】</b>")
            lines.append(f"  订单总数: {total_orders} 单 | 总营收: ¥{total_revenue:,.2f}")
            lines.append(f"  平均客单价: ¥{avg_order:,.2f}")
            if os.path.exists(order_db):
                try:
                    conn = get_conn('order.db')
                    top_products = conn.execute(
                        "SELECT product_name, COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as amt "
                        "FROM orders GROUP BY product_name ORDER BY cnt DESC LIMIT 5"
                    ).fetchall()
                    trend = conn.execute(
                        "SELECT DATE(created_at) as d, COUNT(*) as cnt, "
                        "COALESCE(SUM(total_amount),0) as amt "
                        "FROM orders WHERE created_at >= DATE('now', '-30 days') "
                        "GROUP BY d ORDER BY d"
                    ).fetchall()
                    if top_products:
                        lines.append("  热销产品 TOP5:")
                        for tp in top_products:
                            lines.append(
                                f"    - {tp['product_name']}: {tp['cnt']}单 / ¥{tp['amt']:,.2f}"
                            )
                    if trend and len(trend) >= 2:
                        first = trend[0]
                        last = trend[-1]
                        growth = "上升" if last["cnt"] > first["cnt"] else "下降"
                        lines.append(
                            f"  近30天趋势: 日订单量{first['cnt']}→{last['cnt']} ({growth}趋势)"
                        )
                except Exception:
                    traceback.print_exc()
            lines.append("")

        elif tag == "product":
            lines.append("<b>【产品分析】</b>")
            lines.append(f"  产品总数: {total_products}")
            if low_stock:
                lines.append(
                    f"  <span style='color:#ff6644;'>⚠ 低库存预警 ({len(low_stock)} 款):</span>"
                )
                for ls in low_stock:
                    lines.append(f"    - {ls[0]}: 库存 {ls[1]}, 售价 ¥{ls[2]:.0f}")
            else:
                lines.append("  库存状态: 正常")
            lines.append("")

        elif tag == "customer":
            lines.append("<b>【客户分析】</b>")
            lines.append(f"  客户总数: {total_customers}")
            if os.path.exists(customer_db):
                try:
                    conn = get_conn('customer.db')
                    level_dist = conn.execute(
                        "SELECT level, COUNT(*) as cnt FROM customer "
                        "GROUP BY level ORDER BY cnt DESC"
                    ).fetchall()
                    if level_dist:
                        lines.append("  客户等级分布:")
                        for ld in level_dist:
                            lines.append(f"    - {ld['level']}: {ld['cnt']} 人")
                except Exception:
                    traceback.print_exc()
            if os.path.exists(order_db):
                try:
                    conn = get_conn('order.db')
                    top_cust = conn.execute(
                        "SELECT customer_name, COUNT(*) as cnt, "
                        "COALESCE(SUM(total_amount),0) as amt "
                        "FROM orders GROUP BY customer_name ORDER BY amt DESC LIMIT 5"
                    ).fetchall()
                    if top_cust:
                        lines.append("  高价值客户 TOP5:")
                        for tc in top_cust:
                            lines.append(
                                f"    - {tc['customer_name']}: {tc['cnt']}单 / ¥{tc['amt']:,.2f}"
                            )
                except Exception:
                    traceback.print_exc()
            lines.append("")

        elif tag == "member":
            lines.append("<b>【会员分析】</b>")
            lines.append(f"  会员总数: {total_members}")
            if os.path.exists(member_db):
                try:
                    conn = get_conn('member.db')
                    levels = conn.execute(
                        "SELECT level, COUNT(*) as cnt FROM member "
                        "GROUP BY level ORDER BY cnt DESC"
                    ).fetchall()
                    if levels:
                        lines.append("  会员等级分布:")
                        for lv in levels:
                            lines.append(f"    - {lv['level']}: {lv['cnt']} 人")
                except Exception:
                    traceback.print_exc()
            lines.append("")

        elif tag == "report":
            profit = total_finance_in - total_finance_out
            lines.append(f"<b>【经营日报 · {datetime.now().strftime('%Y-%m-%d')}】</b>")
            lines.append("━" * 30)
            lines.append(f"  营收: ¥{total_revenue:,.2f} ({total_orders}单)")
            lines.append(
                f"  财务: 收 ¥{total_finance_in:,.2f} / 支 ¥{total_finance_out:,.2f} "
                f"/ 利 ¥{profit:,.2f}"
            )
            lines.append(f"  产品: {total_products} 款在售")
            lines.append(f"  客户: {total_customers} 人 | 会员: {total_members} 人")
            lines.append(f"  客单价: ¥{avg_order:,.2f}")
            if low_stock:
                lines.append(f"  低库存: {len(low_stock)} 款需补货")
            lines.append("━" * 30)
            lines.append("")

        else:  # overview
            profit = total_finance_in - total_finance_out
            lines.append("<b>【经营概览】</b> 基于本地数据分析：")
            lines.append(f"  总订单: {total_orders} 单 | 总营收: ¥{total_revenue:,.2f}")
            lines.append(
                f"  产品数: {total_products} | 客户数: {total_customers} | 会员数: {total_members}"
            )
            lines.append(
                f"  财务: 收入 ¥{total_finance_in:,.2f} - 支出 ¥{total_finance_out:,.2f} "
                f"= 利润 ¥{profit:,.2f}"
            )
            lines.append(f"  客单价: ¥{avg_order:,.2f}")
            if low_stock:
                lines.append(
                    f"  <span style='color:#ff6644;'>⚠ 低库存预警: "
                    f"{', '.join(l[0] for l in low_stock)}</span>"
                )
            lines.append("")
            lines.append(
                "  <span style='color:#888;'>提示: 可输入「销售分析/财务分析/产品分析/生成日报」"
                "获取专项报告</span>"
            )

    return "<br>".join(lines)
