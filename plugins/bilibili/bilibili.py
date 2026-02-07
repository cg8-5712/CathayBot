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
    logger.debug(f"[DEBUG] 请求 B 站视频信息:")
    logger.debug(f"  - BV号: {bvid}")
    logger.debug(f"  - API URL: {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        logger.debug(f"[DEBUG] B站API响应状态: {resp.status_code}")

        if resp.status_code != 200:
            logger.error(f"[DEBUG] 请求失败，响应内容: {resp.text[:500]}")
            raise ValueError(f"请求失败: {resp.status_code}")

        json_data = resp.json()
        logger.debug(f"[DEBUG] API 返回 code: {json_data.get('code')}")

        if json_data.get("code") != 0:
            logger.error(f"[DEBUG] B站API错误: {json_data}")
            raise ValueError(f"B站API错误: {json_data.get('message')}")

        data = json_data["data"]
        logger.debug(f"[DEBUG] 视频信息:")
        logger.debug(f"  - 标题: {data.get('title')}")
        logger.debug(f"  - 封面URL: {data.get('pic')}")
        logger.debug(f"  - UP主: {data.get('owner', {}).get('name')}")
        logger.debug(f"  - UP主头像: {data.get('owner', {}).get('face')}")

        return data


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

        cover_url = data.get("pic", "")
        owner_face = data.get("owner", {}).get("face", "")

        # 强制使用 HTTPS（避免 Chromium 阻止 HTTP 请求）
        if cover_url.startswith("http://"):
            cover_url = cover_url.replace("http://", "https://", 1)
            logger.debug(f"[DEBUG] 封面URL转换为HTTPS: {cover_url}")
        if owner_face.startswith("http://"):
            owner_face = owner_face.replace("http://", "https://", 1)
            logger.debug(f"[DEBUG] 头像URL转换为HTTPS: {owner_face}")

        logger.debug(f"[DEBUG] 开始渲染视频卡片:")
        logger.debug(f"  - 封面URL: {cover_url}")
        logger.debug(f"  - UP主头像URL: {owner_face}")

        # 测试图片URL是否可访问
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 测试封面
                if cover_url:
                    logger.debug(f"[DEBUG] 测试封面URL可访问性...")
                    cover_resp = await client.head(cover_url, follow_redirects=True)
                    logger.debug(f"  - 封面响应状态: {cover_resp.status_code}")
                    logger.debug(f"  - 封面Content-Type: {cover_resp.headers.get('content-type')}")
                    if cover_resp.status_code != 200:
                        logger.warning(f"[DEBUG] 封面URL无法访问: {cover_url}")

                # 测试UP主头像
                if owner_face:
                    logger.debug(f"[DEBUG] 测试UP主头像URL可访问性...")
                    face_resp = await client.head(owner_face, follow_redirects=True)
                    logger.debug(f"  - 头像响应状态: {face_resp.status_code}")
                    logger.debug(f"  - 头像Content-Type: {face_resp.headers.get('content-type')}")
                    if face_resp.status_code != 200:
                        logger.warning(f"[DEBUG] 头像URL无法访问: {owner_face}")
        except Exception as test_error:
            logger.warning(f"[DEBUG] 图片URL测试失败: {test_error}")

        # 渲染模板
        tmpl = Template(VIDEO_CARD_TEMPLATE)
        html = tmpl.render(
            title=data.get("title", "无标题"),
            cover=cover_url,
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
                "face": owner_face,
                "name": data.get("owner", {}).get("name", "未知UP主"),
            },
        )

        logger.debug(f"[DEBUG] HTML模板渲染完成，长度: {len(html)}")
        logger.debug(f"[DEBUG] HTML内容预览:\n{html[:500]}...")

        logger.debug(f"[DEBUG] 开始调用 html_to_pic 转换为图片...")
        pic_bytes = await html_to_pic(html=html, viewport={"width": 520, "height": 100})

        if pic_bytes:
            logger.debug(f"[DEBUG] 图片生成成功，大小: {len(pic_bytes)} bytes")
        else:
            logger.error(f"[DEBUG] html_to_pic 返回 None")

        return pic_bytes
    except ImportError as e:
        logger.error(f"未安装 nonebot_plugin_htmlrender: {e}")
        return None
    except Exception as e:
        logger.error(f"渲染视频卡片失败: {e}")
        import traceback
        logger.error(f"[DEBUG] 堆栈跟踪:\n{traceback.format_exc()}")
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