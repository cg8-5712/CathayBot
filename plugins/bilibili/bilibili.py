"""
Bilibili API 调用和卡片渲染
"""

import re

import httpx
from nonebot import logger

from .templates import VIDEO_CARD_TEMPLATE


def extract_bvid(url: str) -> str | None:
    """从 URL 中提取 BV 号"""
    pattern = r"(?:bilibili\.com\/video\/|b23\.tv\/)(BV\w{10})"
    match = re.search(pattern, url)
    return match.group(1) if match else None


async def fetch_video_info(bvid: str) -> dict:
    """获取视频信息"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.bilibili.com/",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise ValueError(f"请求失败: {resp.status_code}")
        json_data = resp.json()
        if json_data.get("code") != 0:
            raise ValueError(f"B站API错误: {json_data.get('message')}")
        logger.debug(f"获取视频信息成功: {bvid}")
        return json_data["data"]


async def render_video_card(data: dict) -> bytes | None:
    """渲染视频卡片"""
    try:
        from nonebot_plugin_htmlrender import html_to_pic
        from jinja2 import Template

        # 处理统计数据
        stat = data.get("stat", {})

        # 处理视频描述
        desc = data.get("desc", "")
        if len(desc) > 100:
            desc = desc[:100] + "..."

        # 渲染模板
        tmpl = Template(VIDEO_CARD_TEMPLATE)
        html = tmpl.render(
            title=data.get("title", "无标题"),
            cover=data.get("pic", ""),
            duration=format_duration(data.get("duration", 0)),
            desc=desc,
            tname=data.get("tname", "未知分区"),
            stat={
                "view": format_stat(stat.get("view", 0)),
                "danmaku": format_stat(stat.get("danmaku", 0)),
                "reply": format_stat(stat.get("reply", 0)),
                "favorite": format_stat(stat.get("favorite", stat.get("fav", 0))),
                "coin": format_stat(stat.get("coin", 0)),
                "share": format_stat(stat.get("share", 0)),
                "like": format_stat(stat.get("like", 0)),
            },
            owner={
                "face": data.get("owner", {}).get("face", ""),
                "name": data.get("owner", {}).get("name", "未知UP主"),
            },
        )

        return await html_to_pic(html=html, viewport={"width": 520, "height": 100})
    except ImportError:
        logger.error("未安装 nonebot_plugin_htmlrender")
        return None
    except Exception as e:
        logger.error(f"渲染视频卡片失败: {e}")
        return None


def format_duration(seconds: int) -> str:
    """格式化视频时长"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_stat(num: int) -> str:
    """格式化统计数据，过万时显示为1.2万"""
    if num >= 10000:
        return f"{num / 10000:.1f}万"
    return str(num)