"""
通用 CRUD 操作

提供基础的增删改查操作封装。
"""

from typing import TypeVar, Generic, Type, Sequence, Optional, Any
from datetime import datetime

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDBase(Generic[ModelT]):
    """
    通用 CRUD 操作基类

    Example:
        ```python
        class UserCRUD(CRUDBase[User]):
            pass

        user_crud = UserCRUD(User)

        # 创建
        user = await user_crud.create(session, username="test", email="test@example.com")

        # 查询
        user = await user_crud.get(session, id=1)
        users = await user_crud.get_multi(session, limit=10)

        # 更新
        await user_crud.update(session, id=1, username="new_name")

        # 删除
        await user_crud.delete(session, id=1)
        ```
    """

    def __init__(self, model: Type[ModelT]):
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> Optional[ModelT]:
        """根据 ID 获取单条记录"""
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by(self, session: AsyncSession, **kwargs: Any) -> Optional[ModelT]:
        """根据条件获取单条记录"""
        stmt = select(self.model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False,
        **filters: Any,
    ) -> Sequence[ModelT]:
        """获取多条记录"""
        stmt = select(self.model)

        # 应用过滤条件
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)

        # 排序
        if order_by:
            order_column = getattr(self.model, order_by)
            stmt = stmt.order_by(order_column.desc() if desc else order_column)

        # 分页
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(self, session: AsyncSession, **filters: Any) -> int:
        """统计记录数"""
        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def create(self, session: AsyncSession, **kwargs: Any) -> ModelT:
        """创建记录"""
        instance = self.model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update(
        self, session: AsyncSession, id: int, **kwargs: Any
    ) -> Optional[ModelT]:
        """更新记录"""
        await session.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        return await self.get(session, id)

    async def delete(self, session: AsyncSession, id: int) -> bool:
        """删除记录"""
        result = await session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def delete_by(self, session: AsyncSession, **kwargs: Any) -> int:
        """根据条件删除记录，返回删除数量"""
        stmt = delete(self.model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.rowcount

    async def bulk_create(
        self, session: AsyncSession, objects: list[dict[str, Any]]
    ) -> list[ModelT]:
        """
        批量创建记录

        Args:
            session: 数据库会话
            objects: 对象字典列表

        Returns:
            创建的对象列表

        Example:
            ```python
            users = await user_crud.bulk_create(
                session,
                [
                    {"username": "user1", "email": "user1@example.com"},
                    {"username": "user2", "email": "user2@example.com"},
                ]
            )
            ```
        """
        instances = [self.model(**obj) for obj in objects]
        session.add_all(instances)
        await session.flush()
        for instance in instances:
            await session.refresh(instance)
        return instances

    async def bulk_update(
        self, session: AsyncSession, updates: list[dict[str, Any]]
    ) -> int:
        """
        批量更新记录

        Args:
            session: 数据库会话
            updates: 更新字典列表，每个字典必须包含 'id' 字段

        Returns:
            更新的记录数

        Example:
            ```python
            count = await user_crud.bulk_update(
                session,
                [
                    {"id": 1, "username": "new_name1"},
                    {"id": 2, "username": "new_name2"},
                ]
            )
            ```
        """
        if not updates:
            return 0

        # 使用 bulk_update_mappings 进行批量更新
        await session.execute(
            update(self.model),
            updates,
        )
        return len(updates)

    async def bulk_delete(self, session: AsyncSession, ids: list[int]) -> int:
        """
        批量删除记录

        Args:
            session: 数据库会话
            ids: 要删除的 ID 列表

        Returns:
            删除的记录数

        Example:
            ```python
            count = await user_crud.bulk_delete(session, [1, 2, 3])
            ```
        """
        if not ids:
            return 0

        result = await session.execute(
            delete(self.model).where(self.model.id.in_(ids))
        )
        return result.rowcount


class SoftDeleteCRUD(CRUDBase[ModelT]):
    """
    支持软删除的 CRUD 操作类

    继承自 CRUDBase，添加软删除相关方法。
    适用于继承了 SoftDeleteMixin 的模型。

    Example:
        ```python
        class UserCRUD(SoftDeleteCRUD[User]):
            pass

        user_crud = UserCRUD(User)

        # 软删除
        await user_crud.soft_delete(session, id=1)

        # 查询时自动过滤已删除记录
        users = await user_crud.get_multi(session, include_deleted=False)

        # 恢复已删除记录
        await user_crud.restore(session, id=1)

        # 永久删除
        await user_crud.hard_delete(session, id=1)
        ```
    """

    async def get(
        self, session: AsyncSession, id: int, include_deleted: bool = False
    ) -> Optional[ModelT]:
        """
        根据 ID 获取单条记录

        Args:
            session: 数据库会话
            id: 记录 ID
            include_deleted: 是否包含已删除的记录

        Returns:
            查询到的记录，不存在则返回 None
        """
        stmt = select(self.model).where(self.model.id == id)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(
        self, session: AsyncSession, include_deleted: bool = False, **kwargs: Any
    ) -> Optional[ModelT]:
        """
        根据条件获取单条记录

        Args:
            session: 数据库会话
            include_deleted: 是否包含已删除的记录
            **kwargs: 查询条件

        Returns:
            查询到的记录，不存在则返回 None
        """
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Sequence[ModelT]:
        """
        获取多条记录

        Args:
            session: 数据库会话
            offset: 偏移量
            limit: 限制数量
            order_by: 排序字段
            desc: 是否降序
            include_deleted: 是否包含已删除的记录
            **filters: 过滤条件

        Returns:
            记录列表
        """
        stmt = select(self.model)

        # 过滤已删除记录
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # 应用过滤条件
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)

        # 排序
        if order_by:
            order_column = getattr(self.model, order_by)
            stmt = stmt.order_by(order_column.desc() if desc else order_column)

        # 分页
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(
        self, session: AsyncSession, include_deleted: bool = False, **filters: Any
    ) -> int:
        """
        统计记录数

        Args:
            session: 数据库会话
            include_deleted: 是否包含已删除的记录
            **filters: 过滤条件

        Returns:
            记录数量
        """
        stmt = select(func.count()).select_from(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def soft_delete(self, session: AsyncSession, id: int) -> bool:
        """
        软删除记录（标记为已删除）

        Args:
            session: 数据库会话
            id: 记录 ID

        Returns:
            是否删除成功
        """
        result = await session.execute(
            update(self.model)
            .where(self.model.id == id)
            .where(self.model.is_deleted == False)
            .values(is_deleted=True, deleted_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def soft_delete_by(self, session: AsyncSession, **kwargs: Any) -> int:
        """
        根据条件软删除记录

        Args:
            session: 数据库会话
            **kwargs: 删除条件

        Returns:
            删除的记录数
        """
        stmt = (
            update(self.model)
            .where(self.model.is_deleted == False)
            .values(is_deleted=True, deleted_at=datetime.utcnow())
        )
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.rowcount

    async def restore(self, session: AsyncSession, id: int) -> bool:
        """
        恢复已删除的记录

        Args:
            session: 数据库会话
            id: 记录 ID

        Returns:
            是否恢复成功
        """
        result = await session.execute(
            update(self.model)
            .where(self.model.id == id)
            .where(self.model.is_deleted == True)
            .values(is_deleted=False, deleted_at=None)
        )
        return result.rowcount > 0

    async def restore_by(self, session: AsyncSession, **kwargs: Any) -> int:
        """
        根据条件恢复已删除的记录

        Args:
            session: 数据库会话
            **kwargs: 恢复条件

        Returns:
            恢复的记录数
        """
        stmt = (
            update(self.model)
            .where(self.model.is_deleted == True)
            .values(is_deleted=False, deleted_at=None)
        )
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.rowcount

    async def hard_delete(self, session: AsyncSession, id: int) -> bool:
        """
        永久删除记录（物理删除）

        Args:
            session: 数据库会话
            id: 记录 ID

        Returns:
            是否删除成功
        """
        result = await session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def hard_delete_by(self, session: AsyncSession, **kwargs: Any) -> int:
        """
        根据条件永久删除记录

        Args:
            session: 数据库会话
            **kwargs: 删除条件

        Returns:
            删除的记录数
        """
        stmt = delete(self.model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await session.execute(stmt)
        return result.rowcount
