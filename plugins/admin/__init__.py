"""
Admin 插件 - 管理员命令

提供机器人状态查看、插件管理、广播等管理功能。
"""

import asyncio
import platform
import sys
from datetime import datetime

import nonebot
from nonebot import get_driver, get_loaded_plugins, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.plugin import PluginMetadata

from .config import Config
from .templates import STATUS_TEMPLATE, PLUGIN_LIST_TEMPLATE

__plugin_meta__ = PluginMetadata(
    name="管理",
    description="管理员命令：状态查看、插件管理、广播等",
    usage="""
/admin status [--raw] - 机器人状态
/admin plugins [--raw] - 插件列表
/admin reload <插件名> - 重载插件
/admin broadcast <消息> - 群发消息
/admin echo <消息> - 回显消息 (测试用)
/admin mute @用户 [时长] - 禁言用户 (默认10分钟，支持: 30s/10m/1h/1d)
/admin unmute @用户 - 解除禁言
/admin kick @用户 [拒绝再次申请] - 踢出群成员

--raw 参数输出纯文字，否则输出图片
    """.strip(),
    type="application",
    config=Config,
    extra={
        "author": "cg8-5712",
        "version": "1.0.0",
        "category": "管理",
    },
)

# 加载配置
plugin_config = Config.load("admin")

# 启动时间
START_TIME = datetime.now()

# 注册命令 (超级管理员或群主可用)
admin_cmd = on_command("admin", permission=SUPERUSER | GROUP_OWNER, priority=1, block=True)


def parse_raw_flag(args: str) -> tuple[str, bool]:
    """解析 --raw 参数"""
    raw_mode = "--raw" in args
    clean_args = args.replace("--raw", "").strip()
    return clean_args, raw_mode


def format_uptime(start: datetime) -> str:
    """格式化运行时间"""
    delta = datetime.now() - start
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days}天{hours}时"
    elif hours > 0:
        return f"{hours}时{minutes}分"
    else:
        return f"{minutes}分钟"


async def render_image(template: str, **kwargs) -> bytes | None:
    """渲染图片"""
    try:
        from nonebot_plugin_htmlrender import html_to_pic
        from jinja2 import Template

        tmpl = Template(template)
        html = tmpl.render(time=datetime.now().strftime("%Y-%m-%d %H:%M"), **kwargs)
        return await html_to_pic(html=html, viewport={"width": 450, "height": 100})
    except ImportError:
        return None
    except Exception:
        return None


@admin_cmd.handle()
async def handle_admin(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    """处理管理命令"""
    arg_text = args.extract_plain_text().strip()

    if not arg_text:
        await matcher.finish("请指定子命令，使用 /help 管理 查看用法")

    arg, raw_mode = parse_raw_flag(arg_text)
    parts = arg.split(maxsplit=1)
    sub_cmd = parts[0].lower()
    sub_args = parts[1] if len(parts) > 1 else ""

    # 检查是否为超级管理员
    driver = get_driver()
    superusers = driver.config.superusers
    is_superuser = str(event.user_id) in superusers

    # 某些命令仅超级管理员可用
    superuser_only_cmds = ["reload", "broadcast"]
    if sub_cmd in superuser_only_cmds and not is_superuser:
        await matcher.finish(f"❌ 命令 {sub_cmd} 仅超级管理员可用")

    if sub_cmd == "status":
        await handle_status(bot, matcher, raw_mode)

    elif sub_cmd == "plugins":
        await handle_plugins(matcher, raw_mode)

    elif sub_cmd == "reload":
        await handle_reload(matcher, sub_args)

    elif sub_cmd == "broadcast":
        await handle_broadcast(bot, matcher, sub_args)

    elif sub_cmd == "echo":
        await matcher.finish(sub_args or "请输入要回显的内容")

    elif sub_cmd == "mute":
        await handle_mute(bot, event, matcher, sub_args, args)

    elif sub_cmd == "unmute":
        await handle_unmute(bot, event, matcher, sub_args, args)

    elif sub_cmd == "kick":
        await handle_kick(bot, event, matcher, sub_args, args)

    else:
        await matcher.finish(f"未知的子命令: {sub_cmd}")


async def handle_status(bot: Bot, matcher: Matcher, raw_mode: bool):
    """处理状态查询"""
    # 获取基本信息
    try:
        bot_info = await bot.get_login_info()
        bot_name = bot_info.get("nickname", "CathayBot")
        bot_id = bot_info.get("user_id", "未知")
    except Exception:
        bot_name = "CathayBot"
        bot_id = "未知"

    # 获取群和好友数量
    try:
        groups = await bot.get_group_list()
        group_count = len(groups)
    except Exception:
        group_count = 0

    try:
        friends = await bot.get_friend_list()
        friend_count = len(friends)
    except Exception:
        friend_count = 0

    # 插件数量
    plugin_count = len(list(get_loaded_plugins()))

    # 运行时间
    uptime = format_uptime(START_TIME)

    # NoneBot 版本
    nonebot_version = nonebot.__version__

    # Python 版本
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # 系统平台
    plat = platform.system()

    if raw_mode or plugin_config.default_output == "text":
        lines = [
            f"🤖 {bot_name} 状态",
            "",
            f"📊 群聊: {group_count} | 好友: {friend_count}",
            f"📦 插件: {plugin_count} | 运行: {uptime}",
            "",
            f"QQ: {bot_id}",
            f"NoneBot: {nonebot_version}",
            f"Python: {python_version}",
            f"系统: {plat}",
        ]
        await matcher.finish("\n".join(lines))
    else:
        img = await render_image(
            STATUS_TEMPLATE,
            bot_name=bot_name,
            bot_id=bot_id,
            groups=group_count,
            friends=friend_count,
            plugins=plugin_count,
            uptime=uptime,
            nonebot_version=nonebot_version,
            python_version=python_version,
            platform=plat,
        )
        if img:
            await matcher.finish(MessageSegment.image(img))
        else:
            # 回退到文字
            lines = [
                f"🤖 {bot_name} 状态",
                "",
                f"📊 群聊: {group_count} | 好友: {friend_count}",
                f"📦 插件: {plugin_count} | 运行: {uptime}",
            ]
            await matcher.finish("\n".join(lines))


async def handle_plugins(matcher: Matcher, raw_mode: bool):
    """处理插件列表"""
    plugins_info = []

    for plugin in get_loaded_plugins():
        meta = plugin.metadata
        if meta:
            plugins_info.append({
                "name": meta.name,
                "description": meta.description or "暂无描述",
                "version": meta.extra.get("version", "1.0.0"),
                "enabled": True,
            })
        else:
            plugins_info.append({
                "name": plugin.name,
                "description": "无元信息",
                "version": "?",
                "enabled": True,
            })

    # 按名称排序
    plugins_info.sort(key=lambda x: x["name"])

    if raw_mode or plugin_config.default_output == "text":
        lines = ["📦 插件列表", ""]
        for p in plugins_info:
            status = "✅" if p["enabled"] else "❌"
            lines.append(f"{status} {p['name']} (v{p['version']})")
            lines.append(f"   {p['description']}")
        lines.append("")
        lines.append(f"共 {len(plugins_info)} 个插件")
        await matcher.finish("\n".join(lines))
    else:
        img = await render_image(PLUGIN_LIST_TEMPLATE, plugins=plugins_info)
        if img:
            await matcher.finish(MessageSegment.image(img))
        else:
            lines = ["📦 插件列表", ""]
            for p in plugins_info:
                lines.append(f"• {p['name']} - {p['description']}")
            await matcher.finish("\n".join(lines))


async def handle_reload(matcher: Matcher, plugin_name: str):
    """处理插件重载"""
    if not plugin_config.allow_reload:
        await matcher.finish("❌ 插件重载功能已禁用")

    if not plugin_name:
        await matcher.finish("请指定要重载的插件名")

    # 查找插件
    target_plugin = None
    for plugin in get_loaded_plugins():
        if plugin.name == plugin_name:
            target_plugin = plugin
            break
        if plugin.metadata and plugin.metadata.name == plugin_name:
            target_plugin = plugin
            break

    if not target_plugin:
        await matcher.finish(f"❌ 未找到插件: {plugin_name}")

    # NoneBot2 目前不支持真正的热重载，这里只是提示
    await matcher.finish(
        f"⚠️ NoneBot2 暂不支持运行时热重载插件\n"
        f"请重启机器人以重新加载 {target_plugin.name}"
    )


async def handle_broadcast(bot: Bot, matcher: Matcher, message: str):
    """处理广播消息"""
    if not plugin_config.allow_broadcast:
        await matcher.finish("❌ 广播功能已禁用")

    if not message:
        await matcher.finish("请输入要广播的消息")

    try:
        groups = await bot.get_group_list()
    except Exception as e:
        await matcher.finish(f"❌ 获取群列表失败: {e}")

    if not groups:
        await matcher.finish("❌ 没有可广播的群")

    await matcher.send(f"📢 开始广播到 {len(groups)} 个群...")

    success = 0
    failed = 0

    for group in groups:
        group_id = group["group_id"]
        try:
            await bot.send_group_msg(group_id=group_id, message=message)
            success += 1
        except Exception:
            failed += 1

        # 间隔发送，防止风控
        await asyncio.sleep(plugin_config.broadcast_interval)

    await matcher.finish(f"📢 广播完成\n✅ 成功: {success}\n❌ 失败: {failed}")


def parse_duration(duration_str: str) -> int:
    """解析时长字符串，返回秒数

    支持格式:
    - 纯数字: 默认为分钟
    - 30s: 30秒
    - 10m: 10分钟
    - 1h: 1小时
    - 1d: 1天
    """
    duration_str = duration_str.strip().lower()

    if not duration_str:
        return 600  # 默认10分钟

    # 纯数字，默认为分钟
    if duration_str.isdigit():
        return int(duration_str) * 60

    # 带单位
    if duration_str[-1] in ['s', 'm', 'h', 'd']:
        try:
            value = int(duration_str[:-1])
            unit = duration_str[-1]

            if unit == 's':
                return value
            elif unit == 'm':
                return value * 60
            elif unit == 'h':
                return value * 3600
            elif unit == 'd':
                return value * 86400
        except ValueError:
            return 600  # 解析失败，返回默认值

    return 600  # 默认10分钟


def format_duration(seconds: int) -> str:
    """格式化时长显示"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分钟"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟" if minutes > 0 else f"{hours}小时"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}天{hours}小时" if hours > 0 else f"{days}天"


async def handle_mute(bot: Bot, event: MessageEvent, matcher: Matcher, args: str, cmd_args: Message):
    """处理禁言命令"""
    from nonebot.exception import FinishedException

    # 检查是否为群聊
    if not isinstance(event, GroupMessageEvent):
        await matcher.finish("❌ 禁言命令只能在群聊中使用")

    # 解析参数
    parts = args.split()

    # 获取目标用户ID
    target_id = None
    duration_str = ""

    # 检查命令参数中是否有 at 消息段
    for seg in cmd_args:
        if seg.type == "at":
            target_id = seg.data.get("qq")
            break

    # 如果没有 at，尝试从参数中解析 QQ 号
    if not target_id:
        if parts and parts[0].isdigit():
            target_id = parts[0]
            duration_str = parts[1] if len(parts) > 1 else ""
        else:
            await matcher.finish("❌ 请使用 @用户 或输入 QQ号")
    else:
        # 有 at 的情况，时长参数在纯文本部分
        duration_str = parts[0] if parts else ""

    # 解析时长
    duration = parse_duration(duration_str)

    # 检查是否禁言自己或机器人
    bot_info = await bot.get_login_info()
    bot_id = str(bot_info.get("user_id"))

    if str(target_id) == bot_id:
        await matcher.finish("❌ 不能禁言机器人自己")

    if str(target_id) == str(event.user_id):
        await matcher.finish("❌ 不能禁言自己")

    # 执行禁言
    try:
        await bot.set_group_ban(
            group_id=event.group_id,
            user_id=int(target_id),
            duration=duration
        )
    except FinishedException:
        raise
    except Exception as e:
        await matcher.finish(f"❌ 禁言失败: {e}")


async def handle_unmute(bot: Bot, event: MessageEvent, matcher: Matcher, args: str, cmd_args: Message):
    """处理解除禁言命令"""
    from nonebot.exception import FinishedException

    # 检查是否为群聊
    if not isinstance(event, GroupMessageEvent):
        await matcher.finish("❌ 解除禁言命令只能在群聊中使用")

    # 获取目标用户ID
    target_id = None

    # 检查命令参数中是否有 at 消息段
    for seg in cmd_args:
        if seg.type == "at":
            target_id = seg.data.get("qq")
            break

    # 如果没有 at，尝试从参数中解析 QQ 号
    if not target_id:
        parts = args.split()
        if parts and parts[0].isdigit():
            target_id = parts[0]
        else:
            await matcher.finish("❌ 请使用 @用户 或输入 QQ号")

    # 执行解除禁言 (duration=0)
    try:
        await bot.set_group_ban(
            group_id=event.group_id,
            user_id=int(target_id),
            duration=0
        )
    except FinishedException:
        raise
    except Exception as e:
        await matcher.finish(f"❌ 解除禁言失败: {e}")


async def handle_kick(bot: Bot, event: MessageEvent, matcher: Matcher, args: str, cmd_args: Message):
    """处理踢人命令"""
    from nonebot.exception import FinishedException

    # 检查是否为群聊
    if not isinstance(event, GroupMessageEvent):
        await matcher.finish("❌ 踢人命令只能在群聊中使用")

    # 解析参数
    parts = args.split()

    # 获取目标用户ID
    target_id = None
    reject_add_request = False

    # 检查命令参数中是否有 at 消息段
    for seg in cmd_args:
        if seg.type == "at":
            target_id = seg.data.get("qq")
            break

    # 如果没有 at，尝试从参数中解析 QQ 号
    if not target_id:
        if parts and parts[0].isdigit():
            target_id = parts[0]
            # 检查是否有拒绝再次申请参数
            if len(parts) > 1 and parts[1].lower() in ['true', '1', 'yes', '拒绝']:
                reject_add_request = True
        else:
            await matcher.finish("❌ 请使用 @用户 或输入 QQ号")
    else:
        # 检查是否有拒绝再次申请参数
        if parts and parts[0].lower() in ['true', '1', 'yes', '拒绝']:
            reject_add_request = True

    # 检查是否踢自己或机器人
    bot_info = await bot.get_login_info()
    bot_id = str(bot_info.get("user_id"))

    if str(target_id) == bot_id:
        await matcher.finish("❌ 不能踢出机器人自己")

    if str(target_id) == str(event.user_id):
        await matcher.finish("❌ 不能踢出自己")

    # 执行踢人
    try:
        await bot.set_group_kick(
            group_id=event.group_id,
            user_id=int(target_id),
            reject_add_request=reject_add_request
        )
    except FinishedException:
        raise
    except Exception as e:
        await matcher.finish(f"❌ 踢人失败: {e}")
