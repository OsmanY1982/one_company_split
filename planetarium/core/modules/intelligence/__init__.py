# 智能中心模块
try:
    from core.modules.intelligence.intelligence_window import IntelligenceWindow
except ImportError:
    IntelligenceWindow = None