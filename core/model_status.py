"""桥接存根: core.model_status → iqra.core.model_status（函数集）"""

from iqra.core.model_status import (
    mark_model_no_token,
    mark_model_failed,
    is_model_available,
)


class ModelStatus:
    """agent_bridge 兼容包装类——将函数转为静态方法"""
    mark_model_no_token = staticmethod(mark_model_no_token)
    mark_model_failed = staticmethod(mark_model_failed)
    is_model_available = staticmethod(is_model_available)
