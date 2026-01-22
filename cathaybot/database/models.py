"""
数据库模型基类和通用混入类
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
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
