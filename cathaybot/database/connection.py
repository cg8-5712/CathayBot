"""
数据库连接管理

支持 SQLite 和 PostgreSQL，使用 SQLAlchemy 2.0 异步模式。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

from cathaybot.config import config


class Base(DeclarativeBase):
    """SQLAlchemy 模型基类"""
    pass


def _create_engine() -> AsyncEngine:
    """根据配置创建数据库引擎"""
    db_config = config.database
    url = db_config.database_url

    if db_config.type == "postgresql":
        return create_async_engine(
            url,
            echo=False,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
        )
    else:
        # SQLite 不支持连接池配置
        return create_async_engine(url, echo=False)


# 数据库引擎
engine = _create_engine()

# 异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    初始化数据库

    创建所有已注册的表。应在应用启动时调用。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    关闭数据库连接

    应在应用关闭时调用。
    """
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的上下文管理器

    Example:
        ```python
        async with get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
        ```
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入用的会话获取器

    Example:
        ```python
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session_dependency)):
            result = await session.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
