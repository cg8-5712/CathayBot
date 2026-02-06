"""
分页助手

提供增强的分页功能，包含总数、总页数等信息。
"""

from dataclasses import dataclass
from typing import TypeVar, Generic, Sequence, Any, Optional, Type
from math import ceil

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import Base

ModelT = TypeVar("ModelT", bound=Base)


@dataclass
class Page(Generic[ModelT]):
    """
    分页结果

    Attributes:
        items: 当前页的数据列表
        total: 总记录数
        page: 当前页码（从 1 开始）
        page_size: 每页大小
        total_pages: 总页数
        has_next: 是否有下一页
        has_prev: 是否有上一页
    """

    items: Sequence[ModelT]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "items": list(self.items),
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


class Paginator(Generic[ModelT]):
    """
    分页器

    提供便捷的分页查询功能。

    Example:
        ```python
        paginator = Paginator(User)

        # 基础分页
        page = await paginator.paginate(session, page=1, page_size=10)
        print(f"总共 {page.total} 条记录，当前第 {page.page} 页")

        # 带过滤条件的分页
        page = await paginator.paginate(
            session,
            page=1,
            page_size=10,
            filters={"status": "active"},
            order_by="created_at",
            desc=True
        )
        ```
    """

    def __init__(self, model: Type[ModelT]):
        self.model = model

    async def paginate(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[str] = None,
        desc: bool = False,
        filters: Optional[dict[str, Any]] = None,
    ) -> Page[ModelT]:
        """
        执行分页查询

        Args:
            session: 数据库会话
            page: 页码（从 1 开始）
            page_size: 每页大小
            order_by: 排序字段
            desc: 是否降序
            filters: 过滤条件

        Returns:
            分页结果
        """
        filters = filters or {}

        # 计算总数
        count_stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            count_stmt = count_stmt.where(getattr(self.model, key) == value)
        total = (await session.execute(count_stmt)).scalar_one()

        # 计算分页信息
        total_pages = ceil(total / page_size) if total > 0 else 1
        page = max(1, min(page, total_pages))  # 确保页码在有效范围内
        offset = (page - 1) * page_size

        # 查询数据
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)

        if order_by:
            order_column = getattr(self.model, order_by)
            stmt = stmt.order_by(order_column.desc() if desc else order_column)

        stmt = stmt.offset(offset).limit(page_size)
        items = (await session.execute(stmt)).scalars().all()

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class SoftDeletePaginator(Paginator[ModelT]):
    """
    支持软删除的分页器

    自动过滤已删除的记录。

    Example:
        ```python
        paginator = SoftDeletePaginator(User)

        # 默认不包含已删除记录
        page = await paginator.paginate(session, page=1, page_size=10)

        # 包含已删除记录
        page = await paginator.paginate(
            session,
            page=1,
            page_size=10,
            include_deleted=True
        )
        ```
    """

    async def paginate(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[str] = None,
        desc: bool = False,
        filters: Optional[dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> Page[ModelT]:
        """
        执行分页查询

        Args:
            session: 数据库会话
            page: 页码（从 1 开始）
            page_size: 每页大小
            order_by: 排序字段
            desc: 是否降序
            filters: 过滤条件
            include_deleted: 是否包含已删除的记录

        Returns:
            分页结果
        """
        filters = filters or {}

        # 计算总数
        count_stmt = select(func.count()).select_from(self.model)
        if not include_deleted:
            count_stmt = count_stmt.where(self.model.is_deleted == False)
        for key, value in filters.items():
            count_stmt = count_stmt.where(getattr(self.model, key) == value)
        total = (await session.execute(count_stmt)).scalar_one()

        # 计算分页信息
        total_pages = ceil(total / page_size) if total > 0 else 1
        page = max(1, min(page, total_pages))
        offset = (page - 1) * page_size

        # 查询数据
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)

        if order_by:
            order_column = getattr(self.model, order_by)
            stmt = stmt.order_by(order_column.desc() if desc else order_column)

        stmt = stmt.offset(offset).limit(page_size)
        items = (await session.execute(stmt)).scalars().all()

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
