"""
数据库模型基类和通用混入类
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .connection import Base


class TimestampMixin:
    """时间戳混入类，提供 created_at 和 updated_at 字段"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class IDMixin:
    """主键混入类，提供自增 id 字段"""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class SoftDeleteMixin:
    """
    软删除混入类，提供 is_deleted 和 deleted_at 字段

    软删除不会真正删除数据，而是标记为已删除。
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )


class BaseModel(Base, IDMixin, TimestampMixin):
    """
    通用模型基类

    包含 id, created_at, updated_at 字段。
    所有业务模型建议继承此类。

    Example:
        ```python
        class User(BaseModel):
            __tablename__ = "users"

            username: Mapped[str] = mapped_column(String(50), unique=True)
            email: Mapped[str] = mapped_column(String(100))
        ```
    """

    __abstract__ = True


class SoftDeleteModel(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    """
    支持软删除的模型基类

    包含 id, created_at, updated_at, is_deleted, deleted_at 字段。
    需要软删除功能的模型建议继承此类。

    Example:
        ```python
        class User(SoftDeleteModel):
            __tablename__ = "users"

            username: Mapped[str] = mapped_column(String(50), unique=True)
            email: Mapped[str] = mapped_column(String(100))
        ```
    """

    __abstract__ = True
