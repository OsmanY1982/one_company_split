"""
高级筛选窗口
支持多条件组合筛选、排序、模板保存
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Callable, Any
import json


class FilterField:
    """筛选字段定义"""
    def __init__(self, key: str, label: str, field_type: str = 'text'):
        self.key = key
        self.label = label
        self.type = field_type  # text, number, date, boolean, select


class FilterCondition:
    """筛选条件"""
    def __init__(self, field: str = None, operator: str = None, value: Any = None):
        self.field = field
        self.operator = operator
        self.value = value

    def to_dict(self):
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value
        }


class AdvancedFilterWindow:
    """高级筛选窗口"""

    OPERATORS = {
        'equals': '等于',
        'not_equals': '不等于',
        'contains': '包含',
        'starts_with': '开头是',
        'ends_with': '结尾是',
        'greater_than': '大于',
        'less_than': '小于',
        'between': '介于',
        'in': '在列表中',
        'is_null': '为空',
        'is_not_null': '不为空'
    }

    def __init__(self, parent=None, available_fields: List[FilterField] = None,
                 initial_filters: Dict = None, on_apply: Callable = None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("高级筛选")
        self.window.geometry("800x700")
        self.window.configure(bg='#0f172a')

        self.available_fields = available_fields or []
        self.initial_filters = initial_filters or {}
        self.on_apply = on_apply

        self.conditions: List[FilterCondition] = []
        self.filter_params = {
            'sort_field': None,
            'sort_order': 'desc'
        }

        self.condition_frames = []

        self._setup_ui()
        self._load_initial_filters()

    def _setup_ui(self):
        """设置UI"""
        # 主容器
        main_frame = tk.Frame(self.window, bg='#0f172a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title = tk.Label(
            main_frame,
            text="🔍 高级筛选",
            font=('PingFang SC', 18, 'bold'),
            fg='#f8fafc',
            bg='#0f172a'
        )
        title.pack(anchor='w', pady=(0, 20))

        # 条件列表容器
        self.conditions_container = tk.Frame(main_frame, bg='#0f172a')
        self.conditions_container.pack(fill=tk.X, pady=(0, 20))

        # 添加条件按钮
        add_btn = tk.Button(
            main_frame,
            text="➕ 添加筛选条件",
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#3b82f6',
            activebackground='#334155',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self._add_condition
        )
        add_btn.pack(fill=tk.X, pady=(0, 20))

        # 排序设置
        self._create_sort_section(main_frame)

        # 按钮区域
        btn_frame = tk.Frame(main_frame, bg='#0f172a')
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        # 清空按钮
        clear_btn = tk.Button(
            btn_frame,
            text="清空",
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#ef4444',
            activebackground='#334155',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._clear_all
        )
        clear_btn.pack(side=tk.LEFT)

        # 保存模板按钮
        save_btn = tk.Button(
            btn_frame,
            text="保存模板",
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#f59e0b',
            activebackground='#334155',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._save_template
        )
        save_btn.pack(side=tk.LEFT, padx=10)

        # 应用按钮
        apply_btn = tk.Button(
            btn_frame,
            text="应用筛选",
            font=('PingFang SC', 12, 'bold'),
            bg='#3b82f6',
            fg='white',
            activebackground='#2563eb',
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor='hand2',
            command=self._apply_filters
        )
        apply_btn.pack(side=tk.RIGHT)

    def _create_sort_section(self, parent):
        """创建排序设置区域"""
        sort_frame = tk.LabelFrame(
            parent,
            text=" 排序设置 ",
            font=('PingFang SC', 12, 'bold'),
            fg='#f8fafc',
            bg='#0f172a',
            bd=1,
            highlightbackground='#334155',
            highlightthickness=1
        )
        sort_frame.pack(fill=tk.X, pady=(0, 20))

        # 排序字段
        field_frame = tk.Frame(sort_frame, bg='#0f172a')
        field_frame.pack(fill=tk.X, padx=15, pady=10)

        field_label = tk.Label(
            field_frame,
            text="排序字段:",
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a'
        )
        field_label.pack(side=tk.LEFT)

        self.sort_field_var = tk.StringVar()
        field_combo = ttk.Combobox(
            field_frame,
            textvariable=self.sort_field_var,
            values=[f.label for f in self.available_fields],
            state='readonly',
            font=('PingFang SC', 11)
        )
        field_combo.pack(side=tk.LEFT, padx=10)

        # 排序方向
        order_frame = tk.Frame(sort_frame, bg='#0f172a')
        order_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.sort_order_var = tk.StringVar(value='desc')

        asc_radio = tk.Radiobutton(
            order_frame,
            text="升序",
            variable=self.sort_order_var,
            value='asc',
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a',
            selectcolor='#1e293b',
            activebackground='#0f172a',
            activeforeground='#f8fafc'
        )
        asc_radio.pack(side=tk.LEFT, padx=(0, 20))

        desc_radio = tk.Radiobutton(
            order_frame,
            text="降序",
            variable=self.sort_order_var,
            value='desc',
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a',
            selectcolor='#1e293b',
            activebackground='#0f172a',
            activeforeground='#f8fafc'
        )
        desc_radio.pack(side=tk.LEFT)

    def _add_condition(self, condition_data: Dict = None):
        """添加筛选条件"""
        condition = FilterCondition()

        if condition_data:
            condition.field = condition_data.get('field')
            condition.operator = condition_data.get('operator')
            condition.value = condition_data.get('value')

        self.conditions.append(condition)

        # 创建条件UI
        frame = tk.Frame(self.conditions_container, bg='#1e293b', padx=15, pady=15)
        frame.pack(fill=tk.X, pady=(0, 10))
        frame.configure(highlightbackground='#334155', highlightthickness=1)

        # 字段选择
        field_frame = tk.Frame(frame, bg='#1e293b')
        field_frame.pack(fill=tk.X, pady=(0, 10))

        field_var = tk.StringVar(value=condition.field or '')
        field_combo = ttk.Combobox(
            field_frame,
            textvariable=field_var,
            values=[f.label for f in self.available_fields],
            state='readonly',
            font=('PingFang SC', 11),
            width=20
        )
        field_combo.pack(side=tk.LEFT)

        # 删除按钮
        delete_btn = tk.Button(
            field_frame,
            text="🗑️",
            font=('Apple Color Emoji', 12),
            bg='#1e293b',
            fg='#ef4444',
            activebackground='#334155',
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda: self._remove_condition(frame, condition)
        )
        delete_btn.pack(side=tk.RIGHT)

        # 操作符
        op_frame = tk.Frame(frame, bg='#1e293b')
        op_frame.pack(fill=tk.X)

        op_var = tk.StringVar(value=condition.operator or 'equals')
        op_combo = ttk.Combobox(
            op_frame,
            textvariable=op_var,
            values=list(self.OPERATORS.values()),
            state='readonly',
            font=('PingFang SC', 11),
            width=15
        )
        op_combo.pack(side=tk.LEFT, padx=(0, 10))

        # 值输入
        value_frame = tk.Frame(frame, bg='#1e293b')
        value_frame.pack(fill=tk.X, pady=(10, 0))

        value_var = tk.StringVar(value=str(condition.value) if condition.value else '')
        value_entry = tk.Entry(
            value_frame,
            textvariable=value_var,
            font=('PingFang SC', 11),
            bg='#0f172a',
            fg='#f8fafc',
            insertbackground='#f8fafc',
            relief=tk.FLAT,
            highlightbackground='#334155',
            highlightthickness=1
        )
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 绑定变量更新
        def update_condition(*args):
            condition.field = field_var.get()
            condition.operator = self._get_operator_key(op_var.get())
            condition.value = value_var.get()

        field_var.trace('w', update_condition)
        op_var.trace('w', update_condition)
        value_var.trace('w', update_condition)

        # 保存引用
        frame.condition = condition
        self.condition_frames.append(frame)

    def _remove_condition(self, frame, condition):
        """移除筛选条件"""
        frame.destroy()
        self.conditions.remove(condition)
        self.condition_frames.remove(frame)

    def _get_operator_key(self, value: str) -> str:
        """获取操作符键"""
        for k, v in self.OPERATORS.items():
            if v == value:
                return k
        return 'equals'

    def _load_initial_filters(self):
        """加载初始筛选条件"""
        if self.initial_filters:
            conditions = self.initial_filters.get('conditions', [])
            for cond_data in conditions:
                self._add_condition(cond_data)

            # 加载排序设置
            sort = self.initial_filters.get('sort', {})
            if sort.get('field'):
                self.sort_field_var.set(sort['field'])
            self.sort_order_var.set(sort.get('order', 'desc'))

    def _clear_all(self):
        """清空所有条件"""
        for frame in self.condition_frames:
            frame.destroy()
        self.condition_frames.clear()
        self.conditions.clear()
        self.sort_field_var.set('')
        self.sort_order_var.set('desc')

    def _save_template(self):
        """保存筛选模板"""
        name = simpledialog.askstring("保存模板", "请输入模板名称:")
        if name:
            # 保存到配置文件
            template = {
                'name': name,
                'conditions': [c.to_dict() for c in self.conditions],
                'sort': {
                    'field': self.sort_field_var.get(),
                    'order': self.sort_order_var.get()
                }
            }
            # TODO: 保存到配置文件
            messagebox.showinfo("成功", f"模板 '{name}' 已保存!")

    def _apply_filters(self):
        """应用筛选"""
        # 构建筛选参数
        filter_params = {
            'conditions': [c.to_dict() for c in self.conditions if c.field and c.operator],
            'sort': {
                'field': self.sort_field_var.get(),
                'order': self.sort_order_var.get()
            }
        }

        if self.on_apply:
            self.on_apply(filter_params)

        self.window.destroy()

    def show(self):
        """显示窗口"""
        if not self.parent:
            self.window.mainloop()


def show_advanced_filter(parent=None, available_fields: List[FilterField] = None,
                         initial_filters: Dict = None, on_apply: Callable = None):
    """显示高级筛选窗口"""
    window = AdvancedFilterWindow(parent, available_fields, initial_filters, on_apply)
    window.show()
    return window


if __name__ == '__main__':
    # 测试
    fields = [
        FilterField('name', '名称'),
        FilterField('price', '价格', 'number'),
        FilterField('category', '分类'),
        FilterField('created_at', '创建时间', 'date')
    ]

    def on_apply(filters):
        print("应用筛选:", json.dumps(filters, ensure_ascii=False, indent=2))

    show_advanced_filter(available_fields=fields, on_apply=on_apply)
