"""
CathayBot 核心模块

提供配置加载、数据库连接、工具函数等基础功能。
"""

from .config import config, GlobalConfig

__all__ = ["config", "GlobalConfig"]
