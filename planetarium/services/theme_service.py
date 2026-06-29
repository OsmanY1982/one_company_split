"""
主题服务
应用主题（亮色/暗色/自定义）管理
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ThemeColors:
    """主题配色"""
    name: str
    primary: str = "#4A90D9"
    secondary: str = "#66BB6A"
    background: str = "#FFFFFF"
    foreground: str = "#333333"
    border: str = "#E0E0E0"
    success: str = "#4CAF50"
    warning: str = "#FF9800"
    error: str = "#F44336"
    info: str = "#2196F3"
    header_bg: str = "#FAFAFA"
    sidebar_bg: str = "#F5F5F5"
    hover_bg: str = "#F0F0F0"
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_disabled: str = "#BDBDBD"
    input_bg: str = "#FFFFFF"
    input_border: str = "#D0D0D0"
    button_primary_text: str = "#FFFFFF"


class ThemeService:
    """主题服务"""

    # 预设主题
    PRESET_THEMES = {
        "light": ThemeColors(
            name="亮色",
            primary="#4A90D9",
            secondary="#66BB6A",
            background="#FFFFFF",
            foreground="#333333",
            border="#E0E0E0",
            success="#4CAF50",
            warning="#FF9800",
            error="#F44336",
            info="#2196F3",
            header_bg="#FAFAFA",
            sidebar_bg="#F5F5F5",
            hover_bg="#F0F0F0",
            text_primary="#212121",
            text_secondary="#757575",
            text_disabled="#BDBDBD",
            input_bg="#FFFFFF",
            input_border="#D0D0D0",
            button_primary_text="#FFFFFF",
        ),
        "dark": ThemeColors(
            name="暗色",
            primary="#4A90D9",
            secondary="#66BB6A",
            background="#1E1E1E",
            foreground="#E0E0E0",
            border="#424242",
            success="#4CAF50",
            warning="#FFB74D",
            error="#EF5350",
            info="#42A5F5",
            header_bg="#2D2D2D",
            sidebar_bg="#252525",
            hover_bg="#383838",
            text_primary="#FFFFFF",
            text_secondary="#BDBDBD",
            text_disabled="#616161",
            input_bg="#2D2D2D",
            input_border="#555555",
            button_primary_text="#FFFFFF",
        ),
        "blue": ThemeColors(
            name="商务蓝",
            primary="#1565C0",
            secondary="#1E88E5",
            background="#F5F7FA",
            foreground="#333333",
            border="#D0D7E3",
            success="#2E7D32",
            warning="#F57C00",
            error="#C62828",
            info="#1976D2",
            header_bg="#1565C0",
            sidebar_bg="#FFFFFF",
            hover_bg="#E3F2FD",
            text_primary="#212121",
            text_secondary="#5F6368",
            text_disabled="#BDBDBD",
            input_bg="#FFFFFF",
            input_border="#D0D7E3",
            button_primary_text="#FFFFFF",
        ),
    }

    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.theme_file = os.path.join(config_dir, "theme.json")
        self._current_theme_name = "light"
        self._custom_themes: Dict[str, ThemeColors] = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.theme_file):
            try:
                with open(self.theme_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                    self._current_theme_name = config.get("theme", "light")

                    for name, colors in config.get("custom_themes", {}).items():
                        self._custom_themes[name] = ThemeColors(name=name, **colors)
            except Exception:
                pass

    def _save_config(self):
        """保存配置"""
        os.makedirs(self.config_dir, exist_ok=True)

        custom_data = {}
        for name, theme in self._custom_themes.items():
            custom_data[name] = {
                k: v for k, v in theme.__dict__.items() if k != "name"
            }

        with open(self.theme_file, "w", encoding="utf-8") as f:
            json.dump({
                "theme": self._current_theme_name,
                "custom_themes": custom_data,
            }, f, ensure_ascii=False, indent=2)

    def set_theme(self, theme_name: str) -> Dict:
        """设置当前主题"""
        available = self.get_available_themes()

        if theme_name not in available:
            return {"success": False, "message": f"主题 '{theme_name}' 不存在"}

        self._current_theme_name = theme_name
        self._save_config()

        return {"success": True, "theme": theme_name}

    def get_current_theme(self) -> ThemeColors:
        """获取当前主题"""
        if self._current_theme_name in self.PRESET_THEMES:
            return self.PRESET_THEMES[self._current_theme_name]
        elif self._current_theme_name in self._custom_themes:
            return self._custom_themes[self._current_theme_name]
        else:
            return self.PRESET_THEMES["light"]

    def get_color(self, color_key: str) -> str:
        """获取指定颜色"""
        theme = self.get_current_theme()
        return getattr(theme, color_key, "#000000")

    def get_available_themes(self) -> Dict[str, str]:
        """获取可用主题列表"""
        themes = {
            name: theme.name
            for name, theme in self.PRESET_THEMES.items()
        }

        for name, theme in self._custom_themes.items():
            themes[name] = theme.name

        return themes

    def add_custom_theme(self, name: str, colors: Dict) -> Dict:
        """添加自定义主题"""
        if name in self.PRESET_THEMES:
            return {"success": False, "message": "不能覆盖预设主题"}

        theme_data = {
            "name": name,
            "primary": colors.get("primary", "#4A90D9"),
            "secondary": colors.get("secondary", "#66BB6A"),
            "background": colors.get("background", "#FFFFFF"),
            "foreground": colors.get("foreground", "#333333"),
            "border": colors.get("border", "#E0E0E0"),
            "success": colors.get("success", "#4CAF50"),
            "warning": colors.get("warning", "#FF9800"),
            "error": colors.get("error", "#F44336"),
            "info": colors.get("info", "#2196F3"),
            "header_bg": colors.get("header_bg", "#FAFAFA"),
            "sidebar_bg": colors.get("sidebar_bg", "#F5F5F5"),
            "hover_bg": colors.get("hover_bg", "#F0F0F0"),
            "text_primary": colors.get("text_primary", "#212121"),
            "text_secondary": colors.get("text_secondary", "#757575"),
            "text_disabled": colors.get("text_disabled", "#BDBDBD"),
            "input_bg": colors.get("input_bg", "#FFFFFF"),
            "input_border": colors.get("input_border", "#D0D0D0"),
            "button_primary_text": colors.get("button_primary_text", "#FFFFFF"),
        }

        self._custom_themes[name] = ThemeColors(**theme_data)
        self._save_config()

        return {"success": True, "name": name}

    def remove_custom_theme(self, name: str) -> Dict:
        """删除自定义主题"""
        if name in self.PRESET_THEMES:
            return {"success": False, "message": "不能删除预设主题"}

        if name == self._current_theme_name:
            return {"success": False, "message": "不能删除当前使用的主题"}

        self._custom_themes.pop(name, None)
        self._save_config()

        return {"success": True}

    def get_theme_preview(self, theme_name: str) -> Optional[Dict]:
        """获取主题预览"""
        if theme_name in self.PRESET_THEMES:
            theme = self.PRESET_THEMES[theme_name]
        elif theme_name in self._custom_themes:
            theme = self._custom_themes[theme_name]
        else:
            return None

        return {
            "name": theme.name,
            "colors": {
                "primary": theme.primary,
                "secondary": theme.secondary,
                "background": theme.background,
                "foreground": theme.foreground,
                "success": theme.success,
                "warning": theme.warning,
                "error": theme.error,
            },
        }

    def is_dark_theme(self) -> bool:
        """是否为暗色主题"""
        theme = self.get_current_theme()
        # 简单判断：背景色较暗
        bg = theme.background.lstrip("#")
        if len(bg) == 6:
            r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            return luminance < 128
        return False

