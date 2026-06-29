"""
国际化服务
多语言支持
"""

import json
import os
from typing import Dict, Optional


class I18nService:
    """国际化服务"""

    # 默认语言包
    DEFAULT_TRANSLATIONS = {
        "zh_CN": {
            "app_name": "一人公司",
            "ok": "确定",
            "cancel": "取消",
            "save": "保存",
            "delete": "删除",
            "edit": "编辑",
            "search": "搜索",
            "refresh": "刷新",
            "export": "导出",
            "import": "导入",
            "settings": "设置",
            "help": "帮助",
            "about": "关于",
            "exit": "退出",
            "yes": "是",
            "no": "否",
            "success": "操作成功",
            "failed": "操作失败",
            "error": "错误",
            "warning": "警告",
            "info": "提示",
            "confirm": "确认",
            "loading": "加载中...",
            "no_data": "暂无数据",
            "total": "合计",
            "amount": "金额",
            "date": "日期",
            "time": "时间",
            "status": "状态",
            "action": "操作",
            "name": "名称",
            "description": "描述",
            "remark": "备注",
            "customer": "客户",
            "product": "产品",
            "product_name": "产品名称",
            "order": "订单",
            "order_no": "订单编号",
            "price": "单价",
            "quantity": "数量",
            "stock": "库存",
            "category": "分类",
        },
        "en_US": {
            "app_name": "One Company",
            "ok": "OK",
            "cancel": "Cancel",
            "save": "Save",
            "delete": "Delete",
            "edit": "Edit",
            "search": "Search",
            "refresh": "Refresh",
            "export": "Export",
            "import": "Import",
            "settings": "Settings",
            "help": "Help",
            "about": "About",
            "exit": "Exit",
            "yes": "Yes",
            "no": "No",
            "success": "Success",
            "failed": "Failed",
            "error": "Error",
            "warning": "Warning",
            "info": "Info",
            "confirm": "Confirm",
            "loading": "Loading...",
            "no_data": "No Data",
            "total": "Total",
            "amount": "Amount",
            "date": "Date",
            "time": "Time",
            "status": "Status",
            "action": "Action",
            "name": "Name",
            "description": "Description",
            "remark": "Remark",
            "customer": "Customer",
            "product": "Product",
            "product_name": "Product Name",
            "order": "Order",
            "order_no": "Order No",
            "price": "Price",
            "quantity": "Quantity",
            "stock": "Stock",
            "category": "Category",
        },
    }

    def __init__(self, config_dir: str = "data", default_locale: str = "zh_CN"):
        self.config_dir = config_dir
        self.locale_file = os.path.join(config_dir, "locale.json")
        self._locale = default_locale
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """加载翻译"""
        # 加载默认翻译
        self._translations = {
            lang: dict(trans) for lang, trans in self.DEFAULT_TRANSLATIONS.items()
        }

        # 加载自定义翻译
        if os.path.exists(self.locale_file):
            try:
                with open(self.locale_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                    self._locale = custom.get("locale", self._locale)

                    for lang, trans in custom.get("translations", {}).items():
                        if lang in self._translations:
                            self._translations[lang].update(trans)
                        else:
                            self._translations[lang] = trans
            except Exception:
                pass

    def _save_config(self):
        """保存配置"""
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.locale_file, "w", encoding="utf-8") as f:
            json.dump({
                "locale": self._locale,
                "translations": self._translations,
            }, f, ensure_ascii=False, indent=2)

    def t(self, key: str, *args, **kwargs) -> str:
        """翻译"""
        locale_trans = self._translations.get(self._locale, {})
        text = locale_trans.get(key)

        if text is None:
            # 回退到中文
            text = self._translations.get("zh_CN", {}).get(key, key)

        try:
            return text.format(*args, **kwargs)
        except Exception:
            return text

    def set_locale(self, locale: str):
        """设置语言"""
        self._locale = locale
        self._save_config()

    def get_locale(self) -> str:
        """获取当前语言"""
        return self._locale

    def get_available_locales(self) -> Dict[str, str]:
        """获取可用语言"""
        return {
            "zh_CN": "简体中文",
            "en_US": "English",
        }

    def add_translation(self, locale: str, key: str, value: str):
        """添加翻译"""
        if locale not in self._translations:
            self._translations[locale] = {}
        self._translations[locale][key] = value
        self._save_config()

    def import_translations(self, data: Dict):
        """批量导入翻译"""
        for locale, trans in data.items():
            if locale in self._translations:
                self._translations[locale].update(trans)
            else:
                self._translations[locale] = dict(trans)
        self._save_config()


# 全局实例
i18n = I18nService()
_ = i18n.t

