"""
GitHub 插件 - 自动识别 GitHub 链接并生成卡片

监听群聊消息，识别 GitHub 用户/仓库链接，返回精美卡片图片。
"""

import re
from datetime import datetime
from dataclasses import asdict

from nonebot import get_driver, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.plugin import PluginMetadata

from .config import Config
from .api import github_api, GitHubUser, GitHubRepo
from .templates import USER_CARD_TEMPLATE, REPO_CARD_TEMPLATE

__plugin_meta__ = PluginMetadata(
    name="GitHub",
    description="自动识别 GitHub 链接并生成卡片",
    usage="""
自动识别群聊中的 GitHub 链接:
- 用户链接: https://github.com/username
- 仓库链接: https://github.com/owner/repo

识别后自动返回精美卡片图片
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
plugin_config = Config.load("github")

# 设置 API Token
if plugin_config.token:
    github_api.token = plugin_config.token

driver = get_driver()

# GitHub 链接正则
# 简单匹配 github.com 后的路径，然后用 / 切分
GITHUB_URL_PATTERN = re.compile(
    r"https?://github\.com/([a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)?)"
)


async def render_card(template: str, **kwargs) -> bytes | None:
    """渲染卡片图片"""
    try:
        from nonebot_plugin_htmlrender import html_to_pic
        from jinja2 import Template

        tmpl = Template(template)
        html = tmpl.render(**kwargs)
        return await html_to_pic(html=html, viewport={"width": 520, "height": 100})
    except ImportError:
        return None
    except Exception as e:
        from nonebot import logger
        logger.error(f"渲染 GitHub 卡片失败: {e}")
        return None


def format_user_text(user: GitHubUser) -> str:
    """格式化用户文字信息"""
    lines = [
        f"👤 {user.name or user.login} (@{user.login})",
        "",
    ]
    if user.bio:
        lines.append(f"📝 {user.bio}")
        lines.append("")

    lines.extend([
        f"⭐ Stars: {user.total_stars}  |  🍴 Forks: {user.total_forks}  |  👥 Followers: {user.followers}",
        f"📦 Repos: {user.public_repos}  |  💻 Commits: {user.total_commits}  |  🔀 PRs: {user.total_prs}",
    ])

    if user.top_languages:
        lines.append(f"🔤 Languages: {', '.join(user.top_languages)}")

    if user.top_repos:
        lines.append("")
        lines.append("🔥 Top Repos:")
        for repo in user.top_repos:
            lines.append(f"  • {repo['name']} (⭐{repo['stars']})")

    return "\n".join(lines)


def format_repo_text(repo: GitHubRepo) -> str:
    """格式化仓库文字信息"""
    lines = [
        f"📦 {repo.full_name}",
        "",
    ]
    if repo.description:
        lines.append(f"📝 {repo.description}")
        lines.append("")

    lines.extend([
        f"⭐ {repo.stargazers_count}  |  🍴 {repo.forks_count}  |  👀 {repo.watchers_count}  |  🐛 {repo.open_issues_count}",
    ])

    if repo.language:
        lines.append(f"💻 Language: {repo.language}")

    if repo.license_name:
        lines.append(f"📄 License: {repo.license_name}")

    if repo.topics:
        lines.append(f"🏷️ Topics: {', '.join(repo.topics[:5])}")

    return "\n".join(lines)


# 消息监听器
github_matcher = on_message(priority=50, block=False)


@github_matcher.handle()
async def handle_github_link(bot: Bot, event: MessageEvent):
    """处理 GitHub 链接"""
    if not plugin_config.auto_detect:
        return

    # 只处理群聊消息
    if not isinstance(event, GroupMessageEvent):
        return

    msg_text = event.get_plaintext()

    # 查找 GitHub 链接
    matches = GITHUB_URL_PATTERN.findall(msg_text)
    if not matches:
        return

    # 只处理第一个匹配的链接
    path = matches[0]

    # 用 / 切分路径
    parts = path.split('/')
    username = parts[0]
    repo_name = parts[1] if len(parts) > 1 else None

    # 过滤掉一些特殊路径
    if username.lower() in ("settings", "notifications", "explore", "topics", "trending", "collections", "events", "sponsors", "login", "join", "pricing", "features", "security", "enterprise", "team", "customer-stories", "readme", "about", "orgs", "marketplace"):
        return

    if repo_name:
        # 过滤仓库的特殊路径
        if repo_name.lower() in ("followers", "following", "stars", "repositories", "projects", "packages", "sponsoring"):
            return

        # 仓库链接
        repo = await github_api.get_repo(username, repo_name)
        if not repo:
            return  # 仓库不存在，静默忽略

        if plugin_config.default_output == "text":
            await github_matcher.finish(format_repo_text(repo))
        else:
            img = await render_card(REPO_CARD_TEMPLATE, **asdict(repo))
            if img:
                await github_matcher.finish(MessageSegment.image(img))
            else:
                await github_matcher.finish(format_repo_text(repo))
    else:
        # 用户链接
        user = await github_api.get_user(username)
        if not user:
            return  # 用户不存在，静默忽略

        if plugin_config.default_output == "text":
            await github_matcher.finish(format_user_text(user))
        else:
            img = await render_card(USER_CARD_TEMPLATE, **asdict(user))
            if img:
                await github_matcher.finish(MessageSegment.image(img))
            else:
                await github_matcher.finish(format_user_text(user))


@driver.on_shutdown
async def cleanup():
    """清理资源"""
    await github_api.close()
