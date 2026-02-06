"""
查询构建器

提供灵活的查询条件构建功能，支持复杂的查询操作。
"""

from typing import TypeVar, Generic, Type, Any, Sequence, Optional
from datetime import datetime

from sqlalchemy import select, and_, or_, not_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from .connection import Base

ModelT = TypeVar("ModelT", bound=Base)


class QueryBuilder(Generic[ModelT]):
    """
    查询构建器

    提供链式调用的查询构建功能，支持复杂的查询条件。

    Example:
        ```python
        builder = QueryBuilder(User)

        # 基础查询
        users = await builder.filter(status="active").all(session)

        # 复杂查询
        users = await (
            builder
            .filter(status="active")
            .like(username="%admin%")
            .in_(role=["admin", "moderator"])
            .between(created_at=(start_date, end_date))
            .order_by("created_at", desc=True)
            .limit(10)
            .all(session)
        )

        # 或条件
        users = await (
            builder
            .or_(
                builder.filter(status="active"),
                builder.filter(role="admin")
            )
            .all(session)
        )
        ```
    """

    def __init__(self, model: Type[ModelT]):
        self.model = model
        self._stmt: Select = select(model)
        self._filters: list[Any] = []

    def filter(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加等值过滤条件

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            查询构建器实例（支持链式调用）
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) == value)
        return self

    def filter_not(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加不等值过滤条件

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) != value)
        return self

    def like(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加 LIKE 模糊查询条件

        Args:
            **kwargs: 字段名=模式的过滤条件

        Returns:
            查询构建器实例

        Example:
            ```python
            # 查询用户名包含 "admin" 的用户
            builder.like(username="%admin%")
            ```
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key).like(value))
        return self

    def ilike(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加不区分大小写的 LIKE 查询条件

        Args:
            **kwargs: 字段名=模式的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key).ilike(value))
        return self

    def in_(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加 IN 查询条件

        Args:
            **kwargs: 字段名=值列表的过滤条件

        Returns:
            查询构建器实例

        Example:
            ```python
            # 查询角色为 admin 或 moderator 的用户
            builder.in_(role=["admin", "moderator"])
            ```
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key).in_(value))
        return self

    def not_in(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加 NOT IN 查询条件

        Args:
            **kwargs: 字段名=值列表的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key).not_in(value))
        return self

    def between(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加 BETWEEN 范围查询条件

        Args:
            **kwargs: 字段名=(最小值, 最大值)的过滤条件

        Returns:
            查询构建器实例

        Example:
            ```python
            # 查询创建时间在指定范围内的记录
            builder.between(created_at=(start_date, end_date))
            ```
        """
        for key, (min_val, max_val) in kwargs.items():
            self._filters.append(getattr(self.model, key).between(min_val, max_val))
        return self

    def gt(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加大于条件

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) > value)
        return self

    def gte(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加大于等于条件

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) >= value)
        return self

    def lt(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加小于条件

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) < value)
        return self

    def lte(self, **kwargs: Any) -> "QueryBuilder[ModelT]":
        """
        添加小于等于条件

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            查询构建器实例
        """
        for key, value in kwargs.items():
            self._filters.append(getattr(self.model, key) <= value)
        return self

    def is_null(self, *fields: str) -> "QueryBuilder[ModelT]":
        """
        添加 IS NULL 条件

        Args:
            *fields: 字段名列表

        Returns:
            查询构建器实例

        Example:
            ```python
            builder.is_null("deleted_at")
            ```
        """
        for field in fields:
            self._filters.append(getattr(self.model, field).is_(None))
        return self

    def is_not_null(self, *fields: str) -> "QueryBuilder[ModelT]":
        """
        添加 IS NOT NULL 条件

        Args:
            *fields: 字段名列表

        Returns:
            查询构建器实例
        """
        for field in fields:
            self._filters.append(getattr(self.model, field).is_not(None))
        return self

    def and_(self, *conditions: "QueryBuilder[ModelT]") -> "QueryBuilder[ModelT]":
        """
        添加 AND 条件组合

        Args:
            *conditions: 查询构建器实例列表

        Returns:
            查询构建器实例
        """
        combined_filters = []
        for condition in conditions:
            combined_filters.extend(condition._filters)
        self._filters.append(and_(*combined_filters))
        return self

    def or_(self, *conditions: "QueryBuilder[ModelT]") -> "QueryBuilder[ModelT]":
        """
        添加 OR 条件组合

        Args:
            *conditions: 查询构建器实例列表

        Returns:
            查询构建器实例

        Example:
            ```python
            builder.or_(
                QueryBuilder(User).filter(status="active"),
                QueryBuilder(User).filter(role="admin")
            )
            ```
        """
        combined_filters = []
        for condition in conditions:
            combined_filters.extend(condition._filters)
        self._filters.append(or_(*combined_filters))
        return self

    def not_(self, condition: "QueryBuilder[ModelT]") -> "QueryBuilder[ModelT]":
        """
        添加 NOT 条件

        Args:
            condition: 查询构建器实例

        Returns:
            查询构建器实例
        """
        self._filters.append(not_(and_(*condition._filters)))
        return self

    def order_by(self, field: str, desc: bool = False) -> "QueryBuilder[ModelT]":
        """
        添加排序条件

        Args:
            field: 排序字段
            desc: 是否降序

        Returns:
            查询构建器实例
        """
        order_column = getattr(self.model, field)
        self._stmt = self._stmt.order_by(
            order_column.desc() if desc else order_column
        )
        return self

    def limit(self, limit: int) -> "QueryBuilder[ModelT]":
        """
        限制返回数量

        Args:
            limit: 限制数量

        Returns:
            查询构建器实例
        """
        self._stmt = self._stmt.limit(limit)
        return self

    def offset(self, offset: int) -> "QueryBuilder[ModelT]":
        """
        设置偏移量

        Args:
            offset: 偏移量

        Returns:
            查询构建器实例
        """
        self._stmt = self._stmt.offset(offset)
        return self

    def _build_stmt(self) -> Select:
        """构建最终的查询语句"""
        if self._filters:
            return self._stmt.where(and_(*self._filters))
        return self._stmt

    async def all(self, session: AsyncSession) -> Sequence[ModelT]:
        """
        执行查询并返回所有结果

        Args:
            session: 数据库会话

        Returns:
            查询结果列表
        """
        stmt = self._build_stmt()
        result = await session.execute(stmt)
        return result.scalars().all()

    async def first(self, session: AsyncSession) -> Optional[ModelT]:
        """
        执行查询并返回第一条结果

        Args:
            session: 数据库会话

        Returns:
            查询结果，不存在则返回 None
        """
        stmt = self._build_stmt().limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self, session: AsyncSession) -> int:
        """
        统计查询结果数量

        Args:
            session: 数据库会话

        Returns:
            记录数量
        """
        stmt = select(func.count()).select_from(self.model)
        if self._filters:
            stmt = stmt.where(and_(*self._filters))
        result = await session.execute(stmt)
        return result.scalar_one()

    async def exists(self, session: AsyncSession) -> bool:
        """
        检查是否存在满足条件的记录

        Args:
            session: 数据库会话

        Returns:
            是否存在
        """
        count = await self.count(session)
        return count > 0


class SoftDeleteQueryBuilder(QueryBuilder[ModelT]):
    """
    支持软删除的查询构建器

    自动过滤已删除的记录。

    Example:
        ```python
        builder = SoftDeleteQueryBuilder(User)

        # 默认不包含已删除记录
        users = await builder.filter(status="active").all(session)

        # 包含已删除记录
        users = await builder.include_deleted().filter(status="active").all(session)

        # 只查询已删除记录
        users = await builder.only_deleted().all(session)
        ```
    """

    def __init__(self, model: Type[ModelT]):
        super().__init__(model)
        self._include_deleted = False
        self._only_deleted = False

    def include_deleted(self) -> "SoftDeleteQueryBuilder[ModelT]":
        """
        包含已删除的记录

        Returns:
            查询构建器实例
        """
        self._include_deleted = True
        self._only_deleted = False
        return self

    def only_deleted(self) -> "SoftDeleteQueryBuilder[ModelT]":
        """
        只查询已删除的记录

        Returns:
            查询构建器实例
        """
        self._only_deleted = True
        self._include_deleted = False
        return self

    def _build_stmt(self) -> Select:
        """构建最终的查询语句"""
        filters = list(self._filters)

        # 添加软删除过滤条件
        if self._only_deleted:
            filters.append(self.model.is_deleted == True)
        elif not self._include_deleted:
            filters.append(self.model.is_deleted == False)

        if filters:
            return self._stmt.where(and_(*filters))
        return self._stmt
