"""
模板服务
文档模板管理和生成
"""

import os
import json
import jinja2
from typing import Dict, List, Optional
from datetime import datetime


class TemplateService:
    """模板服务"""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.meta_file = os.path.join(templates_dir, ".meta.json")
        self._ensure_templates_dir()

        if self._system == "Windows":
            from jinja2 import Environment, FileSystemLoader
        else:
            from jinja2 import Environment, FileSystemLoader

        self._env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=False,
        )

    def _ensure_templates_dir(self):
        """确保模板目录存在"""
        os.makedirs(self.templates_dir, exist_ok=True)
        if not os.path.exists(self.meta_file):
            self._save_meta({})

    def _load_meta(self) -> Dict:
        """加载元数据"""
        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_meta(self, meta: Dict):
        """保存元数据"""
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def add_template(self,
                     name: str,
                     content: str,
                     category: str = "通用",
                     description: str = "",
                     variables: Optional[List[str]] = None) -> Dict:
        """添加模板"""
        file_path = os.path.join(self.templates_dir, f"{name}.j2")

        if os.path.exists(file_path):
            return {"success": False, "message": "模板已存在"}

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 更新元数据
        meta = self._load_meta()
        meta[name] = {
            "name": name,
            "category": category,
            "description": description,
            "variables": variables or self._extract_variables(content),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._save_meta(meta)

        return {"success": True, "name": name, "file": file_path}

    def remove_template(self, name: str) -> Dict:
        """删除模板"""
        file_path = os.path.join(self.templates_dir, f"{name}.j2")
        if os.path.exists(file_path):
            os.remove(file_path)

        meta = self._load_meta()
        meta.pop(name, None)
        self._save_meta(meta)

        return {"success": True}

    def render(self,
               template_name: str,
               variables: Dict) -> Dict:
        """渲染模板"""
        template = self._env.get_template(f"{template_name}.j2")

        try:
            result = template.render(**variables)
            return {"success": True, "rendered": result}
        except Exception as e:
            return {"success": False, "message": f"渲染失败: {e}"}

    def render_to_file(self,
                       template_name: str,
                       variables: Dict,
                       output_path: str) -> Dict:
        """渲染模板到文件"""
        try:
            template = self._env.get_template(f"{template_name}.j2")
            result = template.render(**variables)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)

            return {"success": True, "output": output_path}

        except Exception as e:
            return {"success": False, "message": f"渲染失败: {e}"}

    def get_template_info(self, name: str) -> Optional[Dict]:
        """获取模板信息"""
        meta = self._load_meta()
        return meta.get(name)

    def list_templates(self, category: Optional[str] = None) -> List[Dict]:
        """列出模板"""
        meta = self._load_meta()
        templates = list(meta.values())

        if category:
            templates = [t for t in templates if t.get("category") == category]

        return templates

    def get_categories(self) -> List[str]:
        """获取分类列表"""
        meta = self._load_meta()
        categories = set(t.get("category", "通用") for t in meta.values())
        return sorted(categories)

    def _extract_variables(self, content: str) -> List[str]:
        """提取模板变量"""
        import re
        variables = set()

        # Jinja2变量: {{ var_name }}
        matches = re.findall(r'\{\{\s*(\w+(?:\.\w+)*)\s*\}\}', content)
        variables.update(matches)

        # Jinja2 for循环: {% for item in items %}
        matches = re.findall(r'for\s+(\w+)\s+in', content)
        variables.update(matches)

        return sorted(variables)

    def preview_template(self, name: str) -> Dict:
        """预览模板"""
        meta = self._load_meta()
        info = meta.get(name)

        if not info:
            return {"success": False, "message": "模板不存在"}

        file_path = os.path.join(self.templates_dir, f"{name}.j2")
        if not os.path.exists(file_path):
            return {"success": False, "message": "模板文件不存在"}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "success": True,
            "name": name,
            "info": info,
            "content": content[:3000],  # 预览前3000字符
        }

