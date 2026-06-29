# `core/modules/intelligence/anomaly_detector.py`

> 路径：`core/modules/intelligence/anomaly_detector.py` | 行数：471


---


```python
# -*- coding: utf-8 -*-
"""
异常检测系统 V2
功能：
1. 销售异常检测 - 突然下降/激增
2. 库存异常检测 - 负库存、异常消耗
3. 财务异常检测 - 大额交易、收支异常
4. 客户行为异常 - 频繁退货、异常订单
5. 系统异常检测 - 数据不一致、重复记录
"""

import sys
import os
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from core.modules.intelligence._compat import get_conn


class AnomalyDetector:
    """异常检测系统"""
    
    # 异常严重程度
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_CRITICAL = 'critical'
    
    def __init__(self):
        self.anomalies = []
        
    # ═══════════════════════════════════════════
    # 1. 销售异常检测
    # ═══════════════════════════════════════════
    
    def detect_sales_anomalies(self, days: int = 7) -> List[Dict]:
        """检测销售异常"""
        anomalies = []
        
        try:
            conn = get_conn('order.db')
            
            # 获取历史销售数据
            cursor = conn.execute(
                "SELECT date(created_at) as d, COUNT(*) as cnt, SUM(amount * quantity) as amt "
                "FROM orders WHERE created_at >= date('now', '-30 days') "
                "GROUP BY d ORDER BY d"
            )
            daily_sales = cursor.fetchall()
            
            if len(daily_sales) < 3:
                return anomalies
            
            # 计算统计数据
            amounts = [d[2] for d in daily_sales]
            avg_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            counts = [d[1] for d in daily_sales]
            avg_count = statistics.mean(counts)
            std_count = statistics.stdev(counts) if len(counts) > 1 else 0
            
            # 检测近N天的异常
            recent_sales = daily_sales[-days:]
            
            for date_str, count, amount in recent_sales:
                # 销售额异常低
                if std_amount > 0 and amount < avg_amount - 2 * std_amount:
                    anomalies.append({
                        'type': 'sales_drop',
                        'severity': self.SEVERITY_WARNING,
                        'date': date_str,
                        'message': f'销售额异常下降: ¥{amount:.2f} (平均: ¥{avg_amount:.2f})',
                        'details': {
                            'current_amount': amount,
                            'average': avg_amount,
                            'drop_percent': round((avg_amount - amount) / avg_amount * 100, 2)
                        }
                    })
                
                # 销售额异常高
                elif std_amount > 0 and amount > avg_amount + 2 * std_amount:
                    anomalies.append({
                        'type': 'sales_spike',
                        'severity': self.SEVERITY_INFO,
                        'date': date_str,
                        'message': f'销售额异常激增: ¥{amount:.2f} (平均: ¥{avg_amount:.2f})',
                        'details': {
                            'current_amount': amount,
                            'average': avg_amount,
                            'spike_percent': round((amount - avg_amount) / avg_amount * 100, 2)
                        }
                    })
                
                # 订单数异常低
                if std_count > 0 and count < avg_count - 2 * std_count:
                    anomalies.append({
                        'type': 'order_drop',
                        'severity': self.SEVERITY_WARNING,
                        'date': date_str,
                        'message': f'订单数异常下降: {count}单 (平均: {avg_count:.1f}单)',
                        'details': {
                            'current_count': count,
                            'average': avg_count
                        }
                    })
            
            # 检测零销售日
            cursor = conn.execute(
                "SELECT date(created_at) as d FROM orders WHERE created_at >= date('now', '-7 days') GROUP BY d"
            )
            sales_days = {row[0] for row in cursor.fetchall()}
            
            for i in range(days):
                check_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                if check_date not in sales_days:
                    anomalies.append({
                        'type': 'no_sales',
                        'severity': self.SEVERITY_CRITICAL,
                        'date': check_date,
                        'message': f'{check_date} 无销售记录',
                        'details': {}
                    })
            
        except Exception as e:
            anomalies.append({
                'type': 'error',
                'severity': self.SEVERITY_WARNING,
                'message': f'销售异常检测失败: {str(e)}'
            })
        
        return anomalies
    
    # ═══════════════════════════════════════════
    # 2. 库存异常检测
    # ═══════════════════════════════════════════
    
    def detect_inventory_anomalies(self) -> List[Dict]:
        """检测库存异常"""
        anomalies = []
        
        try:
            conn = get_conn('product.db')
            
            # 负库存
            cursor = conn.execute(
                'SELECT name, stock, price, category FROM product WHERE stock < 0'
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'negative_stock',
                    'severity': self.SEVERITY_CRITICAL,
                    'message': f'产品"{row[0]}"库存为负: {row[1]}',
                    'details': {
                        'product': row[0],
                        'stock': row[1],
                        'price': row[2],
                        'category': row[3]
                    }
                })
            
            # 零库存但有销售记录的产品
            cursor = conn.execute(
                'SELECT p.name, p.stock FROM product p '
                'WHERE p.stock = 0 AND EXISTS '
                '(SELECT 1 FROM orders o WHERE o.product = p.name)'
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'zero_stock_with_sales',
                    'severity': self.SEVERITY_WARNING,
                    'message': f'产品"{row[0]}"库存为零但有销售记录',
                    'details': {'product': row[0]}
                })
            
            # 库存过高（超过平均3倍）
            cursor = conn.execute('SELECT AVG(stock) FROM product')
            avg_stock = cursor.fetchone()[0] or 0
            
            if avg_stock > 0:
                cursor = conn.execute(
                    'SELECT name, stock, price FROM product WHERE stock > ? * 3',
                    (avg_stock,)
                )
                for row in cursor.fetchall():
                    anomalies.append({
                        'type': 'excess_stock',
                        'severity': self.SEVERITY_INFO,
                        'message': f'产品"{row[0]}"库存过高: {row[1]} (平均: {avg_stock:.0f})',
                        'details': {
                            'product': row[0],
                            'stock': row[1],
                            'average': avg_stock
                        }
                    })
            
        except Exception as e:
            anomalies.append({
                'type': 'error',
                'severity': self.SEVERITY_WARNING,
                'message': f'库存异常检测失败: {str(e)}'
            })
        
        return anomalies
    
    # ═══════════════════════════════════════════
    # 3. 财务异常检测
    # ═══════════════════════════════════════════
    
    def detect_finance_anomalies(self, days: int = 7) -> List[Dict]:
        """检测财务异常"""
        anomalies = []
        
        try:
            conn = get_conn('finance.db')
            
            # 大额交易
            cursor = conn.execute(
                "SELECT id, type, amount, category, description, created_at "
                "FROM finance WHERE ABS(amount) > 10000 AND created_at >= date('now', '-7 days')"
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'large_transaction',
                    'severity': self.SEVERITY_INFO,
                    'date': row[5],
                    'message': f'大额{"收入" if row[1] == "income" else "支出"}: ¥{abs(row[2]):.2f} - {row[4]}',
                    'details': {
                        'id': row[0],
                        'type': row[1],
                        'amount': row[2],
                        'category': row[3]
                    }
                })
            
            # 异常收支比
            cursor = conn.execute(
                "SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income, "
                "SUM(CASE WHEN type='expense' THEN ABS(amount) ELSE 0 END) as expense "
                "FROM finance WHERE created_at >= date('now', '-7 days')"
            )
            income, expense = cursor.fetchone()
            income = income or 0
            expense = expense or 0
            
            if expense > 0 and income / expense < 0.5:
                anomalies.append({
                    'type': 'low_income_ratio',
                    'severity': self.SEVERITY_WARNING,
                    'message': f'收支比异常: 收入¥{income:.2f} vs 支出¥{expense:.2f}',
                    'details': {
                        'income': income,
                        'expense': expense,
                        'ratio': round(income / expense, 2)
                    }
                })
            
            # 重复交易检测
            cursor = conn.execute(
                "SELECT amount, category, COUNT(*) as cnt, GROUP_CONCAT(id) as ids "
                "FROM finance WHERE created_at >= date('now', '-7 days') "
                "GROUP BY amount, category HAVING cnt > 1"
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'duplicate_transaction',
                    'severity': self.SEVERITY_WARNING,
                    'message': f'检测到{row[2]}笔相同金额(¥{row[0]:.2f})的{row[1]}交易',
                    'details': {
                        'amount': row[0],
                        'category': row[1],
                        'count': row[2],
                        'ids': row[3]
                    }
                })
            
        except Exception as e:
            anomalies.append({
                'type': 'error',
                'severity': self.SEVERITY_WARNING,
                'message': f'财务异常检测失败: {str(e)}'
            })
        
        return anomalies
    
    # ═══════════════════════════════════════════
    # 4. 客户行为异常检测
    # ═══════════════════════════════════════════
    
    def detect_customer_anomalies(self) -> List[Dict]:
        """检测客户行为异常"""
        anomalies = []
        
        try:
            conn = get_conn('order.db')
            
            # 频繁下单的客户（一天超过5单）
            cursor = conn.execute(
                "SELECT customer, date(created_at) as d, COUNT(*) as cnt "
                "FROM orders WHERE created_at >= date('now', '-7 days') "
                "GROUP BY customer, d HAVING cnt > 5"
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'frequent_orders',
                    'severity': self.SEVERITY_INFO,
                    'date': row[1],
                    'message': f'客户"{row[0]}"单日下单{row[2]}次',
                    'details': {
                        'customer': row[0],
                        'date': row[1],
                        'count': row[2]
                    }
                })
            
            # 大额订单
            cursor = conn.execute(
                "SELECT customer, amount * quantity as total, created_at "
                "FROM orders WHERE amount * quantity > 5000 AND created_at >= date('now', '-7 days')"
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'large_order',
                    'severity': self.SEVERITY_INFO,
                    'date': row[2],
                    'message': f'客户"{row[0]}"大额订单: ¥{row[1]:.2f}',
                    'details': {
                        'customer': row[0],
                        'amount': row[1]
                    }
                })
            
        except Exception as e:
            anomalies.append({
                'type': 'error',
                'severity': self.SEVERITY_WARNING,
                'message': f'客户异常检测失败: {str(e)}'
            })
        
        return anomalies
    
    # ═══════════════════════════════════════════
    # 5. 系统异常检测
    # ═══════════════════════════════════════════
    
    def detect_system_anomalies(self) -> List[Dict]:
        """检测系统异常"""
        anomalies = []
        
        try:
            # 检测重复记录
            conn = get_conn('order.db')
            cursor = conn.execute(
                "SELECT customer, product, amount, COUNT(*) as cnt "
                "FROM orders WHERE created_at >= date('now', '-1 day') "
                "GROUP BY customer, product, amount HAVING cnt > 1"
            )
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'duplicate_order',
                    'severity': self.SEVERITY_WARNING,
                    'message': f'检测到{row[3]}笔重复订单: {row[0]} - {row[1]}',
                    'details': {
                        'customer': row[0],
                        'product': row[1],
                        'amount': row[2],
                        'count': row[3]
                    }
                })
            
            # 检测数据不一致
            cursor = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE amount <= 0 OR quantity <= 0"
            )
            invalid_count = cursor.fetchone()[0]
            if invalid_count > 0:
                anomalies.append({
                    'type': 'invalid_data',
                    'severity': self.SEVERITY_CRITICAL,
                    'message': f'发现{invalid_count}条无效订单数据（金额或数量<=0）',
                    'details': {'count': invalid_count}
                })
            
        except Exception as e:
            anomalies.append({
                'type': 'error',
                'severity': self.SEVERITY_WARNING,
                'message': f'系统异常检测失败: {str(e)}'
            })
        
        return anomalies
    
    # ═══════════════════════════════════════════
    # 综合检测
    # ═══════════════════════════════════════════
    
    def detect_all(self) -> Dict:
        """执行所有异常检测"""
        all_anomalies = []
        
        # 各类异常检测
        all_anomalies.extend(self.detect_sales_anomalies())
        all_anomalies.extend(self.detect_inventory_anomalies())
        all_anomalies.extend(self.detect_finance_anomalies())
        all_anomalies.extend(self.detect_customer_anomalies())
        all_anomalies.extend(self.detect_system_anomalies())
        
        # 按严重程度统计
        severity_count = defaultdict(int)
        for a in all_anomalies:
            severity_count[a.get('severity', 'unknown')] += 1
        
        # 按类型分组
        type_groups = defaultdict(list)
        for a in all_anomalies:
            type_groups[a.get('type', 'unknown')].append(a)
        
        return {
            'status': 'success',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_anomalies': len(all_anomalies),
                'critical': severity_count.get(self.SEVERITY_CRITICAL, 0),
                'warning': severity_count.get(self.SEVERITY_WARNING, 0),
                'info': severity_count.get(self.SEVERITY_INFO, 0)
            },
            'anomalies': all_anomalies,
            'by_type': dict(type_groups)
        }
    
    def get_critical_issues(self) -> List[Dict]:
        """获取关键问题"""
        result = self.detect_all()
        return [a for a in result['anomalies'] if a.get('severity') == self.SEVERITY_CRITICAL]


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def get_anomaly_detector() -> AnomalyDetector:
    """获取异常检测器实例"""
    return AnomalyDetector()


# 测试
if __name__ == '__main__':
    detector = AnomalyDetector()
    
    print("=" * 50)
    print("异常检测系统 V2 测试")
    print("=" * 50)
    
    # 综合检测
    print("\n1. 综合异常检测:")
    result = detector.detect_all()
    print(f"总计异常: {result['summary']['total_anomalies']}")
    print(f"严重: {result['summary']['critical']}, 警告: {result['summary']['warning']}, 信息: {result['summary']['info']}")
    
    # 显示关键问题
    critical = detector.get_critical_issues()
    if critical:
        print("\n2. 关键问题:")
        for issue in critical:
            print(f"  [CRITICAL] {issue['message']}")
    else:
        print("\n2. 无关键问题")

```
