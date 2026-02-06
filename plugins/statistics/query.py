"""
Statistics 插件 - 查询模块

负责从 Redis 和数据库查询统计数据
"""

from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import select, func

from cathaybot.cache import redis_client
from cathaybot.database import get_session

from .config import Config
from .models import UserGroupDailyStats, UserGroupMessageStats

# 加载配置
plugin_config = Config.load("statistics")


def get_date_key(dt: datetime = None) -> str:
    """获取日期 key (YYYY-MM-DD)"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")


def get_week_dates() -> list[str]:
    """获取本周所有日期 key"""
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def get_month_dates() -> list[str]:
    """获取本月所有日期 key"""
    today = datetime.now()
    start = today.replace(day=1)
    dates = []
    current = start
    while current.month == today.month and current <= today:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


class StatQuery:
    """统计查询类"""

    @staticmethod
    async def get_group_stats_today(group_id: str, limit: int) -> List[Tuple[str, int]]:
        """获取今日群发言排行（仅从 Redis）"""
        date_key = get_date_key()
        user_counts: dict[str, int] = {}

        # 从 Redis 获取今日数据
        data = await redis_client.hgetall(f"stat:msg:daily:{date_key}:{group_id}")
        for user_id, count in data.items():
            user_counts[user_id] = int(count)

        # 排序并限制数量
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]

    @staticmethod
    async def get_group_stats_week(group_id: str, limit: int) -> List[Tuple[str, int]]:
        """获取本周群发言排行（数据库 + Redis）"""
        date_keys = get_week_dates()
        user_counts: dict[str, int] = {}

        # 1. 从数据库获取历史数据
        async with get_session() as session:
            result = await session.execute(
                select(
                    UserGroupDailyStats.user_id,
                    func.sum(UserGroupDailyStats.count).label("total")
                )
                .where(
                    UserGroupDailyStats.group_id == group_id,
                    UserGroupDailyStats.date.in_(date_keys)
                )
                .group_by(UserGroupDailyStats.user_id)
            )
            for row in result:
                user_counts[row.user_id] = int(row.total)

        # 2. 从 Redis 获取增量数据
        for date_key in date_keys:
            data = await redis_client.hgetall(f"stat:msg:daily:{date_key}:{group_id}")
            for user_id, count in data.items():
                user_counts[user_id] = user_counts.get(user_id, 0) + int(count)

        # 排序并限制数量
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]

    @staticmethod
    async def get_group_stats_month(group_id: str, limit: int) -> List[Tuple[str, int]]:
        """获取本月群发言排行（数据库 + Redis）"""
        date_keys = get_month_dates()
        user_counts: dict[str, int] = {}

        # 1. 从数据库获取历史数据
        async with get_session() as session:
            result = await session.execute(
                select(
                    UserGroupDailyStats.user_id,
                    func.sum(UserGroupDailyStats.count).label("total")
                )
                .where(
                    UserGroupDailyStats.group_id == group_id,
                    UserGroupDailyStats.date.in_(date_keys)
                )
                .group_by(UserGroupDailyStats.user_id)
            )
            for row in result:
                user_counts[row.user_id] = int(row.total)

        # 2. 从 Redis 获取增量数据
        for date_key in date_keys:
            data = await redis_client.hgetall(f"stat:msg:daily:{date_key}:{group_id}")
            for user_id, count in data.items():
                user_counts[user_id] = user_counts.get(user_id, 0) + int(count)

        # 排序并限制数量
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]

    @staticmethod
    async def get_group_stats_all(group_id: str, limit: int) -> List[Tuple[str, int]]:
        """获取群总发言排行（数据库聚合表 + Redis）"""
        user_counts: dict[str, int] = {}

        # 1. 从数据库聚合表获取历史总数
        async with get_session() as session:
            result = await session.execute(
                select(
                    UserGroupMessageStats.user_id,
                    UserGroupMessageStats.total_count
                )
                .where(UserGroupMessageStats.group_id == group_id)
            )
            for row in result:
                user_counts[row.user_id] = int(row.total_count)

        # 2. 从 Redis 获取所有增量数据（未同步的）
        # 获取所有日期的 Redis 数据
        keys = await redis_client.keys(f"stat:msg:daily:*:{group_id}")
        for key in keys:
            data = await redis_client.hgetall(key)
            for user_id, count in data.items():
                user_counts[user_id] = user_counts.get(user_id, 0) + int(count)

        # 排序并限制数量
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]

    @staticmethod
    async def get_user_stats(user_id: str, group_id: str = None) -> dict:
        """获取用户统计（支持指定群或全局）"""
        stats = {
            "today": 0,
            "week": 0,
            "month": 0,
            "total": 0,
            "cmd_week": 0,
        }

        date_key = get_date_key()
        week_dates = get_week_dates()
        month_dates = get_month_dates()

        # 今日发言（从 Redis）
        if group_id:
            today_count = await redis_client.hget(f"stat:msg:daily:{date_key}:{group_id}", user_id)
            stats["today"] = int(today_count) if today_count else 0
        else:
            # 全局今日（所有群）
            user_daily = await redis_client.hget(f"stat:msg:user:{user_id}:daily", date_key)
            stats["today"] = int(user_daily) if user_daily else 0

        # 本周发言（数据库 + Redis）
        if group_id:
            async with get_session() as session:
                result = await session.execute(
                    select(func.sum(UserGroupDailyStats.count))
                    .where(
                        UserGroupDailyStats.group_id == group_id,
                        UserGroupDailyStats.user_id == user_id,
                        UserGroupDailyStats.date.in_(week_dates)
                    )
                )
                db_count = result.scalar() or 0
                stats["week"] = int(db_count)

            # 加上 Redis 增量
            for d in week_dates:
                c = await redis_client.hget(f"stat:msg:daily:{d}:{group_id}", user_id)
                stats["week"] += int(c) if c else 0
        else:
            # 全局本周
            for d in week_dates:
                c = await redis_client.hget(f"stat:msg:user:{user_id}:daily", d)
                stats["week"] += int(c) if c else 0

        # 本月发言（数据库 + Redis）
        if group_id:
            async with get_session() as session:
                result = await session.execute(
                    select(func.sum(UserGroupDailyStats.count))
                    .where(
                        UserGroupDailyStats.group_id == group_id,
                        UserGroupDailyStats.user_id == user_id,
                        UserGroupDailyStats.date.in_(month_dates)
                    )
                )
                db_count = result.scalar() or 0
                stats["month"] = int(db_count)

            # 加上 Redis 增量
            for d in month_dates:
                c = await redis_client.hget(f"stat:msg:daily:{d}:{group_id}", user_id)
                stats["month"] += int(c) if c else 0

        # 总发言（数据库聚合表 + Redis）
        if group_id:
            async with get_session() as session:
                result = await session.execute(
                    select(UserGroupMessageStats.total_count)
                    .where(
                        UserGroupMessageStats.group_id == group_id,
                        UserGroupMessageStats.user_id == user_id
                    )
                )
                row = result.scalar_one_or_none()
                stats["total"] = int(row) if row else 0

            # 加上 Redis 所有增量
            keys = await redis_client.keys(f"stat:msg:daily:*:{group_id}")
            for key in keys:
                c = await redis_client.hget(key, user_id)
                stats["total"] += int(c) if c else 0

        # 近7天命令数（从 Redis）
        for i in range(7):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            c = await redis_client.hget(f"stat:cmd:user:{user_id}:daily", d)
            stats["cmd_week"] += int(c) if c else 0

        return stats

    @staticmethod
    async def get_plugin_stats(limit: int) -> List[Tuple[str, int]]:
        """获取插件调用排行（近30天）"""
        plugin_counts: dict[str, int] = {}
        now = datetime.now()

        # 从 Redis 获取近30天数据
        date_keys = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        for date_key in date_keys:
            data = await redis_client.hgetall(f"stat:cmd:daily:{date_key}")
            for plugin_name, count in data.items():
                plugin_counts[plugin_name] = plugin_counts.get(plugin_name, 0) + int(count)

        sorted_plugins = sorted(plugin_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_plugins[:limit]
