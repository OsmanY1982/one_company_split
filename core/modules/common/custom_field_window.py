"""
自定义字段管理窗口
支持创建、编辑、删除自定义字段
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Callable
from enum import Enum


class FieldType(Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"


class CustomField:
    """自定义字段定义"""
    def __init__(self, id: str, name: str, key: str, field_type: FieldType,
                 options: List[str] = None, is_required: bool = False):
        self.id = id
        self.name = name
        self.key = key
        self.type = field_type
        self.options = options or []
        self.is_required = is_required


class CustomFieldWindow:
    """自定义字段管理窗口"""

    TYPE_LABELS = {
        FieldType.TEXT: '文本',
        FieldType.NUMBER: '数字',
        FieldType.DATE: '日期',
        FieldType.BOOLEAN: '布尔',
        FieldType.SELECT: '下拉'
    }

    TYPE_COLORS = {
        FieldType.TEXT: '#3b82f6',
        FieldType.NUMBER: '#10b981',
        FieldType.DATE: '#f59e0b',
        FieldType.BOOLEAN: '#8b5cf6',
        FieldType.SELECT: '#06b6d4'
    }

    def __init__(self, parent=None, on_fields_change: Callable = None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("自定义字段管理")
        self.window.geometry("900x700")
        self.window.configure(bg='#0f172a')

        self.on_fields_change = on_fields_change
        self.fields: List[CustomField] = []
        self.field_frames = []

        self._setup_ui()
        self._load_fields()

    def _setup_ui(self):
        """设置UI"""
        # 主容器
        main_frame = tk.Frame(self.window, bg='#0f172a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题栏
        header = tk.Frame(main_frame, bg='#0f172a')
        header.pack(fill=tk.X, pady=(0, 20))

        title = tk.Label(
            header,
            text="📝 自定义字段管理",
            font=('PingFang SC', 20, 'bold'),
            fg='#f8fafc',
            bg='#0f172a'
        )
        title.pack(side=tk.LEFT)

        # 添加按钮
        add_btn = tk.Button(
            header,
            text="➕ 添加字段",
            font=('PingFang SC', 12),
            bg='#3b82f6',
            fg='white',
            activebackground='#2563eb',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._show_add_dialog
        )
        add_btn.pack(side=tk.RIGHT)

        # 字段列表容器
        self.list_container = tk.Frame(main_frame, bg='#0f172a')
        self.list_container.pack(fill=tk.BOTH, expand=True)

        # 空状态提示
        self.empty_label = tk.Label(
            self.list_container,
            text="暂无自定义字段\n点击右上角添加字段",
            font=('PingFang SC', 14),
            fg='#64748b',
            bg='#0f172a',
            justify=tk.CENTER
        )

    def _load_fields(self):
        """加载字段列表"""
        # 模拟数据
        self.fields = [
            CustomField(
                id='1',
                name='客户等级',
                key='customer_level',
                field_type=FieldType.SELECT,
                options=['普通', 'VIP', 'SVIP'],
                is_required=True
            ),
            CustomField(
                id='2',
                name='生日',
                key='birthday',
                field_type=FieldType.DATE,
                is_required=False
            )
        ]
        self._refresh_list()

    def _refresh_list(self):
        """刷新字段列表"""
        # 清除旧列表
        for frame in self.field_frames:
            frame.destroy()
        self.field_frames.clear()

        if not self.fields:
            self.empty_label.pack(expand=True)
            return

        self.empty_label.pack_forget()

        for field in self.fields:
            self._create_field_card(field)

    def _create_field_card(self, field: CustomField):
        """创建字段卡片"""
        card = tk.Frame(
            self.list_container,
            bg='#1e293b',
            highlightbackground='#334155',
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card.pack(fill=tk.X, pady=(0, 10))

        # 头部信息
        header = tk.Frame(card, bg='#1e293b')
        header.pack(fill=tk.X)

        # 类型标签
        type_color = self.TYPE_COLORS.get(field.type, '#64748b')
        type_label = tk.Label(
            header,
            text=self.TYPE_LABELS.get(field.type, '未知'),
            font=('PingFang SC', 10),
            fg=type_color,
            bg='#1e293b'
        )
        type_label.pack(side=tk.LEFT)

        # 必填标签
        if field.is_required:
            required_label = tk.Label(
                header,
                text='必填',
                font=('PingFang SC', 10),
                fg='#ef4444',
                bg='#1e293b'
            )
            required_label.pack(side=tk.LEFT, padx=(10, 0))

        # 操作按钮
        btn_frame = tk.Frame(header, bg='#1e293b')
        btn_frame.pack(side=tk.RIGHT)

        edit_btn = tk.Button(
            btn_frame,
            text="✏️",
            font=('Apple Color Emoji', 12),
            bg='#1e293b',
            fg='#94a3b8',
            activebackground='#334155',
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda: self._show_edit_dialog(field)
        )
        edit_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(
            btn_frame,
            text="🗑️",
            font=('Apple Color Emoji', 12),
            bg='#1e293b',
            fg='#ef4444',
            activebackground='#334155',
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda: self._delete_field(field)
        )
        delete_btn.pack(side=tk.LEFT)

        # 字段名称
        name_label = tk.Label(
            card,
            text=field.name,
            font=('PingFang SC', 16, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        name_label.pack(anchor='w', pady=(15, 5))

        # 字段标识
        key_label = tk.Label(
            card,
            text=f"字段名: {field.key}",
            font=('PingFang SC', 11),
            fg='#64748b',
            bg='#1e293b'
        )
        key_label.pack(anchor='w')

        # 选项列表
        if field.options:
            options_frame = tk.Frame(card, bg='#1e293b')
            options_frame.pack(anchor='w', pady=(10, 0))

            for option in field.options:
                option_label = tk.Label(
                    options_frame,
                    text=option,
                    font=('PingFang SC', 10),
                    fg='#f8fafc',
                    bg='#334155',
                    padx=10,
                    pady=3
                )
                option_label.pack(side=tk.LEFT, padx=(0, 8))

        self.field_frames.append(card)

    def _show_add_dialog(self):
        """显示添加字段对话框"""
        self._show_field_dialog()

    def _show_edit_dialog(self, field: CustomField):
        """显示编辑字段对话框"""
        self._show_field_dialog(field)

    def _show_field_dialog(self, field: CustomField = None):
        """显示字段编辑对话框"""
        is_edit = field is not None
        dialog = tk.Toplevel(self.window)
        dialog.title("编辑字段" if is_edit else "添加字段")
        dialog.geometry("500x600")
        dialog.configure(bg='#0f172a')
        dialog.transient(self.window)
        dialog.grab_set()

        # 表单
        form_frame = tk.Frame(dialog, bg='#0f172a', padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 显示名称
        name_frame = tk.Frame(form_frame, bg='#0f172a')
        name_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            name_frame,
            text="显示名称:",
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a'
        ).pack(anchor='w')

        name_entry = tk.Entry(
            name_frame,
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#f8fafc',
            insertbackground='#f8fafc',
            relief=tk.FLAT,
            highlightbackground='#334155',
            highlightthickness=1
        )
        name_entry.pack(fill=tk.X, pady=(5, 0))
        if is_edit:
            name_entry.insert(0, field.name)

        # 字段标识
        key_frame = tk.Frame(form_frame, bg='#0f172a')
        key_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            key_frame,
            text="字段标识:",
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a'
        ).pack(anchor='w')

        key_entry = tk.Entry(
            key_frame,
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#f8fafc',
            insertbackground='#f8fafc',
            relief=tk.FLAT,
            highlightbackground='#334155',
            highlightthickness=1
        )
        key_entry.pack(fill=tk.X, pady=(5, 0))
        if is_edit:
            key_entry.insert(0, field.key)

        # 字段类型
        type_frame = tk.Frame(form_frame, bg='#0f172a')
        type_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            type_frame,
            text="字段类型:",
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a'
        ).pack(anchor='w')

        type_var = tk.StringVar(value=field.type.value if is_edit else FieldType.TEXT.value)
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=type_var,
            values=[t.value for t in FieldType],
            state='readonly',
            font=('PingFang SC', 12)
        )
        type_combo.pack(fill=tk.X, pady=(5, 0))

        # 必填选项
        required_var = tk.BooleanVar(value=field.is_required if is_edit else False)
        required_cb = tk.Checkbutton(
            form_frame,
            text="必填字段",
            variable=required_var,
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0f172a',
            selectcolor='#1e293b',
            activebackground='#0f172a',
            activeforeground='#f8fafc'
        )
        required_cb.pack(anchor='w', pady=(0, 15))

        # 选项列表（仅下拉类型）
        options_frame = tk.LabelFrame(
            form_frame,
            text=" 选项列表 ",
            font=('PingFang SC', 11, 'bold'),
            fg='#f8fafc',
            bg='#0f172a',
            bd=1,
            highlightbackground='#334155',
            highlightthickness=1
        )
        options_frame.pack(fill=tk.X, pady=(0, 15))

        options_list = tk.Listbox(
            options_frame,
            bg='#1e293b',
            fg='#f8fafc',
            font=('PingFang SC', 11),
            relief=tk.FLAT,
            highlightbackground='#334155',
            highlightthickness=1
        )
        options_list.pack(fill=tk.X, padx=10, pady=10)

        if is_edit and field.options:
            for opt in field.options:
                options_list.insert(tk.END, opt)

        # 选项操作
        opt_btn_frame = tk.Frame(options_frame, bg='#0f172a')
        opt_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def add_option():
            option = simpledialog.askstring("添加选项", "请输入选项值:", parent=dialog)
            if option:
                options_list.insert(tk.END, option)

        def remove_option():
            selection = options_list.curselection()
            if selection:
                options_list.delete(selection[0])

        tk.Button(
            opt_btn_frame,
            text="添加",
            font=('PingFang SC', 10),
            bg='#3b82f6',
            fg='white',
            relief=tk.FLAT,
            command=add_option
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            opt_btn_frame,
            text="删除",
            font=('PingFang SC', 10),
            bg='#ef4444',
            fg='white',
            relief=tk.FLAT,
            command=remove_option
        ).pack(side=tk.LEFT)

        # 按钮
        btn_frame = tk.Frame(form_frame, bg='#0f172a')
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            btn_frame,
            text="取消",
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#94a3b8',
            activebackground='#334155',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=dialog.destroy
        ).pack(side=tk.LEFT)

        def save():
            name = name_entry.get().strip()
            key = key_entry.get().strip()
            field_type = FieldType(type_var.get())
            is_required = required_var.get()
            options = [options_list.get(i) for i in range(options_list.size())]

            if not name or not key:
                messagebox.showwarning("提示", "请填写完整信息", parent=dialog)
                return

            if is_edit:
                field.name = name
                field.key = key
                field.type = field_type
                field.is_required = is_required
                field.options = options
            else:
                new_field = CustomField(
                    id=str(len(self.fields) + 1),
                    name=name,
                    key=key,
                    field_type=field_type,
                    options=options,
                    is_required=is_required
                )
                self.fields.append(new_field)

            self._refresh_list()
            if self.on_fields_change:
                self.on_fields_change(self.fields)
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="保存",
            font=('PingFang SC', 12, 'bold'),
            bg='#3b82f6',
            fg='white',
            activebackground='#2563eb',
            relief=tk.FLAT,
            padx=30,
            pady=8,
            command=save
        ).pack(side=tk.RIGHT)

    def _delete_field(self, field: CustomField):
        """删除字段"""
        if messagebox.askyesno("确认删除", f"确定要删除字段 '{field.name}' 吗？"):
            self.fields.remove(field)
            self._refresh_list()
            if self.on_fields_change:
                self.on_fields_change(self.fields)

    def show(self):
        """显示窗口"""
        if not self.parent:
            self.window.mainloop()


def show_custom_field_manager(parent=None, on_fields_change: Callable = None):
    """显示自定义字段管理窗口"""
    window = CustomFieldWindow(parent, on_fields_change)
    window.show()
    return window


if __name__ == '__main__':
    show_custom_field_manager()
