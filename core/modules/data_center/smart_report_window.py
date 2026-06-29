# -*- coding: utf-8 -*-
"""
智能报表窗口 — 自然语言交互界面
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
from core.smart_report import ask, get_smart_report


class SmartReportWindow:
    """智能报表窗口"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("🤖 智能报表 — 一句话生成")
        self.window.geometry("900x700")
        self.window.configure(bg="#f5f5f5")
        
        self._create_ui()
        self._load_suggestions()
    
    def _create_ui(self):
        """创建界面"""
        # 标题
        title_frame = tk.Frame(self.window, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🤖 智能报表助手",
            font=("微软雅黑", 18, "bold"),
            bg="#2196F3",
            fg="white"
        ).pack(pady=10)
        
        # 输入区域
        input_frame = tk.Frame(self.window, bg="#f5f5f5", padx=20, pady=15)
        input_frame.pack(fill=tk.X)
        
        tk.Label(
            input_frame,
            text="💬 告诉我你想看什么报表：",
            font=("微软雅黑", 11),
            bg="#f5f5f5"
        ).pack(anchor=tk.W)
        
        self.query_entry = tk.Entry(
            input_frame,
            font=("微软雅黑", 12),
            width=60,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor="#2196F3",
            highlightbackground="#ddd"
        )
        self.query_entry.pack(fill=tk.X, pady=5, ipady=8)
        self.query_entry.bind("<Return>", lambda e: self._on_search())
        
        # 按钮区域
        btn_frame = tk.Frame(input_frame, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.search_btn = tk.Button(
            btn_frame,
            text="🚀 生成报表",
            font=("微软雅黑", 11, "bold"),
            bg="#2196F3",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2",
            command=self._on_search
        )
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = tk.Button(
            btn_frame,
            text="📊 导出Excel",
            font=("微软雅黑", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2",
            command=self._on_export,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # 建议区域
        self.suggestion_frame = tk.LabelFrame(
            self.window,
            text="💡 试试这些",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666"
        )
        self.suggestion_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 结果区域
        result_frame = tk.Frame(self.window, bg="#f5f5f5", padx=20, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题标签
        self.result_title = tk.Label(
            result_frame,
            text="",
            font=("微软雅黑", 14, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        self.result_title.pack(anchor=tk.W, pady=5)
        
        # 图表类型标签
        self.chart_type_label = tk.Label(
            result_frame,
            text="",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666"
        )
        self.chart_type_label.pack(anchor=tk.W)
        
        # 数据表格
        table_frame = tk.Frame(result_frame, bg="white", relief=tk.FLAT, bd=1)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建Treeview
        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        
        scrollbar_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        scrollbar_x.pack(fill=tk.X)
        self.tree.configure(xscrollcommand=scrollbar_x.set)
        
        # SQL显示区域
        self.sql_frame = tk.LabelFrame(
            result_frame,
            text="📝 生成的SQL",
            font=("微软雅黑", 9),
            bg="#f5f5f5",
            fg="#999"
        )
        self.sql_frame.pack(fill=tk.X, pady=5)
        
        self.sql_text = tk.Text(
            self.sql_frame,
            height=3,
            font=("Menlo", 9),
            bg="#f8f8f8",
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.sql_text.pack(fill=tk.X, padx=5, pady=5)
        self.sql_text.config(state=tk.DISABLED)
        
        # 状态栏
        self.status_bar = tk.Label(
            self.window,
            text="就绪",
            font=("微软雅黑", 9),
            bg="#e0e0e0",
            fg="#666",
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _load_suggestions(self):
        """加载查询建议"""
        generator = get_smart_report()
        suggestions = generator.get_suggestions()
        
        for suggestion in suggestions:
            btn = tk.Button(
                self.suggestion_frame,
                text=suggestion,
                font=("微软雅黑", 9),
                bg="white",
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda s=suggestion: self._on_suggestion_click(s)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def _on_suggestion_click(self, suggestion: str):
        """点击建议"""
        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, suggestion)
        self._on_search()
    
    def _on_search(self):
        """搜索按钮点击"""
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("提示", "请输入查询内容")
            return
        
        self.status_bar.config(text="正在生成报表...")
        self.window.update()
        
        try:
            # 调用智能报表
            result = ask(query)
            
            if result["success"]:
                self._display_result(result)
                self.status_bar.config(text=f"✅ 报表生成成功 | 数据条数: {len(result['data'])}")
                self.export_btn.config(state=tk.NORMAL)
            else:
                messagebox.showerror("错误", f"生成失败: {result.get('error', '未知错误')}")
                self.status_bar.config(text="❌ 报表生成失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"系统错误: {str(e)}")
            self.status_bar.config(text="❌ 系统错误")
    
    def _display_result(self, result: dict):
        """显示结果"""
        # 更新标题
        self.result_title.config(text=result["title"])
        
        # 更新图表类型
        chart_types = {
            "line": "📈 折线图",
            "bar": "📊 柱状图",
            "pie": "🥧 饼图",
            "table": "📋 表格",
            "kpi": "🎯 KPI指标"
        }
        chart_text = chart_types.get(result["chart_type"], result["chart_type"])
        self.chart_type_label.config(text=f"图表类型: {chart_text}")
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 设置列
        if result["data"]:
            columns = list(result["data"][0].keys())
            self.tree["columns"] = columns
            
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120, anchor=tk.CENTER)
            
            # 插入数据
            for row in result["data"]:
                values = [row.get(col, "") for col in columns]
                self.tree.insert("", tk.END, values=values)
        
        # 显示SQL
        self.sql_text.config(state=tk.NORMAL)
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(1.0, result["sql"])
        self.sql_text.config(state=tk.DISABLED)
        
        # 保存当前结果
        self.current_result = result
    
    def _on_export(self):
        """导出Excel"""
        if not hasattr(self, 'current_result') or not self.current_result:
            messagebox.showwarning("提示", "请先生成报表")
            return
        
        try:
            from core.excel_export import export_to_excel
            
            filename = f"智能报表_{self.current_result['title']}.xlsx"
            export_to_excel(self.current_result["data"], filename)
            
            messagebox.showinfo("成功", f"报表已导出: {filename}")
            self.status_bar.config(text=f"✅ 已导出: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def run(self):
        """运行窗口"""
        if not self.parent:
            self.window.mainloop()


# 便捷函数
def open_smart_report(parent=None):
    """打开智能报表窗口"""
    window = SmartReportWindow(parent)
    window.run()
    return window


if __name__ == "__main__":
    open_smart_report()
