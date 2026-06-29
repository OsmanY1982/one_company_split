# -*- coding: utf-8 -*-
"""
手机版 HTTP API
为手机版应用提供 RESTful API 接口
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs

from core.paths import DATA_DIR
from core.database import get_conn, close_conn


class MobileAPIHandler(BaseHTTPRequestHandler):
    """手机版 API 请求处理器"""
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        try:
            if path == '/api/health':
                self._json_response({"status": "ok", "version": "1.0.0", "time": datetime.now().isoformat()})
            elif path == '/api/dashboard':
                self._handle_dashboard(params)
            elif path == '/api/orders':
                self._handle_orders(params)
            elif path == '/api/customers':
                self._handle_customers(params)
            elif path == '/api/products':
                self._handle_products(params)
            elif path == '/api/finance':
                self._handle_finance(params)
            elif path.startswith('/api/sync/'):
                self._handle_sync(path)
            else:
                self._json_response({"error": "Not found"}, 404)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)
    
    def do_POST(self):
        """处理 POST 请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body) if body else {}
        
        parsed = urlparse(self.path)
        path = parsed.path
        
        try:
            if path == '/api/sync/push':
                self._handle_sync_push(data)
            else:
                self._json_response({"error": "Not found"}, 404)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)
    
    def _handle_dashboard(self, params):
        """仪表盘数据"""
        result = {}
        db_tables = {
            "customer.db": "customers",
            "product.db": "products", 
            "order.db": "orders",
            "finance.db": "finance_records"
        }
        for db_name, table_name in db_tables.items():
            db_path = os.path.join(DATA_DIR, db_name)
            if os.path.exists(db_path):
                conn = get_conn(db_name)
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                result[table_name] = count
                close_conn(db_name)
            else:
                result[table_name] = 0
        self._json_response(result)
    
    def _handle_orders(self, params):
        """订单列表"""
        limit = int(params.get('limit', [20])[0])
        offset = int(params.get('offset', [0])[0])
        db_path = os.path.join(DATA_DIR, "order.db")
        orders = []
        if os.path.exists(db_path):
            conn = get_conn("order.db")
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
                orders = [dict(r) for r in cursor.fetchall()]
            except Exception:
                pass
            close_conn("order.db")
        self._json_response({"orders": orders, "limit": limit, "offset": offset})
    
    def _handle_customers(self, params):
        """客户列表"""
        limit = int(params.get('limit', [50])[0])
        keyword = params.get('keyword', [''])[0]
        db_path = os.path.join(DATA_DIR, "customer.db")
        customers = []
        if os.path.exists(db_path):
            conn = get_conn("customer.db")
            if keyword:
                cursor = conn.execute(
                    "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? LIMIT ?",
                    (f'%{keyword}%', f'%{keyword}%', limit)
                )
            else:
                cursor = conn.execute("SELECT * FROM customers LIMIT ?", (limit,))
            customers = [dict(r) for r in cursor.fetchall()]
            close_conn("customer.db")
        self._json_response({"customers": customers})
    
    def _handle_products(self, params):
        """产品列表"""
        limit = int(params.get('limit', [50])[0])
        db_path = os.path.join(DATA_DIR, "product.db")
        products = []
        if os.path.exists(db_path):
            conn = get_conn("product.db")
            cursor = conn.execute("SELECT * FROM products LIMIT ?", (limit,))
            products = [dict(r) for r in cursor.fetchall()]
            close_conn("product.db")
        self._json_response({"products": products})
    
    def _handle_finance(self, params):
        """财务数据"""
        db_path = os.path.join(DATA_DIR, "finance.db")
        records = []
        if os.path.exists(db_path):
            conn = get_conn("finance.db")
            cursor = conn.execute("SELECT * FROM finance_records ORDER BY created_at DESC LIMIT 100")
            records = [dict(r) for r in cursor.fetchall()]
            close_conn("finance.db")
        self._json_response({"finance_records": records})
    
    def _handle_sync(self, path):
        """同步接口"""
        self._json_response({"sync": "ok", "method": path}, 200)
    
    def _handle_sync_push(self, data):
        """接收手机端推送的数据"""
        self._json_response({"received": True, "count": len(data)}, 200)
    
    def _json_response(self, data, code=200):
        """发送 JSON 响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"[MobileAPI] {args[0]}" if args else "")


def start_server(host: str = '127.0.0.1', port: int = 8899):
    """启动手机版 API 服务器"""
    server = HTTPServer((host, port), MobileAPIHandler)
    print(f"[MobileAPI] 服务器已启动: http://{host}:{port}")
    print(f"[MobileAPI] 仪表盘: http://{host}:{port}/api/dashboard")
    return server


if __name__ == "__main__":
    print("=" * 40)
    print("手机版 API 服务测试")
    print("=" * 40)
    server = start_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()
