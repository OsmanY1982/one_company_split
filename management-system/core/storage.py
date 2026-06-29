# -*- coding: utf-8 -*-

import json
import os
from typing import Dict, Any, Optional


class Storage:
    

    _instance: Optional['Storage'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        # 数据目录
        self.data_dir = os.path.join(BASE_DIR, "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def save(self, key: str, data: Dict[str, Any]):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        file_path = os.path.join(self.data_dir, f"{key}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存: {key}")
        except Exception as e:
            print(f"保存数据失败: {key} - {e}")

    def load(self, key: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        
        file_path = os.path.join(self.data_dir, f"{key}.json")
        if not os.path.exists(file_path):
            return default or {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"数据已加载: {key}")
            return data
        except Exception as e:
            print(f"加载数据失败: {key} - {e}")
            return default or {}

    def remove(self, key: str):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        file_path = os.path.join(self.data_dir, f"{key}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"数据已删除: {key}")


# 全局实例
storage = Storage()
