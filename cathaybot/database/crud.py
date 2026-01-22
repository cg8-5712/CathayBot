"""
通用 CRUD 操作

提供基础的增删改查操作封装。
"""

from typing import TypeVar, Generic, Type, Sequence, Optional, Any

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
