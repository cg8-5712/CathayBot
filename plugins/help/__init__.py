"""
Help 插件 - 自动帮助生成

自动扫描所有已加载插件，生成帮助信息。
支持图片和文字输出。
"""

from datetime import datetime

from nonebot import get_loaded_plugins, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

from .config import Config
from .templates import HELP_LIST_TEMPLATE, HELP_DETAIL_TEMPLATE, CATEGORY_ICONS

__plugin_meta__ = PluginMetadata(
    name="帮助",
    description="显示所有插件的帮助信息",
    usage="""
/help [--raw] - 显示插件列表
/help <插件名> [--raw] - 显示插件详情

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
plugin_config = Config.load("help")

# 注册命令
help_cmd = on_command("help", aliases={"帮助"}, priority=1, block=True)


def parse_raw_flag(args: str) -> tuple[str, bool]:
    """解析 --raw 参数"""
    raw_mode = "--raw" in args
    clean_args = args.replace("--raw", "").strip()
    return clean_args, raw_mode


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


def get_plugin_list() -> dict[str, list[dict]]:
    """
    获取所有插件列表，按分类整理

    Returns:
        {分类: [{name, description, icon}, ...]}
    """
    categories: dict[str, list[dict]] = {}

    for plugin in get_loaded_plugins():
        meta = plugin.metadata
        if not meta:
            continue

        # 检查是否隐藏
        if meta.extra.get("hidden", False) and not plugin_config.show_hidden:
            continue

        category = meta.extra.get("category", "其他")
        if category not in categories:
            categories[category] = []

        categories[category].append({
            "name": meta.name,
            "description": meta.description or "暂无描述",
            "icon": CATEGORY_ICONS.get(category, "📦"),
        })

    # 按分类名排序
    return dict(sorted(categories.items()))


def get_plugin_detail(name: str) -> dict | None:
    """
    获取插件详细信息

    Args:
        name: 插件名称

    Returns:
        插件详情字典，未找到返回 None
    """
    for plugin in get_loaded_plugins():
        meta = plugin.metadata
        if not meta:
            continue

        if meta.name == name:
            category = meta.extra.get("category", "其他")
            return {
                "name": meta.name,
                "description": meta.description or "暂无描述",
                "usage": meta.usage or "暂无用法说明",
                "version": meta.extra.get("version", "1.0.0"),
                "author": meta.extra.get("author", "未知"),
                "category": category,
                "icon": CATEGORY_ICONS.get(category, "📦"),
            }

    return None


def format_text_list(categories: dict[str, list[dict]]) -> str:
    """格式化文字版插件列表"""
    lines = ["📚 插件列表", ""]

    total = 0
    for category, plugins in categories.items():
        lines.append(f"【{category}】")
        for p in plugins:
            lines.append(f"  • {p['name']} - {p['description']}")
            total += 1
        lines.append("")

    lines.append(f"共 {total} 个插件")
    lines.append("💡 使用 /help <插件名> 查看详情")

    return "\n".join(lines)


def format_text_detail(detail: dict) -> str:
    """格式化文字版插件详情"""
    lines = [
        f"📖 {detail['name']}",
        "",
        f"📝 {detail['description']}",
        "",
        "📋 用法:",
        detail['usage'],
        "",
        f"版本: {detail['version']}",
        f"作者: {detail['author']}",
        f"分类: {detail['category']}",
    ]
    return "\n".join(lines)


@help_cmd.handle()
async def handle_help(matcher: Matcher, args: Message = CommandArg()):
    """处理帮助命令"""
    arg_text = args.extract_plain_text().strip()
    arg, raw_mode = parse_raw_flag(arg_text)

    if not arg:
        # 显示插件列表
        categories = get_plugin_list()

        if not categories:
            await matcher.finish("暂无可用插件")

        total = sum(len(plugins) for plugins in categories.values())

        if raw_mode or plugin_config.default_output == "text":
            await matcher.finish(format_text_list(categories))
        else:
            img = await render_image(
                HELP_LIST_TEMPLATE,
                categories=categories,
                total=total,
            )
            if img:
                await matcher.finish(MessageSegment.image(img))
            else:
                # 回退到文字
                await matcher.finish(format_text_list(categories))
    else:
        # 显示插件详情
        detail = get_plugin_detail(arg)

        if not detail:
            await matcher.finish(f"❌ 未找到插件: {arg}")

        if raw_mode or plugin_config.default_output == "text":
            await matcher.finish(format_text_detail(detail))
        else:
            img = await render_image(
                HELP_DETAIL_TEMPLATE,
                **detail,
            )
            if img:
                await matcher.finish(MessageSegment.image(img))
            else:
                await matcher.finish(format_text_detail(detail))
