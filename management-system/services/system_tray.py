"""
系统托盘
Windows/macOS 系统托盘图标
"""

import platform
import json
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime


class SystemTray:
    """系统托盘"""

    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "tray_config.json")
        self._system = platform.system()
        self._menu_items: List[Dict] = []
        self._callbacks: Dict[str, Callable] = []
        self._icon_path: Optional[str] = None
        self._tooltip: str = "一人公司"
        self._visible: bool = False
        self._load_config()

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self._menu_items = config.get("menu_items", [])
                    self._icon_path = config.get("icon_path")
                    self._tooltip = config.get("tooltip", "一人公司")
            except Exception:
                pass

        if not self._menu_items:
            self._init_default_menu()

    def _init_default_menu(self):
        """初始化默认菜单"""
        self._menu_items = [
            {"id": "dashboard", "label": "工作面板", "separator_after": False},
            {"id": "new_order", "label": "新建订单", "separator_after": False},
            {"id": "separator_1", "type": "separator"},
            {"id": "sync", "label": "立即同步", "separator_after": False},
            {"id": "backup", "label": "数据备份", "separator_after": False},
            {"id": "separator_2", "type": "separator"},
            {"id": "settings", "label": "设置", "separator_after": False},
            {"id": "separator_3", "type": "separator"},
            {"id": "about", "label": "关于", "separator_after": False},
            {"id": "exit", "label": "退出", "separator_after": False},
        ]

    def _save_config(self):
        """保存配置"""
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump({
                "menu_items": self._menu_items,
                "icon_path": self._icon_path,
                "tooltip": self._tooltip,
            }, f, ensure_ascii=False, indent=2)

    def show(self):
        """显示托盘图标"""
        self._visible = True

        if self._system == "Windows":
            self._show_windows_tray()
        elif self._system == "Darwin":
            self._show_macos_tray()

    def _show_windows_tray(self):
        """Windows托盘"""
        try:
            import pystray
            from PIL import Image

            # 图标
            if self._icon_path and os.path.exists(self._icon_path):
                image = Image.open(self._icon_path)
            else:
                image = Image.new("RGB", (64, 64), color=(66, 133, 244))

            # 菜单
            menu = self._build_menu()

            self._tray_icon = pystray.Icon("one_company", image, self._tooltip, menu)
            self._tray_icon.run_detached()

        except ImportError:
            pass

    def _show_macos_tray(self):
        """macOS托盘"""
        try:
            import rumps

            class OneCompanyApp(rumps.App):
                def __init__(self, tray_instance):
                    super().__init__("一人公司", quit_button=None)
                    self.tray = tray_instance

                @rumps.clicked("工作面板")
                def dashboard(self, _):
                    self.tray.trigger_callback("dashboard")

                @rumps.clicked("新建订单")
                def new_order(self, _):
                    self.tray.trigger_callback("new_order")

                @rumps.clicked("设置")
                def settings(self, _):
                    self.tray.trigger_callback("settings")

                @rumps.clicked("退出")
                def quit_app(self, _):
                    self.tray.trigger_callback("exit")
                    rumps.quit_application()

            self._app = OneCompanyApp(self)
            self._app.run()

        except ImportError:
            pass

    def _build_menu(self):
        """构建菜单"""
        import pystray

        items = []
        for mi in self._menu_items:
            if mi.get("type") == "separator":
                items.append(pystray.Menu.SEPARATOR)
            else:
                item_id = mi["id"]
                label = mi.get("label", item_id)
                items.append(pystray.MenuItem(
                    label,
                    lambda id=item_id: self.trigger_callback(id),
                ))

        return pystray.Menu(*items)

    def hide(self):
        """隐藏托盘图标"""
        self._visible = False

        if hasattr(self, "_tray_icon"):
            self._tray_icon.stop()

    def add_menu_item(self, item_id: str, label: str, callback: Optional[Callable] = None, separator_after: bool = False):
        """添加菜单项"""
        item = {"id": item_id, "label": label, "separator_after": separator_after}
        self._menu_items.append(item)

        if callback:
            self._callbacks.append((item_id, callback))

        self._save_config()

    def add_separator(self):
        """添加分隔线"""
        self._menu_items.append({"type": "separator"})
        self._save_config()

    def remove_menu_item(self, item_id: str):
        """删除菜单项"""
        self._menu_items = [mi for mi in self._menu_items if mi.get("id") != item_id]
        self._save_config()

    def bind_callback(self, item_id: str, callback: Callable):
        """绑定回调"""
        self._callbacks.append((item_id, callback))

    def trigger_callback(self, item_id: str):
        """触发回调"""
        for id, callback in self._callbacks:
            if id == item_id:
                callback()
                return

    def set_tooltip(self, text: str):
        """设置提示文本"""
        self._tooltip = text
        self._save_config()

    def set_icon(self, icon_path: str):
        """设置图标"""
        self._icon_path = icon_path
        self._save_config()

    def show_notification(self, title: str, message: str):
        """显示托盘通知"""
        if self._system == "Windows" and hasattr(self, "_tray_icon"):
            try:
                self._tray_icon.notify(message, title)
            except Exception:
                pass
        elif self._system == "Darwin" and hasattr(self, "_app"):
            try:
                self._app.notification(title, "", message)
            except Exception:
                pass

    def get_menu_items(self) -> List[Dict]:
        """获取菜单项"""
        return list(self._menu_items)

    def is_visible(self) -> bool:
        """是否可见"""
        return self._visible

