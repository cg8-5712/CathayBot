"""
Whois 插件 - 域名查询

提供域名 whois 信息查询功能。
"""

import asyncio
import re
import socket
from datetime import datetime
from typing import Optional

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

from .config import Config
from .template import WHOIS_TEMPLATE

__plugin_meta__ = PluginMetadata(
    name="域名查询",
    description="查询域名的 whois 信息、DNS 解析和 IP 地理位置",
    usage="""
/whois <域名> [--raw] - 查询域名信息
示例:
  /whois google.com
  /whois baidu.com --raw

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
plugin_config = Config.load("whois")

# 注册命令
whois_cmd = on_command("whois", priority=5, block=True)


def is_valid_domain(domain: str) -> bool:
    """验证域名格式"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def parse_raw_flag(args: str) -> tuple[str, bool]:
    """解析 --raw 参数"""
    raw_mode = "--raw" in args
    clean_args = args.replace("--raw", "").strip()
    return clean_args, raw_mode


async def resolve_domain(domain: str) -> list[str]:
    """解析域名的 IP 地址"""
    try:
        # 使用 socket 进行 DNS 解析
        result = await asyncio.to_thread(socket.getaddrinfo, domain, None)
        # 提取 IPv4 地址
        ips = list(set([addr[4][0] for addr in result if addr[0] == socket.AF_INET]))
        return ips[:5]  # 最多返回5个IP
    except Exception:
        return []


async def query_ip_location(ip: str) -> Optional[dict]:
    """查询 IP 地理位置信息"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 使用 ip-api.com 免费 API
            response = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"lang": "zh-CN", "fields": "status,country,regionName,city,isp,org,as"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "未知"),
                        "region": data.get("regionName", "未知"),
                        "city": data.get("city", "未知"),
                        "isp": data.get("isp", "未知"),
                        "org": data.get("org", "未知"),
                        "as": data.get("as", "未知"),
                    }
    except Exception:
        pass
    return None


async def query_whois(domain: str, timeout: int = 10) -> Optional[dict]:
    """查询域名 whois 信息，返回结构化数据"""
    try:
        import whois

        result = await asyncio.wait_for(
            asyncio.to_thread(whois.whois, domain),
            timeout=timeout
        )

        if not result:
            return None

        # 提取并格式化数据
        data = {}

        # 域名
        data["domain"] = domain.upper()

        # 状态
        if hasattr(result, 'status') and result.status:
            status = result.status
            if isinstance(status, list):
                # 提取第一个状态，去除 URL 部分
                status = status[0] if status else "未知"
            # 清理状态文本
            status = status.split()[0] if ' ' in status else status
            data["status"] = status
        else:
            data["status"] = "未知"

        # 注册商
        data["registrar"] = getattr(result, 'registrar', None) or "未知"

        # 注册时间
        if hasattr(result, 'creation_date') and result.creation_date:
            creation = result.creation_date
            if isinstance(creation, list):
                creation = creation[0]
            if isinstance(creation, datetime):
                data["creation_date"] = creation.strftime('%Y-%m-%d %H:%M:%S')
            else:
                data["creation_date"] = str(creation)
        else:
            data["creation_date"] = "未知"

        # 过期时间
        if hasattr(result, 'expiration_date') and result.expiration_date:
            expiration = result.expiration_date
            if isinstance(expiration, list):
                expiration = expiration[0]
            if isinstance(expiration, datetime):
                data["expiration_date"] = expiration.strftime('%Y-%m-%d %H:%M:%S')
                # 计算剩余天数
                # 处理时区问题：如果 expiration 有时区信息，使用 utcnow()；否则使用 now()
                if expiration.tzinfo is not None:
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                else:
                    now = datetime.now()
                days_left = (expiration - now).days
                data["days_left"] = days_left
            else:
                data["expiration_date"] = str(expiration)
                data["days_left"] = None
        else:
            data["expiration_date"] = "未知"
            data["days_left"] = None

        # 更新时间
        if hasattr(result, 'updated_date') and result.updated_date:
            updated = result.updated_date
            if isinstance(updated, list):
                updated = updated[0]
            if isinstance(updated, datetime):
                data["updated_date"] = updated.strftime('%Y-%m-%d %H:%M:%S')
            else:
                data["updated_date"] = str(updated)
        else:
            data["updated_date"] = "未知"

        # DNS 服务器
        if hasattr(result, 'name_servers') and result.name_servers:
            ns_list = result.name_servers
            if isinstance(ns_list, list):
                data["name_servers"] = [ns.lower() for ns in ns_list[:5]]
            else:
                data["name_servers"] = [str(ns_list).lower()]
        else:
            data["name_servers"] = []

        # 组织信息
        data["org"] = getattr(result, 'org', None) or "未知"
        data["country"] = getattr(result, 'country', None) or "未知"

        return data

    except ImportError:
        return {"error": "缺少 python-whois 库，请安装: pip install python-whois"}
    except asyncio.TimeoutError:
        return {"error": "查询超时，请稍后重试"}
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def format_text_output(whois_data: dict, dns_data: list, ip_locations: dict) -> str:
    """格式化文本输出"""
    lines = [f"🌐 域名信息: {whois_data.get('domain', '未知')}", ""]

    if "error" in whois_data:
        return f"❌ {whois_data['error']}"

    # Whois 信息
    lines.append(f"📊 状态: {whois_data.get('status', '未知')}")
    lines.append(f"🏢 注册商: {whois_data.get('registrar', '未知')}")
    lines.append(f"🏛️ 组织: {whois_data.get('org', '未知')}")
    lines.append(f"🌍 国家: {whois_data.get('country', '未知')}")
    lines.append("")
    lines.append(f"📅 注册时间: {whois_data.get('creation_date', '未知')}")
    lines.append(f"⏰ 过期时间: {whois_data.get('expiration_date', '未知')}")

    if whois_data.get('days_left') is not None:
        days = whois_data['days_left']
        if days > 0:
            lines.append(f"⏳ 剩余天数: {days} 天")
        else:
            lines.append(f"⚠️ 已过期 {abs(days)} 天")

    lines.append(f"🔄 更新时间: {whois_data.get('updated_date', '未知')}")

    # DNS 服务器
    if whois_data.get('name_servers'):
        lines.append("")
        lines.append("🖥️ DNS 服务器:")
        for ns in whois_data['name_servers']:
            lines.append(f"  • {ns}")

    # DNS 解析
    if dns_data:
        lines.append("")
        lines.append("🔍 DNS 解析:")
        for ip in dns_data:
            lines.append(f"  • {ip}")
            # IP 地理位置
            if ip in ip_locations:
                loc = ip_locations[ip]
                lines.append(f"    📍 {loc['country']} {loc['region']} {loc['city']}")
                lines.append(f"    🏢 {loc['isp']}")

    return "\n".join(lines)


async def render_image(whois_data: dict, dns_data: list, ip_locations: dict) -> bytes | None:
    """渲染图片"""
    try:
        from nonebot_plugin_htmlrender import html_to_pic
        from jinja2 import Template

        tmpl = Template(WHOIS_TEMPLATE)
        html = tmpl.render(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            whois=whois_data,
            dns=dns_data,
            ip_locations=ip_locations,
        )
        return await html_to_pic(html=html, viewport={"width": 600, "height": 100})
    except ImportError:
        return None
    except Exception:
        return None


@whois_cmd.handle()
async def handle_whois(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    """处理 whois 查询命令"""
    arg_text = args.extract_plain_text().strip()

    if not arg_text:
        await matcher.finish("请输入要查询的域名\n示例: /whois google.com")

    # 解析参数
    domain, raw_mode = parse_raw_flag(arg_text)

    # 移除可能的协议前缀
    domain = re.sub(r'^https?://', '', domain)
    # 移除可能的路径
    domain = domain.split('/')[0]
    # 移除可能的端口
    domain = domain.split(':')[0]

    # 验证域名格式
    if not is_valid_domain(domain):
        await matcher.finish(f"❌ 无效的域名格式: {domain}")

    # 发送查询提示
    # await matcher.send(f"🔍 正在查询域名: {domain}")

    # 并行执行查询
    whois_task = query_whois(domain, timeout=plugin_config.timeout)
    dns_task = resolve_domain(domain)

    whois_data, dns_data = await asyncio.gather(whois_task, dns_task)

    # 查询 IP 地理位置
    ip_locations = {}
    if dns_data:
        location_tasks = [query_ip_location(ip) for ip in dns_data]
        locations = await asyncio.gather(*location_tasks)
        for ip, loc in zip(dns_data, locations):
            if loc:
                ip_locations[ip] = loc

    # 检查是否有错误
    if whois_data and "error" in whois_data:
        await matcher.finish(f"❌ {whois_data['error']}")

    # 输出结果
    if raw_mode or plugin_config.default_output == "text":
        result = format_text_output(whois_data, dns_data, ip_locations)
        if len(result) > plugin_config.max_length:
            result = result[:plugin_config.max_length] + "\n\n... (内容过长，已截断)"
        await matcher.finish(result)
    else:
        img = await render_image(whois_data, dns_data, ip_locations)
        if img:
            await matcher.finish(MessageSegment.image(img))
        else:
            # 回退到文本模式
            result = format_text_output(whois_data, dns_data, ip_locations)
            await matcher.finish(result)
