# -*- coding: utf-8 -*-
"""
modules — 共享模块命名空间。
通过 pkgutil.extend_path 将父项目的 modules 与 iqra 的 modules 合并，
使 modules.astronomy 和 modules.intelligence 可同时访问。
"""
try:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
except (NameError, ImportError):
    pass
