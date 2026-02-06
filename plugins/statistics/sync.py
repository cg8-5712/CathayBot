"""
Statistics 插件 - 数据同步模块

负责将 Redis 数据同步到数据库
"""

import asyncio
import json
from datetime import datetime, timedelta

from nonebot import logger, get_driver
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from cathaybot.cache import redis_client
from cathaybot.config import GlobalConfig
from cathaybot.database import get_session

from .config import Config
from .models import (
    DailyMessageStat,
    DailyCommandStat,
    ChatMessage,
    UserGroupMessageStats,
    UserGroupDailyStats,
)

# 加载配置
plugin_config = Config.load("statistics")


async def sync_stats_to_db():
    """将 Redis 统计数据同步到数据库"""
    if not GlobalConfig.redis.enabled:
        return

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    async with get_session() as session:
        # 同步群消息统计
        group_keys = await redis_client.keys(f"stat:msg:daily:{yesterday}:*")
        for key in group_keys:
            parts = key.split(":")
            if len(parts) >= 5:
                group_id = parts[4]
                data = await redis_client.hgetall(key)

                for user_id, count in data.items():
                    stat = DailyMessageStat(
                        date=yesterday,
                        group_id=group_id,
                        user_id=user_id,
                        count=int(count),
                    )
                    session.add(stat)

        # 同步命令统计
        cmd_data = await redis_client.hgetall(f"stat:cmd:daily:{yesterday}")
        for plugin_name, count in cmd_data.items():
            stat = DailyCommandStat(
                date=yesterday,
                plugin_name=plugin_name,
                count=int(count),
            )
            session.add(stat)

        await session.commit()


async def sync_chat_history_to_db():
    """将 Redis 聊天记录同步到数据库，并更新聚合统计表"""
    if not GlobalConfig.redis.enabled:
        return

    if not plugin_config.save_chat_history:
        return

    try:
        # 获取所有群聊消息 key
        group_keys = await redis_client.keys("chat:group:*:messages")
        private_keys = await redis_client.keys("chat:private:*:messages")

        all_keys = group_keys + private_keys
        synced_count = 0

        # 用于统计每个用户在每个群的消息数
        group_user_counts = {}  # {(group_id, user_id): count}
        daily_counts = {}  # {(date, group_id, user_id): count}

        async with get_session() as session:
            for key in all_keys:
                # 解析 key
                parts = key.split(":")
                if len(parts) < 4:
                    continue

                conv_type = parts[1]  # group / private
                conv_id = parts[2]

                # 只处理群聊统计
                if conv_type != "group":
                    continue

                # 获取 Redis 中的消息数量
                total_count = await redis_client.llen(key)

                if total_count == 0:
                    continue

                # 确定需要同步的消息
                messages_to_sync = []

                if plugin_config.max_messages_per_chat > 0:
                    # 限制模式：只同步超出部分
                    if total_count <= plugin_config.max_messages_per_chat:
                        continue  # 没有超出，不需要同步

                    # 获取超出部分的消息（从尾部开始）
                    start_index = plugin_config.max_messages_per_chat
                    messages_json = await redis_client.lrange(key, start_index, -1)
                    messages_to_sync = messages_json
                else:
                    # 不限制模式：同步所有消息，但不从 Redis 删除
                    messages_json = await redis_client.lrange(key, 0, -1)
                    messages_to_sync = messages_json

                # 同步消息到数据库
                for msg_json in messages_to_sync:
                    try:
                        msg_data = json.loads(msg_json)

                        # 检查消息是否已存在
                        existing = await session.execute(
                            select(ChatMessage).where(ChatMessage.message_id == msg_data["id"])
                        )
                        if existing.scalar_one_or_none():
                            continue  # 已存在，跳过

                        # 创建消息记录
                        msg_time = datetime.fromisoformat(msg_data["time"])
                        chat_msg = ChatMessage(
                            message_id=msg_data["id"],
                            conv_type=conv_type,
                            conv_id=conv_id,
                            user_id=msg_data["user_id"],
                            user_name=msg_data.get("user_name"),
                            content=msg_data["content"],
                            raw_message=msg_data.get("raw"),
                            timestamp=msg_time,
                        )
                        session.add(chat_msg)
                        synced_count += 1

                        # 统计计数
                        group_id = conv_id
                        user_id = msg_data["user_id"]
                        date_key = msg_time.strftime("%Y-%m-%d")

                        # 累计总数
                        key_tuple = (group_id, user_id)
                        group_user_counts[key_tuple] = group_user_counts.get(key_tuple, 0) + 1

                        # 累计每日数
                        daily_key = (date_key, group_id, user_id)
                        daily_counts[daily_key] = daily_counts.get(daily_key, 0) + 1

                    except Exception as e:
                        logger.warning(f"同步消息失败: {e}")
                        continue

                # 如果配置了 max_messages_per_chat > 0，同步后从 Redis 中删除已同步的消息
                if plugin_config.max_messages_per_chat > 0 and len(messages_to_sync) > 0:
                    # 删除已同步的消息（从尾部删除）
                    await redis_client.ltrim(key, 0, plugin_config.max_messages_per_chat - 1)

            # 更新聚合统计表
            if group_user_counts:
                for (group_id, user_id), count in group_user_counts.items():
                    # 使用 upsert 更新或插入
                    stmt = insert(UserGroupMessageStats).values(
                        group_id=group_id,
                        user_id=user_id,
                        total_count=count,
                        last_sync_time=datetime.now(),
                    )
                    # PostgreSQL upsert
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["group_id", "user_id"],
                        set_={
                            "total_count": UserGroupMessageStats.total_count + count,
                            "last_sync_time": datetime.now(),
                        }
                    )
                    await session.execute(stmt)

            # 更新每日统计表
            if daily_counts:
                for (date, group_id, user_id), count in daily_counts.items():
                    stmt = insert(UserGroupDailyStats).values(
                        date=date,
                        group_id=group_id,
                        user_id=user_id,
                        count=count,
                    )
                    # PostgreSQL upsert
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["date", "group_id", "user_id"],
                        set_={"count": UserGroupDailyStats.count + count}
                    )
                    await session.execute(stmt)

            await session.commit()

        if synced_count > 0:
            logger.info(f"同步聊天记录完成: {synced_count} 条消息")

    except Exception as e:
        logger.error(f"同步聊天记录失败: {e}")


async def start_sync_loop():
    """启动定时同步循环"""
    while True:
        await asyncio.sleep(plugin_config.chat_sync_interval)
        try:
            # 同步统计数据
            await sync_stats_to_db()
            # 同步聊天记录
            await sync_chat_history_to_db()
        except Exception as e:
            logger.error(f"同步数据失败: {e}")


def init_sync_task():
    """初始化同步任务"""
    driver = get_driver()

    @driver.on_startup
    async def _():
        asyncio.create_task(start_sync_loop())
