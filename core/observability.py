"""桥接存根: core.observability（可观测性/NOP 存根）"""

class ObservableBridge:
    """可观测性桥接 — 当前为最小存根，不采集遥测数据"""
    def __init__(self, memory_store=None, **kwargs):
        self.memory_store = memory_store

    def record(self, *args, **kwargs):
        pass

    def flush(self):
        pass
