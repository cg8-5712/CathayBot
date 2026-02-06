"""
AI Chat 插件数据模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from cathaybot.database import BaseModel


class ChatHistory(BaseModel):
    """聊天历史记录"""

    __tablename__ = "ai_chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conv_id: Mapped[str] = mapped_column(String(64), index=True, comment="会话ID (群号或用户ID)")
    conv_type: Mapped[str] = mapped_column(String(16), comment="会话类型 (group/private)")
    user_id: Mapped[str] = mapped_column(String(32), comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(64), comment="用户名")
    role: Mapped[str] = mapped_column(String(16), comment="角色 (user/assistant)")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="时间戳")


class ChatMemory(BaseModel):
    """AI 记忆存储"""

    __tablename__ = "ai_chat_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conv_id: Mapped[str] = mapped_column(String(64), index=True, comment="会话ID")
    user_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="用户ID (可选)")
    memory_type: Mapped[str] = mapped_column(String(32), comment="记忆类型 (fact/preference/event)")
    key: Mapped[str] = mapped_column(String(128), comment="记忆键")
    value: Mapped[str] = mapped_column(Text, comment="记忆值")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )
