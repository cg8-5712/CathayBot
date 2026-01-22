"""
Statistics 插件 - 发言/调用统计

使用 Redis 缓存实时数据，定期同步到数据库。
支持图片和文字输出。
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Sequence

from nonebot import get_driver, on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from sqlalchemy import select, func, and_

from cathaybot.config import config as global_config
from cathaybot.cache import redis_client
from cathaybot.database import get_session

from .config import Config
from .models import MessageRecord, CommandRecord, DailyMessageStat, DailyCommandStat
from .templates import STAT_TEMPLATE

__plugin_meta__ = PluginMetadata(
    name="统计",
    description="统计群发言次数、插件调用次数",
    usage="""
/stat today [--raw] - 今日群发言统计
/stat week [--raw] - 本周群发言统计
/stat month [--raw] - 本月群发言统计
/stat user [@用户] [--raw] - 用户统计
/stat plugin [--raw] - 插件调用排行

--raw 参数输出纯文字，否则输出图片
    """.strip(),
    type="application",
    config=Config,
    extra={
        "author": "cg8-5712",
        "version": "1.0.0",
        "category": "工具",
    },
)

# 加载配置
plugin_config = Config.load("statistics")

driver = get_driver()

# ==================== Redis Key 设计 ====================
#
# 统计数据 Key 结构:
#   stat:msg:daily:{date}:{group_id}     -> Hash { user_id: count }  今日群消息统计
#   stat:msg:user:{user_id}:daily:{date} -> int  用户今日总消息数
#   stat:cmd:daily:{date}                -> Hash { plugin_name: count }  今日命令统计
#   stat:cmd:user:{user_id}:daily:{date} -> int  用户今日命令数
#
# 聊天记录 Key 结构:
#   chat:group:{group_id}:messages       -> List [json_message, ...]  群聊消息列表
#   chat:private:{user_id}:messages      -> List [json_message, ...]  私聊消息列表
#   chat:group:{group_id}:info           -> Hash { name, avatar, last_time }  群信息
#


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


# ==================== 消息记录 (Redis) ====================

msg_recorder = on_message(priority=99, block=False)


@msg_recorder.handle()
async def record_message(event: MessageEvent):
    """记录消息到 Redis"""
    if not plugin_config.track_messages:
        return

    user_id = str(event.user_id)
    date_key = get_date_key()

    if isinstance(event, GroupMessageEvent):
        group_id = str(event.group_id)

        # 群消息统计: stat:msg:daily:{date}:{group_id} -> { user_id: count }
        await redis_client.hincrby(f"stat:msg:daily:{date_key}:{group_id}", user_id, 1)

        # 保存聊天记录到 Redis List
        if plugin_config.save_chat_history:
            msg_data = {
                "id": str(event.message_id),
                "user_id": user_id,
                "user_name": event.sender.nickname or user_id,
                "content": str(event.message),
                "raw": event.raw_message,
                "time": datetime.now().isoformat(),
            }
            await redis_client.lpush(
                f"chat:group:{group_id}:messages",
                json.dumps(msg_data, ensure_ascii=False)
            )
            # 限制列表长度，保留最近 N 条
            await redis_client.ltrim(
                f"chat:group:{group_id}:messages",
                0,
                plugin_config.max_messages_per_chat - 1
            )
    else:
        # 私聊消息
        if plugin_config.save_chat_history:
            msg_data = {
                "id": str(event.message_id),
                "user_id": user_id,
                "user_name": event.sender.nickname or user_id,
                "content": str(event.message),
                "raw": event.raw_message,
                "time": datetime.now().isoformat(),
            }
            await redis_client.lpush(
                f"chat:private:{user_id}:messages",
                json.dumps(msg_data, ensure_ascii=False)
            )
            await redis_client.ltrim(
                f"chat:private:{user_id}:messages",
                0,
                plugin_config.max_messages_per_chat - 1
            )

    # 用户总消息统计
    await redis_client.hincrby(f"stat:msg:user:{user_id}:daily", date_key, 1)

    # 设置过期时间 (7天后自动清理)
    expire_seconds = 7 * 24 * 3600
    if isinstance(event, GroupMessageEvent):
        await redis_client.expire(f"stat:msg:daily:{date_key}:{group_id}", expire_seconds)
    await redis_client.expire(f"stat:msg:user:{user_id}:daily", expire_seconds)


# ==================== 统计命令 ====================

stat_cmd = on_command("stat", aliases={"统计"}, priority=10, block=True)


def parse_raw_flag(args: str) -> tuple[str, bool]:
    """解析 --raw 参数"""
    raw_mode = "--raw" in args
    clean_args = args.replace("--raw", "").strip()
    return clean_args, raw_mode


async def render_image(title: str, subtitle: str, items: list[dict]) -> bytes | None:
    """渲染统计图片"""
    try:
        from nonebot_plugin_htmlrender import html_to_pic
        from jinja2 import Template

        template = Template(STAT_TEMPLATE)
        html = template.render(
            title=title,
            subtitle=subtitle,
            items=items,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        return await html_to_pic(html=html, viewport={"width": 450, "height": 100})
    except ImportError:
        return None
    except Exception:
        return None


def format_text_stat(title: str, subtitle: str, items: list[dict]) -> str:
    """格式化文字统计"""
    lines = [f"📊 {title}", f"📅 {subtitle}", ""]

    if not items:
        lines.append("暂无数据")
    else:
        for i, item in enumerate(items, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            detail = f" ({item['detail']})" if item.get("detail") else ""
            lines.append(f"{medal} {item['name']}{detail}: {item['count']}")

    return "\n".join(lines)


async def send_stat(
    matcher: Matcher,
    title: str,
    subtitle: str,
    items: list[dict],
    raw_mode: bool,
):
    """发送统计结果"""
    if raw_mode or plugin_config.default_output == "text":
        await matcher.finish(format_text_stat(title, subtitle, items))
    else:
        img = await render_image(title, subtitle, items)
        if img:
            await matcher.finish(MessageSegment.image(img))
        else:
            await matcher.finish(format_text_stat(title, subtitle, items))


async def get_group_stats_from_redis(
    group_id: str,
    date_keys: list[str],
    limit: int,
) -> list[tuple[str, int]]:
    """从 Redis 获取群统计数据"""
    user_counts: dict[str, int] = {}

    for date_key in date_keys:
        data = await redis_client.hgetall(f"stat:msg:daily:{date_key}:{group_id}")
        for user_id, count in data.items():
            user_counts[user_id] = user_counts.get(user_id, 0) + int(count)

    # 排序并限制数量
    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_users[:limit]


async def get_plugin_stats_from_redis(
    date_keys: list[str],
    limit: int,
) -> list[tuple[str, int]]:
    """从 Redis 获取插件统计数据"""
    plugin_counts: dict[str, int] = {}

    for date_key in date_keys:
        data = await redis_client.hgetall(f"stat:cmd:daily:{date_key}")
        for plugin_name, count in data.items():
            plugin_counts[plugin_name] = plugin_counts.get(plugin_name, 0) + int(count)

    sorted_plugins = sorted(plugin_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_plugins[:limit]


@stat_cmd.handle()
async def handle_stat(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    """处理统计命令"""
    arg_text = args.extract_plain_text().strip()
    arg, raw_mode = parse_raw_flag(arg_text)

    group_id = str(event.group_id) if isinstance(event, GroupMessageEvent) else None
    now = datetime.now()

    parts = arg.split()
    sub_cmd = parts[0] if parts else "today"

    if sub_cmd in ("today", "今日", "今天"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        date_key = get_date_key()
        stats = await get_group_stats_from_redis(group_id, [date_key], plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        await send_stat(matcher, "今日发言排行", now.strftime("%Y-%m-%d"), items, raw_mode)

    elif sub_cmd in ("week", "本周", "周"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        date_keys = get_week_dates()
        stats = await get_group_stats_from_redis(group_id, date_keys, plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        start_date = (now - timedelta(days=now.weekday())).strftime("%m-%d")
        await send_stat(
            matcher,
            "本周发言排行",
            f"{start_date} ~ {now.strftime('%m-%d')}",
            items,
            raw_mode,
        )

    elif sub_cmd in ("month", "本月", "月"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        date_keys = get_month_dates()
        stats = await get_group_stats_from_redis(group_id, date_keys, plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        await send_stat(matcher, "本月发言排行", now.strftime("%Y年%m月"), items, raw_mode)

    elif sub_cmd in ("plugin", "插件"):
        # 获取近30天的日期
        date_keys = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        stats = await get_plugin_stats_from_redis(date_keys, plugin_config.top_limit)

        items = [{"name": name, "count": count} for name, count in stats]

        await send_stat(matcher, "插件调用排行", "近30天", items, raw_mode)

    elif sub_cmd in ("user", "用户"):
        # 获取 @ 的用户
        target_user = None
        for seg in args:
            if seg.type == "at":
                target_user = str(seg.data.get("qq"))
                break

        if not target_user:
            target_user = str(event.user_id)

        # 从 Redis 获取用户统计
        date_key = get_date_key()
        today_count = await redis_client.hget(f"stat:msg:user:{target_user}:daily", date_key)
        today_count = int(today_count) if today_count else 0

        # 获取用户总消息数 (近7天)
        total_count = 0
        for i in range(7):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            c = await redis_client.hget(f"stat:msg:user:{target_user}:daily", d)
            total_count += int(c) if c else 0

        # 获取命令调用数
        cmd_count = 0
        for i in range(7):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            c = await redis_client.hget(f"stat:cmd:user:{target_user}:daily", d)
            cmd_count += int(c) if c else 0

        try:
            info = await bot.get_stranger_info(user_id=int(target_user))
            name = info.get("nickname", target_user)
        except Exception:
            name = target_user

        items = [
            {"name": "今日发言", "count": today_count},
            {"name": "近7天发言", "count": total_count},
            {"name": "近7天命令", "count": cmd_count},
        ]

        await send_stat(matcher, f"{name} 的统计", f"QQ: {target_user}", items, raw_mode)

    else:
        await matcher.finish("未知的统计类型，请使用 /help 统计 查看用法")


# ==================== 命令调用记录 ====================

@driver.on_startup
async def setup_command_hook():
    """设置命令调用记录钩子"""
    from nonebot.message import run_preprocessor

    @run_preprocessor
    async def record_command(matcher: Matcher, event: MessageEvent):
        """记录命令调用到 Redis"""
        if not plugin_config.track_commands:
            return

        if not matcher.plugin:
            return

        plugin_name = matcher.plugin.name
        if matcher.plugin.metadata:
            plugin_name = matcher.plugin.metadata.name

        user_id = str(event.user_id)
        date_key = get_date_key()

        # 插件调用统计
        await redis_client.hincrby(f"stat:cmd:daily:{date_key}", plugin_name, 1)

        # 用户命令统计
        await redis_client.hincrby(f"stat:cmd:user:{user_id}:daily", date_key, 1)

        # 设置过期时间
        expire_seconds = 30 * 24 * 3600  # 30天
        await redis_client.expire(f"stat:cmd:daily:{date_key}", expire_seconds)
        await redis_client.expire(f"stat:cmd:user:{user_id}:daily", expire_seconds)


# ==================== 定时同步到数据库 ====================

async def sync_stats_to_db():
    """将 Redis 统计数据同步到数据库"""
    if not global_config.redis.enabled:
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


@driver.on_startup
async def start_sync_task():
    """启动定时同步任务"""
    async def sync_loop():
        while True:
            await asyncio.sleep(global_config.redis.sync_interval)
            try:
                await sync_stats_to_db()
            except Exception as e:
                from nonebot import logger
                logger.error(f"同步统计数据失败: {e}")

    asyncio.create_task(sync_loop())
