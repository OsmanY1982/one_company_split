# `iqra/core/_tool_registry.py`

> 路径：`iqra/core/_tool_registry.py` | 行数：53


---


```python
"""工具注册表 - 从 core_engine.py 拆分"""

from typing import Optional, List, Dict, Any, Callable


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, name: str, description: str, parameters: dict, handler: Callable):
        """注册一个工具"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def get(self, name: str) -> Optional[dict]:
        """获取工具定义"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[dict]:
        """获取所有工具定义（OpenAI 格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"]
                }
            }
            for t in self._tools.values()
        ]
    
    def execute(self, name: str, arguments: dict) -> Any:
        """执行工具"""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"工具不存在：{name}"}
        try:
            result = tool["handler"](**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}

```
