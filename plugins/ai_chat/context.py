"""
AI Chat 上下文管理模块
"""

import json
from datetime import datetime
from typing import List, Dict, Optional

from nonebot import logger

from cathaybot.cache import redis_client
from cathaybot.database import get_session

from .config import Config
from .models import ChatHistory


class ContextManager:
    """上下文管理器"""

    def __init__(self, config: Config):
        self.config = config

    def _get_context_key(self, conv_id: str) -> str:
        """获取上下文 Redis Key"""
        return f"ai_chat:context:{conv_id}"

    async def add_message(
        self,
        conv_id: str,
        conv_type: str,
        user_id: str,
        user_name: str,
        role: str,
        content: str,
    ):
        """添加消息到上下文

        Args:
            conv_id: 会话ID (群号或用户ID)
            conv_type: 会话类型 (group/private)
            user_id: 用户ID
            user_name: 用户名
            role: 角色 (user/assistant)
            content: 消息内容
        """
        message = {
            "role": role,
            "content": content,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat(),
        }

        # 存储到 Redis
        key = self._get_context_key(conv_id)
        await redis_client.lpush(key, json.dumps(message, ensure_ascii=False))

        # 限制上下文长度
        if self.config.max_context_messages > 0:
            await redis_client.ltrim(key, 0, self.config.max_context_messages - 1)

        # 设置过期时间
        await redis_client.expire(key, self.config.context_expire_seconds)

        # 异步存储到数据库
        try:
            async with get_session() as session:
                history = ChatHistory(
                    conv_id=conv_id,
                    conv_type=conv_type,
                    user_id=user_id,
                    user_name=user_name,
                    role=role,
                    content=content,
                )
                session.add(history)
                await session.commit()
        except Exception as e:
            logger.warning(f"保存聊天历史到数据库失败: {e}")

    async def get_context(self, conv_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取上下文消息列表

        Args:
            conv_id: 会话ID
            limit: 限制数量 (None 则使用配置的最大值)

        Returns:
            消息列表，格式: [{"role": "user", "content": "...", "user_name": "..."}, ...]
        """
        if not self.config.enable_context:
            return []

        key = self._get_context_key(conv_id)
        limit = limit or self.config.max_context_messages

        # 从 Redis 获取
        messages_json = await redis_client.lrange(key, 0, limit - 1)

        messages = []
        for msg_json in reversed(messages_json):  # 反转顺序，从旧到新
            try:
                msg = json.loads(msg_json)
                messages.append(msg)
            except Exception as e:
                logger.warning(f"解析上下文消息失败: {e}")

        return messages

    async def clear_context(self, conv_id: str):
        """清空上下文"""
        key = self._get_context_key(conv_id)
        await redis_client.delete(key)

    async def get_formatted_context(self, conv_id: str) -> List[Dict[str, str]]:
        """获取格式化的上下文（用于 AI API）

        Returns:
            格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        messages = await self.get_context(conv_id)

        formatted = []
        for msg in messages:
            # 对于用户消息，添加用户名前缀
            content = msg["content"]
            if msg["role"] == "user":
                content = f"[{msg.get('user_name', 'User')}]: {content}"

            formatted.append({"role": msg["role"], "content": content})

        # 上下文压缩
        if self.config.enable_context_compression and len(formatted) > self.config.keep_recent_messages:
            formatted = self._compress_context(formatted)

        return formatted

    def _compress_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """压缩上下文

        策略：
        - 保留最近 N 条完整消息
        - 更早的消息生成摘要
        """
        keep_count = self.config.keep_recent_messages
        if len(messages) <= keep_count:
            return messages

        recent = messages[-keep_count:]  # 最近N条
        old = messages[:-keep_count]     # 更早的

        # 生成简单摘要
        old_count = len(old)
        summary = f"[历史对话摘要: 之前讨论了 {old_count} 轮对话]"

        return [{"role": "system", "content": summary}] + recent

    async def get_context_summary(self, conv_id: str) -> str:
        """获取上下文摘要（用于长上下文压缩）"""
        messages = await self.get_context(conv_id)

        if not messages:
            return ""

        # 简单的摘要：最近 N 条消息的概要
        summary_parts = []
        for msg in messages[-5:]:  # 最近 5 条
            role = "用户" if msg["role"] == "user" else "助手"
            content = msg["content"][:50]  # 截取前 50 字符
            summary_parts.append(f"{role}: {content}...")

        return "\n".join(summary_parts)
