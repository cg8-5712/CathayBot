"""
Statistics 插件数据模型
"""

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Index, Date, Text
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


class ChatMessage(BaseModel):
    """聊天记录 (从 Redis 同步持久化)"""

    __tablename__ = "chat_messages"

    message_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    conv_type: Mapped[str] = mapped_column(String(10), nullable=False)  # group / private
    conv_id: Mapped[str] = mapped_column(String(20), nullable=False)  # 群号或用户ID
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_name: Mapped[str] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_message: Mapped[str] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_chat_conv", "conv_type", "conv_id"),
        Index("ix_chat_user", "user_id"),
        Index("ix_chat_timestamp", "timestamp"),
        Index("ix_chat_message_id", "message_id"),
    )


class Conversation(BaseModel):
    """会话信息 (群/私聊)"""

    __tablename__ = "conversations"

    conv_type: Mapped[str] = mapped_column(String(10), nullable=False)  # group / private
    conv_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    avatar: Mapped[str] = mapped_column(String(500), nullable=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_conv_type_id", "conv_type", "conv_id"),
        Index("ix_conv_last_msg", "last_message_at"),
    )


class UserGroupMessageStats(BaseModel):
    """用户群组消息统计聚合表"""

    __tablename__ = "user_group_message_stats"

    group_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_sync_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_user_group_stats", "group_id", "user_id", unique=True),
    )


class UserGroupDailyStats(BaseModel):
    """用户群组每日消息统计"""

    __tablename__ = "user_group_daily_stats"

    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    group_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_daily_stats", "date", "group_id", "user_id", unique=True),
        Index("ix_daily_stats_date", "date"),
    )
