# `core/custom_fields.py`

> 路径：`core/custom_fields.py` | 行数：284


---


```python
"""
自定义字段管理模块
支持动态字段定义、数据验证、高级筛选
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime


class FieldType(Enum):
    """字段类型枚举"""
    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    RICH_TEXT = "rich_text"
    FILE = "file"
    IMAGE = "image"
    REFERENCE = "reference"


@dataclass
class FieldOption:
    """下拉选项"""
    value: str
    label: str
    color: Optional[str] = None


@dataclass
class CustomField:
    """自定义字段定义"""
    id: str
    name: str
    field_type: FieldType
    entity_type: str
    required: bool = False
    default_value: Any = None
    options: List[FieldOption] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'name': self.name, 'field_type': self.field_type.value,
            'entity_type': self.entity_type, 'required': self.required,
            'default_value': self.default_value,
            'options': [{'value': opt.value, 'label': opt.label, 'color': opt.color} for opt in self.options],
            'validation_rules': self.validation_rules,
            'placeholder': self.placeholder, 'help_text': self.help_text,
            'sort_order': self.sort_order, 'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomField':
        field_type = FieldType(data.get('field_type', 'text'))
        options = [FieldOption(**opt) for opt in data.get('options', [])]
        return cls(
            id=data['id'], name=data['name'], field_type=field_type,
            entity_type=data['entity_type'], required=data.get('required', False),
            default_value=data.get('default_value'), options=options,
            validation_rules=data.get('validation_rules', {}),
            placeholder=data.get('placeholder'), help_text=data.get('help_text'),
            sort_order=data.get('sort_order', 0), is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        )


@dataclass
class FilterCondition:
    """筛选条件"""
    field: str
    operator: str
    value: Any
    logic: str = 'AND'
    
    def to_dict(self) -> Dict[str, Any]:
        return {'field': self.field, 'operator': self.operator, 'value': self.value, 'logic': self.logic}


@dataclass
class FilterGroup:
    """筛选条件组"""
    conditions: List[FilterCondition] = field(default_factory=list)
    logic: str = 'AND'
    
    def add_condition(self, condition: FilterCondition):
        self.conditions.append(condition)
    
    def to_dict(self) -> Dict[str, Any]:
        return {'conditions': [c.to_dict() for c in self.conditions], 'logic': self.logic}


class CustomFieldManager:
    """自定义字段管理器"""
    
    def __init__(self, storage_path: str = 'data/custom_fields.json'):
        self.storage_path = storage_path
        self.fields: Dict[str, CustomField] = {}
        self._load_fields()
    
    def _load_fields(self):
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for field_data in data.get('fields', []):
                    field = CustomField.from_dict(field_data)
                    self.fields[field.id] = field
        except FileNotFoundError:
            pass
    
    def _save_fields(self):
        data = {
            'fields': [field.to_dict() for field in self.fields.values()],
            'updated_at': datetime.now().isoformat(),
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_field(self, field: CustomField) -> CustomField:
        if not field.id:
            field.id = self._generate_id()
        field.created_at = datetime.now()
        field.updated_at = datetime.now()
        self.fields[field.id] = field
        self._save_fields()
        return field
    
    def update_field(self, field_id: str, updates: Dict[str, Any]) -> Optional[CustomField]:
        if field_id not in self.fields:
            return None
        field = self.fields[field_id]
        for key, value in updates.items():
            if hasattr(field, key):
                setattr(field, key, value)
        field.updated_at = datetime.now()
        self._save_fields()
        return field
    
    def delete_field(self, field_id: str) -> bool:
        if field_id not in self.fields:
            return False
        del self.fields[field_id]
        self._save_fields()
        return True
    
    def get_field(self, field_id: str) -> Optional[CustomField]:
        return self.fields.get(field_id)
    
    def get_fields_by_entity(self, entity_type: str, include_inactive: bool = False) -> List[CustomField]:
        fields = [f for f in self.fields.values() if f.entity_type == entity_type]
        if not include_inactive:
            fields = [f for f in fields if f.is_active]
        return sorted(fields, key=lambda f: f.sort_order)
    
    def validate_value(self, field_id: str, value: Any) -> tuple[bool, Optional[str]]:
        field = self.fields.get(field_id)
        if not field:
            return False, "字段不存在"
        if field.required and (value is None or value == ''):
            return False, f"{field.name} 为必填项"
        if value is not None:
            if field.field_type == FieldType.NUMBER:
                try: int(value)
                except (ValueError, TypeError): return False, f"{field.name} 必须为整数"
            elif field.field_type == FieldType.DECIMAL:
                try: float(value)
                except (ValueError, TypeError): return False, f"{field.name} 必须为数字"
            elif field.field_type == FieldType.EMAIL:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)):
                    return False, f"{field.name} 邮箱格式不正确"
            elif field.field_type == FieldType.PHONE:
                if not re.match(r'^1[3-9]\d{9}$', str(value)):
                    return False, f"{field.name} 手机号格式不正确"
            elif field.field_type == FieldType.URL:
                if not re.match(r'^https?://.*', str(value)):
                    return False, f"{field.name} URL格式不正确"
            rules = field.validation_rules
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                return False, f"{field.name} 最少 {rules['min_length']} 个字符"
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                return False, f"{field.name} 最多 {rules['max_length']} 个字符"
            if 'min' in rules:
                try:
                    if float(value) < float(rules['min']):
                        return False, f"{field.name} 最小值为 {rules['min']}"
                except (ValueError, TypeError): pass
            if 'max' in rules:
                try:
                    if float(value) > float(rules['max']):
                        return False, f"{field.name} 最大值为 {rules['max']}"
                except (ValueError, TypeError): pass
            if 'pattern' in rules and not re.match(rules['pattern'], str(value)):
                return False, f"{field.name} 格式不符合要求"
        return True, None
    
    def apply_filter(self, data: List[Dict[str, Any]], filter_group: FilterGroup) -> List[Dict[str, Any]]:
        if not filter_group.conditions:
            return data
        result = []
        for item in data:
            matches = [self._check_condition(item, c) for c in filter_group.conditions]
            if filter_group.logic == 'AND':
                if all(matches): result.append(item)
            else:
                if any(matches): result.append(item)
        return result
    
    def _check_condition(self, item: Dict[str, Any], condition: FilterCondition) -> bool:
        field_value = item.get(condition.field)
        if condition.operator == 'eq': return field_value == condition.value
        elif condition.operator == 'ne': return field_value != condition.value
        elif condition.operator == 'gt':
            try: return float(field_value) > float(condition.value)
            except (ValueError, TypeError): return False
        elif condition.operator == 'lt':
            try: return float(field_value) < float(condition.value)
            except (ValueError, TypeError): return False
        elif condition.operator == 'gte':
            try: return float(field_value) >= float(condition.value)
            except (ValueError, TypeError): return False
        elif condition.operator == 'lte':
            try: return float(field_value) <= float(condition.value)
            except (ValueError, TypeError): return False
        elif condition.operator == 'contains':
            if field_value is None: return False
            return str(condition.value).lower() in str(field_value).lower()
        elif condition.operator == 'starts_with':
            if field_value is None: return False
            return str(field_value).lower().startswith(str(condition.value).lower())
        elif condition.operator == 'ends_with':
            if field_value is None: return False
            return str(field_value).lower().endswith(str(condition.value).lower())
        elif condition.operator == 'in':
            if isinstance(condition.value, list): return field_value in condition.value
            return field_value == condition.value
        elif condition.operator == 'between':
            if isinstance(condition.value, (list, tuple)) and len(condition.value) == 2:
                try: return float(condition.value[0]) <= float(field_value) <= float(condition.value[1])
                except (ValueError, TypeError): return False
            return False
        elif condition.operator == 'is_null': return field_value is None or field_value == ''
        elif condition.operator == 'is_not_null': return field_value is not None and field_value != ''
        return False
    
    def _generate_id(self) -> str:
        import uuid
        return f"field_{uuid.uuid4().hex[:8]}"


def get_field_manager() -> CustomFieldManager:
    return CustomFieldManager()


if __name__ == '__main__':
    manager = CustomFieldManager()
    field = CustomField(
        id='', name='客户等级', field_type=FieldType.SELECT, entity_type='customer', required=True,
        options=[FieldOption('A', 'VIP客户', '#FF6B6B'), FieldOption('B', '重要客户', '#4ECDC4'), FieldOption('C', '普通客户', '#45B7D1')],
        sort_order=1,
    )
    created = manager.create_field(field)
    print(f"创建字段: {created.to_dict()}")
    valid, error = manager.validate_value(created.id, 'A')
    print(f"验证结果: {valid}, {error}")

```
