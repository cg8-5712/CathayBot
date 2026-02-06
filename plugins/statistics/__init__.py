"""
Statistics 插件 - 发言/调用统计

使用 Redis 缓存实时数据，定期同步到数据库。
支持图片和文字输出。
"""

import json
from datetime import datetime

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

from cathaybot.cache import redis_client

from .config import Config
from .query import StatQuery
from .sync import init_sync_task

__plugin_meta__ = PluginMetadata(
    name="统计",
    description="统计群发言次数、插件调用次数",
    usage="""
/stat [all] [--raw] - 总发言统计（默认）
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
        "version": "2.0.0",
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
#   stat:msg:user:{user_id}:daily        -> Hash { date: count }  用户每日消息数
#   stat:cmd:daily:{date}                -> Hash { plugin_name: count }  今日命令统计
#   stat:cmd:user:{user_id}:daily        -> Hash { date: count }  用户每日命令数
#
# 聊天记录 Key 结构:
#   chat:group:{group_id}:messages       -> List [json_message, ...]  群聊消息列表
#   chat:private:{user_id}:messages      -> List [json_message, ...]  私聊消息列表
#


def get_date_key(dt: datetime = None) -> str:
    """获取日期 key (YYYY-MM-DD)"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")


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
            # 限制列表长度，保留最近 N 条 (0=不限制)
            if plugin_config.max_messages_per_chat > 0:
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
            # 限制列表长度，保留最近 N 条 (0=不限制)
            if plugin_config.max_messages_per_chat > 0:
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


async def render_image(title: str, subtitle: str, items: list[dict], template_type: str = "rank") -> bytes | None:
    """渲染统计图片

    Args:
        title: 标题
        subtitle: 副标题
        items: 数据项列表
        template_type: 模板类型 (rank/user/plugin)
    """
    try:
        from nonebot_plugin_htmlrender import html_to_pic

        # 根据类型构建不同的 HTML
        if template_type == "user":
            html = _build_user_stat_html(title, subtitle, items)
        elif template_type == "plugin":
            html = _build_plugin_stat_html(title, subtitle, items)
        else:
            html = _build_rank_html(title, subtitle, items)

        return await html_to_pic(html=html, viewport={"width": 450, "height": 100})
    except ImportError:
        return None
    except Exception:
        return None


def _build_rank_html(title: str, subtitle: str, items: list[dict]) -> str:
    """构建排行榜 HTML"""
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    items_html = ""
    if items:
        for i, item in enumerate(items, 1):
            rank_class = f"rank-{i}" if i <= 3 else "rank-other"
            detail_html = f'<div class="rank-detail">{item["detail"]}</div>' if item.get("detail") else ""
            items_html += f'''
            <li class="rank-item {rank_class}">
                <div class="rank-num">{i}</div>
                <div class="rank-info">
                    <div class="rank-name">{item["name"]}</div>
                    {detail_html}
                </div>
                <div class="rank-count">{item["count"]}</div>
            </li>
            '''
    else:
        items_html = '<div class="empty">暂无数据</div>'

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-width: 400px; }}
        .container {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 2px solid #f0f0f0; }}
        .header h1 {{ font-size: 24px; color: #333; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 14px; color: #888; }}
        .rank-list {{ list-style: none; }}
        .rank-item {{ display: flex; align-items: center; padding: 12px 16px; margin-bottom: 8px; background: #f8f9fa; border-radius: 12px; transition: transform 0.2s; }}
        .rank-item:hover {{ transform: translateX(4px); }}
        .rank-num {{ width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 12px; }}
        .rank-1 .rank-num {{ background: linear-gradient(135deg, #FFD700, #FFA500); color: white; }}
        .rank-2 .rank-num {{ background: linear-gradient(135deg, #C0C0C0, #A0A0A0); color: white; }}
        .rank-3 .rank-num {{ background: linear-gradient(135deg, #CD7F32, #8B4513); color: white; }}
        .rank-other .rank-num {{ background: #e0e0e0; color: #666; }}
        .rank-info {{ flex: 1; }}
        .rank-name {{ font-size: 16px; font-weight: 500; color: #333; }}
        .rank-detail {{ font-size: 12px; color: #888; margin-top: 2px; }}
        .rank-count {{ font-size: 18px; font-weight: bold; color: #667eea; }}
        .footer {{ text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; font-size: 12px; color: #aaa; }}
        .empty {{ text-align: center; padding: 40px; color: #888; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
        </div>
        <ul class="rank-list">{items_html}</ul>
        <div class="footer">CathayBot Statistics · {time_str}</div>
    </div>
</body>
</html>'''


def _build_user_stat_html(title: str, subtitle: str, items: list[dict]) -> str:
    """构建用户统计 HTML"""
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    items_html = ""
    for item in items:
        highlight_class = "highlight" if item["name"] == "总发言" else ""
        items_html += f'''
        <div class="stat-card {highlight_class}">
            <div class="stat-label">{item["name"]}</div>
            <div class="stat-value">{item["count"]}</div>
        </div>
        '''

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-width: 400px; }}
        .container {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 2px solid #f0f0f0; }}
        .header h1 {{ font-size: 24px; color: #333; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 14px; color: #888; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
        .stat-card {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; padding: 16px; text-align: center; transition: transform 0.2s; }}
        .stat-card:hover {{ transform: translateY(-2px); }}
        .stat-card.highlight {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; grid-column: span 2; }}
        .stat-label {{ font-size: 14px; color: #666; margin-bottom: 8px; }}
        .stat-card.highlight .stat-label {{ color: rgba(255,255,255,0.9); }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #667eea; }}
        .stat-card.highlight .stat-value {{ color: white; font-size: 32px; }}
        .footer {{ text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; font-size: 12px; color: #aaa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
        </div>
        <div class="stats-grid">{items_html}</div>
        <div class="footer">CathayBot Statistics · {time_str}</div>
    </div>
</body>
</html>'''


def _build_plugin_stat_html(title: str, subtitle: str, items: list[dict]) -> str:
    """构建插件统计 HTML"""
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    items_html = ""
    if items:
        for item in items:
            items_html += f'''
            <li class="plugin-item">
                <div class="plugin-icon">🔌</div>
                <div class="plugin-info">
                    <div class="plugin-name">{item["name"]}</div>
                </div>
                <div>
                    <span class="plugin-count">{item["count"]}</span>
                    <span class="plugin-count-label">次调用</span>
                </div>
            </li>
            '''
    else:
        items_html = '<div class="empty">暂无数据</div>'

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; min-width: 400px; }}
        .container {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 2px solid #f0f0f0; }}
        .header h1 {{ font-size: 24px; color: #333; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 14px; color: #888; }}
        .plugin-list {{ list-style: none; }}
        .plugin-item {{ display: flex; align-items: center; padding: 14px 16px; margin-bottom: 10px; background: #f8f9fa; border-radius: 12px; border-left: 4px solid #11998e; transition: all 0.2s; }}
        .plugin-item:hover {{ transform: translateX(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .plugin-icon {{ width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 12px; }}
        .plugin-info {{ flex: 1; }}
        .plugin-name {{ font-size: 16px; font-weight: 500; color: #333; }}
        .plugin-count {{ font-size: 20px; font-weight: bold; color: #11998e; }}
        .plugin-count-label {{ font-size: 12px; color: #888; margin-left: 4px; }}
        .footer {{ text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; font-size: 12px; color: #aaa; }}
        .empty {{ text-align: center; padding: 40px; color: #888; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
        </div>
        <ul class="plugin-list">{items_html}</ul>
        <div class="footer">CathayBot Statistics · {time_str}</div>
    </div>
</body>
</html>'''


def format_text_stat(title: str, subtitle: str, items: list[dict], stat_type: str = "rank") -> str:
    """格式化文字统计

    Args:
        title: 标题
        subtitle: 副标题
        items: 数据项列表
        stat_type: 统计类型 (rank/user/plugin)
    """
    lines = [f"📊 {title}", f"📅 {subtitle}", ""]

    if not items:
        lines.append("暂无数据")
    else:
        if stat_type == "user":
            # 用户统计：显示各项指标
            for item in items:
                lines.append(f"{item['name']}: {item['count']}")
        elif stat_type == "plugin":
            # 插件统计：显示插件名和调用次数
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item['name']}: {item['count']} 次")
        else:
            # 排行榜：显示排名、名称、数量
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
    stat_type: str = "rank",
):
    """发送统计结果

    Args:
        matcher: 匹配器
        title: 标题
        subtitle: 副标题
        items: 数据项列表
        raw_mode: 是否使用文本模式
        stat_type: 统计类型 (rank/user/plugin)
    """
    if raw_mode or plugin_config.default_output == "text":
        await matcher.finish(format_text_stat(title, subtitle, items, stat_type))
    else:
        img = await render_image(title, subtitle, items, stat_type)
        if img:
            await matcher.finish(MessageSegment.image(img))
        else:
            await matcher.finish(format_text_stat(title, subtitle, items, stat_type))


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
    sub_cmd = parts[0] if parts else "all"

    if sub_cmd in ("today", "今日", "今天"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        stats = await StatQuery.get_group_stats_today(group_id, plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        await send_stat(matcher, "今日发言排行", now.strftime("%Y-%m-%d"), items, raw_mode, "rank")

    elif sub_cmd in ("week", "本周", "周"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        stats = await StatQuery.get_group_stats_week(group_id, plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        from datetime import timedelta
        start_date = (now - timedelta(days=now.weekday())).strftime("%m-%d")
        await send_stat(
            matcher,
            "本周发言排行",
            f"{start_date} ~ {now.strftime('%m-%d')}",
            items,
            raw_mode,
            "rank",
        )

    elif sub_cmd in ("month", "本月", "月"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        stats = await StatQuery.get_group_stats_month(group_id, plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        await send_stat(matcher, "本月发言排行", now.strftime("%Y年%m月"), items, raw_mode, "rank")

    elif sub_cmd in ("all", "全部", "总"):
        if not group_id:
            await matcher.finish("请在群聊中使用此命令")

        stats = await StatQuery.get_group_stats_all(group_id, plugin_config.top_limit)

        items = []
        for user_id, count in stats:
            try:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
                name = info.get("card") or info.get("nickname", user_id)
            except Exception:
                name = user_id
            items.append({"name": name, "count": count, "detail": f"QQ: {user_id}"})

        await send_stat(matcher, "总发言排行", "全部时间", items, raw_mode, "rank")

    elif sub_cmd in ("plugin", "插件"):
        stats = await StatQuery.get_plugin_stats(plugin_config.top_limit)
        items = [{"name": name, "count": count} for name, count in stats]
        await send_stat(matcher, "插件调用排行", "近30天", items, raw_mode, "plugin")

    elif sub_cmd in ("user", "用户"):
        # 获取 @ 的用户
        target_user = None
        for seg in args:
            if seg.type == "at":
                target_user = str(seg.data.get("qq"))
                break

        if not target_user:
            target_user = str(event.user_id)

        # 从查询模块获取用户统计
        user_stats = await StatQuery.get_user_stats(target_user, group_id)

        try:
            if group_id:
                info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(target_user))
                name = info.get("card") or info.get("nickname", target_user)
            else:
                info = await bot.get_stranger_info(user_id=int(target_user))
                name = info.get("nickname", target_user)
        except Exception:
            name = target_user

        items = [
            {"name": "今日发言", "count": user_stats["today"]},
            {"name": "本周发言", "count": user_stats["week"]},
            {"name": "本月发言", "count": user_stats["month"]},
            {"name": "总发言", "count": user_stats["total"]},
            {"name": "近7天命令", "count": user_stats["cmd_week"]},
        ]

        location = f"本群 (QQ: {target_user})" if group_id else f"QQ: {target_user}"
        await send_stat(matcher, f"{name} 的统计", location, items, raw_mode, "user")

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


# ==================== 初始化同步任务 ====================

# 初始化同步任务
init_sync_task()

