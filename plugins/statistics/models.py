"""
Statistics 插件数据模型
"""

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Index, Date
from sqlalchemy.orm import Mapped, mapped_column

from cathaybot.database.models import BaseModel


class MessageRecord(BaseModel):
    """消息记录 (原始记录，可选使用)"""

    __tablename__ = "stat_message_records"

    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    group_id: Mapped[str] = mapped_column(String(20), nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_message_user_group", "user_id", "group_id"),
        Index("ix_message_timestamp", "timestamp"),
    )


class CommandRecord(BaseModel):
    """命令调用记录 (原始记录，可选使用)"""

    __tablename__ = "stat_command_records"

    plugin_name: Mapped[str] = mapped_column(String(50), nullable=False)
    command: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    group_id: Mapped[str] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_command_plugin", "plugin_name"),
        Index("ix_command_user_group", "user_id", "group_id"),
        Index("ix_command_timestamp", "timestamp"),
    )


class DailyMessageStat(BaseModel):
    """每日消息统计 (从 Redis 同步)"""

    __tablename__ = "stat_daily_messages"

    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    group_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_daily_msg_date_group", "date", "group_id"),
        Index("ix_daily_msg_user", "user_id"),
    )


class DailyCommandStat(BaseModel):
    """每日命令统计 (从 Redis 同步)"""

    __tablename__ = "stat_daily_commands"

    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    plugin_name: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_daily_cmd_date", "date"),
        Index("ix_daily_cmd_plugin", "plugin_name"),
    )
