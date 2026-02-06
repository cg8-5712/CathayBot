"""
Bilibili 插件 - 自动识别 B 站视频链接并生成卡片
"""

from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.plugin import PluginMetadata

from .bilibili import extract_bvid, fetch_video_info, render_video_card

__plugin_meta__ = PluginMetadata(
    name="Bilibili",
    description="自动识别 B 站视频链接并生成卡片",
    usage="""
自动识别群聊中的 B 站视频链接:
- bilibili.com/video/BV...
- b23.tv/BV...

识别后自动返回视频卡片图片
    """.strip(),
    type="application",
    extra={
        "author": "cg8-5712",
        "version": "1.0.0",
        "category": "娱乐",
    },
)

video_card = on_message(priority=99, block=False)


@video_card.handle()
async def handle_bilibili_video(event: MessageEvent):
    """处理 B 站视频链接"""
    url = str(event.get_message())
    bvid = extract_bvid(url)
    if not bvid:
        return  # 非 B 站视频链接，放行

    try:
        video_data = await fetch_video_info(bvid)
    except Exception as e:
        await video_card.finish(f"❌ 视频信息获取失败: {e}")

    pic = await render_video_card(video_data)
    if pic:
        await video_card.finish(MessageSegment.image(pic))
    else:
        await video_card.finish("❌ 生成视频卡片失败")