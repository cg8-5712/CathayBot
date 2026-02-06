"""
数据库模块

提供数据库连接管理、模型基类和通用 CRUD 操作。
"""

from .connection import Base, get_session, init_db, close_db, engine
from .models import (
    BaseModel,
    IDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SoftDeleteModel,
)
from .crud import CRUDBase, SoftDeleteCRUD
from .pagination import Page, Paginator, SoftDeletePaginator
from .query import QueryBuilder, SoftDeleteQueryBuilder
from .utils import (
    exists,
    get_or_create,
    update_or_create,
    count_by_date_range,
    get_recent,
    get_by_ids,
    increment,
    decrement,
    toggle,
    get_random,
)

__all__ = [
    # 连接管理
    "Base",
    "get_session",
    "init_db",
    "close_db",
    "engine",
    # 模型基类和混入
    "BaseModel",
    "IDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "SoftDeleteModel",
    # CRUD 操作
    "CRUDBase",
    "SoftDeleteCRUD",
    # 分页
    "Page",
    "Paginator",
    "SoftDeletePaginator",
    # 查询构建器
    "QueryBuilder",
    "SoftDeleteQueryBuilder",
    # 工具函数
    "exists",
    "get_or_create",
    "update_or_create",
    "count_by_date_range",
    "get_recent",
    "get_by_ids",
    "increment",
    "decrement",
    "toggle",
    "get_random",
]
