"""
GitHub 插件配置
"""

from cathaybot.utils.plugin_config import PluginConfig
from pydantic import Field


class Config(PluginConfig):
    """GitHub 插件配置"""

    # GitHub API Token (可选，提高速率限制)
    token: str = Field(default="", description="GitHub API Token")

    # 是否启用自动识别
    auto_detect: bool = Field(default=True, description="自动识别 GitHub 链接")

    # 默认输出模式: image / text
    default_output: str = Field(default="image", description="默认输出模式")

    # 卡片缓存时间 (秒)
    cache_ttl: int = Field(default=3600, description="卡片缓存时间")
