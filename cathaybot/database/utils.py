"""
数据库工具函数

提供一些常用的数据库操作辅助函数。
"""

from typing import Type, TypeVar, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import Base

ModelT = TypeVar("ModelT", bound=Base)


async def exists(
    session: AsyncSession,
    model: Type[ModelT],
    **filters: Any
) -> bool:
    """
    检查是否存在满足条件的记录

    Args:
        session: 数据库会话
        model: 模型类
        **filters: 过滤条件

    Returns:
        是否存在

    Example:
        ```python
        # 检查用户名是否存在
        exists = await exists(session, User, username="alice")
        ```
    """
    stmt = select(func.count()).select_from(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    result = await session.execute(stmt)
    count = result.scalar_one()
    return count > 0


async def get_or_create(
    session: AsyncSession,
    model: Type[ModelT],
    defaults: Optional[dict[str, Any]] = None,
    **filters: Any
) -> tuple[ModelT, bool]:
    """
    获取或创建记录

    Args:
        session: 数据库会话
        model: 模型类
        defaults: 创建时的默认值
        **filters: 查询条件

    Returns:
        (对象, 是否新创建)

    Example:
        ```python
        user, created = await get_or_create(
            session,
            User,
            defaults={"email": "alice@example.com"},
            username="alice"
        )
        if created:
            print("创建了新用户")
        else:
            print("用户已存在")
        ```
    """
    # 尝试查询
    stmt = select(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance, False

    # 不存在则创建
    defaults = defaults or {}
    create_data = {**filters, **defaults}
    instance = model(**create_data)
    session.add(instance)
    await session.flush()
    await session.refresh(instance)
    return instance, True


async def update_or_create(
    session: AsyncSession,
    model: Type[ModelT],
    defaults: Optional[dict[str, Any]] = None,
    **filters: Any
) -> tuple[ModelT, bool]:
    """
    更新或创建记录

    Args:
        session: 数据库会话
        model: 模型类
        defaults: 更新/创建时的值
        **filters: 查询条件

    Returns:
        (对象, 是否新创建)

    Example:
        ```python
        user, created = await update_or_create(
            session,
            User,
            defaults={"email": "newemail@example.com", "age": 25},
            username="alice"
        )
        ```
    """
    # 尝试查询
    stmt = select(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    defaults = defaults or {}

    if instance:
        # 存在则更新
        for key, value in defaults.items():
            setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance, False

    # 不存在则创建
    create_data = {**filters, **defaults}
    instance = model(**create_data)
    session.add(instance)
    await session.flush()
    await session.refresh(instance)
    return instance, True


async def count_by_date_range(
    session: AsyncSession,
    model: Type[ModelT],
    date_field: str = "created_at",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    **filters: Any
) -> int:
    """
    统计日期范围内的记录数

    Args:
        session: 数据库会话
        model: 模型类
        date_field: 日期字段名
        start_date: 开始日期
        end_date: 结束日期
        **filters: 额外过滤条件

    Returns:
        记录数量

    Example:
        ```python
        # 统计最近7天的用户注册数
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(days=7)
        count = await count_by_date_range(
            session,
            User,
            date_field="created_at",
            start_date=start
        )
        ```
    """
    stmt = select(func.count()).select_from(model)

    date_column = getattr(model, date_field)
    if start_date:
        stmt = stmt.where(date_column >= start_date)
    if end_date:
        stmt = stmt.where(date_column <= end_date)

    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)

    result = await session.execute(stmt)
    return result.scalar_one()


async def get_recent(
    session: AsyncSession,
    model: Type[ModelT],
    limit: int = 10,
    date_field: str = "created_at",
    **filters: Any
) -> list[ModelT]:
    """
    获取最近的记录

    Args:
        session: 数据库会话
        model: 模型类
        limit: 限制数量
        date_field: 日期字段名
        **filters: 过滤条件

    Returns:
        记录列表

    Example:
        ```python
        # 获取最近10条活跃用户
        users = await get_recent(
            session,
            User,
            limit=10,
            status="active"
        )
        ```
    """
    stmt = select(model)

    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)

    date_column = getattr(model, date_field)
    stmt = stmt.order_by(date_column.desc()).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_by_ids(
    session: AsyncSession,
    model: Type[ModelT],
    ids: list[int]
) -> list[ModelT]:
    """
    根据 ID 列表批量获取记录

    Args:
        session: 数据库会话
        model: 模型类
        ids: ID 列表

    Returns:
        记录列表

    Example:
        ```python
        users = await get_by_ids(session, User, [1, 2, 3, 4, 5])
        ```
    """
    if not ids:
        return []

    stmt = select(model).where(model.id.in_(ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def increment(
    session: AsyncSession,
    model: Type[ModelT],
    id: int,
    field: str,
    amount: int = 1
) -> Optional[ModelT]:
    """
    增加字段值

    Args:
        session: 数据库会话
        model: 模型类
        id: 记录 ID
        field: 字段名
        amount: 增加的数量

    Returns:
        更新后的对象

    Example:
        ```python
        # 增加文章浏览次数
        article = await increment(session, Article, id=1, field="view_count")
        ```
    """
    stmt = select(model).where(model.id == id)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        current_value = getattr(instance, field, 0)
        setattr(instance, field, current_value + amount)
        await session.flush()
        await session.refresh(instance)

    return instance


async def decrement(
    session: AsyncSession,
    model: Type[ModelT],
    id: int,
    field: str,
    amount: int = 1
) -> Optional[ModelT]:
    """
    减少字段值

    Args:
        session: 数据库会话
        model: 模型类
        id: 记录 ID
        field: 字段名
        amount: 减少的数量

    Returns:
        更新后的对象

    Example:
        ```python
        # 减少库存
        product = await decrement(session, Product, id=1, field="stock", amount=5)
        ```
    """
    stmt = select(model).where(model.id == id)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        current_value = getattr(instance, field, 0)
        setattr(instance, field, max(0, current_value - amount))
        await session.flush()
        await session.refresh(instance)

    return instance


async def toggle(
    session: AsyncSession,
    model: Type[ModelT],
    id: int,
    field: str
) -> Optional[ModelT]:
    """
    切换布尔字段值

    Args:
        session: 数据库会话
        model: 模型类
        id: 记录 ID
        field: 布尔字段名

    Returns:
        更新后的对象

    Example:
        ```python
        # 切换用户激活状态
        user = await toggle(session, User, id=1, field="is_active")
        ```
    """
    stmt = select(model).where(model.id == id)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        current_value = getattr(instance, field, False)
        setattr(instance, field, not current_value)
        await session.flush()
        await session.refresh(instance)

    return instance


async def get_random(
    session: AsyncSession,
    model: Type[ModelT],
    limit: int = 1,
    **filters: Any
) -> list[ModelT]:
    """
    随机获取记录

    Args:
        session: 数据库会话
        model: 模型类
        limit: 限制数量
        **filters: 过滤条件

    Returns:
        随机记录列表

    Example:
        ```python
        # 随机获取5个活跃用户
        users = await get_random(session, User, limit=5, status="active")
        ```
    """
    stmt = select(model)

    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)

    stmt = stmt.order_by(func.random()).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())
